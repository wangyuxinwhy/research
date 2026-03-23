# 零依赖头脑风暴服务器

用一个仅使用 Node.js 内置模块的零依赖 `server.js` 文件，替换头脑风暴伴侣服务器中已打包的 node_modules（express、ws、chokidar —— 714 个被跟踪的文件）。

## 动机

将 node_modules 打包到 git 仓库中会带来供应链风险：冻结的依赖不会获得安全补丁，714 个第三方代码文件在未经审计的情况下被提交，对打包代码的修改看起来像普通提交。虽然实际风险较低（仅限本地开发服务器），但消除这一风险非常简单。

## 架构

一个约 250-300 行的 `server.js` 文件，使用 `http`、`crypto`、`fs` 和 `path`。该文件承担两个角色：

- **直接运行时**（`node server.js`）：启动 HTTP/WebSocket 服务器
- **被引用时**（`require('./server.js')`）：导出 WebSocket 协议函数供单元测试使用

### WebSocket 协议

仅对文本帧实现 RFC 6455：

**握手：** 使用 SHA-1 加上 RFC 6455 魔法 GUID，从客户端的 `Sec-WebSocket-Key` 计算 `Sec-WebSocket-Accept`。返回 101 Switching Protocols。

**帧解码（客户端到服务器）：** 处理三种掩码长度编码：
- 小型：负载 < 126 字节
- 中型：126-65535 字节（16 位扩展）
- 大型：> 65535 字节（64 位扩展）

使用 4 字节掩码密钥对负载进行 XOR 解码。返回 `{ opcode, payload, bytesConsumed }` 或对不完整缓冲区返回 `null`。拒绝未掩码的帧。

**帧编码（服务器到客户端）：** 使用相同三种长度编码的未掩码帧。

**处理的操作码：** TEXT (0x01)、CLOSE (0x08)、PING (0x09)、PONG (0x0A)。无法识别的操作码会收到状态码为 1003（不支持的数据）的关闭帧。

**刻意跳过的功能：** 二进制帧、分片消息、扩展（permessage-deflate）、子协议。对于本地客户端之间的小型 JSON 文本消息，这些功能是不必要的。扩展和子协议在握手过程中协商——不主动提供它们，它们就永远不会被激活。

**缓冲区累积：** 每个连接维护一个缓冲区。收到 `data` 时，追加数据并循环调用 `decodeFrame`，直到返回 null 或缓冲区为空。

### HTTP 服务器

三个路由：

1. **`GET /`** —— 通过 mtime 从屏幕目录中提供最新的 `.html` 文件。检测完整文档与片段，将片段包装在框架模板中，注入 helper.js。返回 `text/html`。当没有 `.html` 文件时，提供一个硬编码的等待页面（"Waiting for Claude to push a screen..."）并注入 helper.js。
2. **`GET /files/*`** —— 从屏幕目录中提供静态文件，通过硬编码的扩展名映射表（html、css、js、png、jpg、gif、svg、json）确定 MIME 类型。找不到时返回 404。
3. **其他所有请求** —— 404。

WebSocket 升级通过 HTTP 服务器上的 `'upgrade'` 事件处理，与请求处理器分开。

### 配置

环境变量（均为可选）：

- `BRAINSTORM_PORT` —— 绑定端口（默认：随机高端口 49152-65535）
- `BRAINSTORM_HOST` —— 绑定接口（默认：`127.0.0.1`）
- `BRAINSTORM_URL_HOST` —— 启动 JSON 中 URL 使用的主机名（默认：当 host 为 `127.0.0.1` 时使用 `localhost`，否则与 host 相同）
- `BRAINSTORM_DIR` —— 屏幕目录路径（默认：`/tmp/brainstorm`）

### 启动顺序

1. 如果 `SCREEN_DIR` 不存在则创建（递归 `mkdirSync`）
2. 从 `__dirname` 加载框架模板和 helper.js
3. 在配置的主机/端口上启动 HTTP 服务器
4. 在 `SCREEN_DIR` 上启动 `fs.watch`
5. 成功监听后，将 `server-started` JSON 输出到标准输出：`{ type, port, host, url_host, url, screen_dir }`
6. 将相同的 JSON 写入 `SCREEN_DIR/.server-info`，以便代理在标准输出被隐藏时（后台执行）也能找到连接详情

### 应用层 WebSocket 消息

当从客户端收到 TEXT 帧时：

1. 解析为 JSON。如果解析失败，记录到标准错误并继续。
2. 以 `{ source: 'user-event', ...event }` 格式输出到标准输出。
3. 如果事件包含 `choice` 属性，将 JSON 追加到 `SCREEN_DIR/.events`（每行一个事件）。

### 文件监视

`fs.watch(SCREEN_DIR)` 替换 chokidar。在 HTML 文件事件发生时：

- 新文件（`rename` 事件且文件存在）：如果存在 `.events` 文件则删除（`unlinkSync`），将 `screen-added` 以 JSON 格式输出到标准输出
- 文件更改（`change` 事件）：将 `screen-updated` 以 JSON 格式输出到标准输出（不清除 `.events`）
- 两种事件都会：向所有已连接的 WebSocket 客户端发送 `{ type: 'reload' }`

使用每个文件名约 100ms 超时进行防抖，以防止重复事件（在 macOS 和 Linux 上常见）。

### 错误处理

- 来自 WebSocket 客户端的格式错误的 JSON：记录到标准错误，继续
- 无法处理的操作码：以状态码 1003 关闭
- 客户端断开连接：从广播集合中移除
- `fs.watch` 错误：记录到标准错误，继续
- 无优雅关闭逻辑——Shell 脚本通过 SIGTERM 处理进程生命周期

## 变更内容

| 变更前 | 变更后 |
|---|---|
| `index.js` + `package.json` + `package-lock.json` + 714 个 `node_modules` 文件 | `server.js`（单个文件） |
| express、ws、chokidar 依赖 | 无 |
| 无静态文件服务 | `/files/*` 从屏幕目录提供文件 |

## 保持不变的内容

- `helper.js` —— 无变更
- `frame-template.html` —— 无变更
- `start-server.sh` —— 单行更新：`index.js` 改为 `server.js`
- `stop-server.sh` —— 无变更
- `visual-companion.md` —— 无变更
- 所有现有的服务器行为和外部接口

## 平台兼容性

- `server.js` 仅使用跨平台的 Node 内置模块
- `fs.watch` 在 macOS、Linux 和 Windows 上对单层目录都很可靠
- Shell 脚本需要 bash（Windows 上需要 Git Bash，这是 Claude Code 的必要条件）

## 测试

**单元测试**（`ws-protocol.test.js`）：通过引用 `server.js` 导出的函数，直接测试 WebSocket 帧编解码、握手计算和协议边界情况。

**集成测试**（`server.test.js`）：测试完整的服务器行为——HTTP 服务、WebSocket 通信、文件监视、头脑风暴工作流。使用 `ws` npm 包作为仅用于测试的客户端依赖（不会分发给最终用户）。

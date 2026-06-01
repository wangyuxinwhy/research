# 一起学 pi Agent — 学习笔记

> 对象：[earendil-works/pi](https://github.com/badlogic/pi-mono)（`pi-mono`，v0.78.0）
> 代码已 clone 到 `pi-agent-packages/pi-mono/`（已 gitignore，不入库）。

## 0. 仓库全貌

四个 package，层层叠加：

```
pi-ai (底层) ──┐
               ├──> pi-agent-core ──> pi-coding-agent
pi-tui ────────────────────────────────┘ (CLI 用 tui 做界面)
```

| 包名 | 作用 |
|------|------|
| `pi-ai` | 统一多家 LLM 的 API（对话/流式/模型发现/计费/OAuth） |
| `pi-agent-core` | 在 pi-ai 之上加 agent loop（工具调用循环）+ 状态管理 |
| `pi-coding-agent` | 完整编码 CLI（read/bash/edit/write 工具 + 会话持久化） |
| `pi-tui` | 终端 UI 库（差分渲染、编辑器、补全、Markdown） |

---

## 1. pi-ai 架构地图

### 1.1 一句话定位
把「Anthropic / OpenAI / Google / Mistral / Bedrock / 以及几十家 OpenAI 兼容厂商」抹平成
**一个统一的 `stream()` 调用 + 一套统一的消息/事件类型**。上层（agent）不需要知道在跟谁说话。

### 1.2 核心数据流

```
                  你的调用
                     │
   stream(model, context, options)        ← src/stream.ts（统一入口）
                     │
   resolveApiProvider(model.api)          ← 按 model.api 去 registry 查
                     │
   apiProviderRegistry.get(api)           ← src/api-registry.ts（注册表 Map）
                     │                       provider 在 import 时自注册
                     ▼                       (src/providers/register-builtins.ts)
   provider.stream(model, context, opts)  ← 具体厂商实现
   e.g. src/providers/anthropic.ts
                     │
   把厂商 SSE/WebSocket 原始 chunk
   翻译成统一的 AssistantMessageEvent
                     │
                     ▼
   AssistantMessageEventStream            ← src/utils/event-stream.ts
   (一个 async-iterable + .result() Promise)
```

### 1.3 三组关键抽象

**A. 数据模型（src/types.ts）— 整个包的"宪法"**
- `Model<TApi>`：模型描述（id/provider/api/baseUrl/cost/contextWindow/thinking 能力…）。`TApi` 泛型决定 `compat` 字段形状。
- `Context`：`{ systemPrompt?, messages, tools? }` —— 一次请求的全部输入。
- `Message` = `UserMessage | AssistantMessage | ToolResultMessage`。
- 内容块：`TextContent | ThinkingContent | ImageContent | ToolCall`（统一了"思考/文本/图片/工具调用"）。
- `Usage`：token 数 + 按 `model.cost` 算出的美元成本。

**B. 流协议（src/types.ts 的 `AssistantMessageEvent`）**
事件序列固定：
```
start → (text_start/delta/end | thinking_* | toolcall_*)* → done | error
```
每个事件都带一个 `partial: AssistantMessage`（增量累积的当前快照），
所以消费方既能做"打字机"流式渲染，也能在 `done` 时拿到完整结果。

**C. 注册表（src/api-registry.ts + models.ts）— 两张表**
- `apiProviderRegistry`：`api 字符串 → { stream, streamSimple }`。`registerApiProvider()` 写入，`stream()` 读取。带 `sourceId` 支持插件按来源批量注销（可扩展性的关键）。
- `modelRegistry`：`provider → modelId → Model`。数据来自生成文件 `models.generated.ts`。`getModel(provider, id)` 取用。

### 1.4 两层 API（simple vs 原始）
- `stream()` / `complete()`：传 provider 专属 options（`ProviderStreamOptions`）。
- `streamSimple()` / `completeSimple()`：传统一的 `reasoning: "low|medium|high"` 等（`SimpleStreamOptions`），由各 provider 自己翻译成专属参数。**上层 agent 用的是 simple 这层。**
- `complete*` 只是 `stream*().result()` 的 await 封装。

### 1.5 EventStream 的实现要点（src/utils/event-stream.ts）
- 自己手写的 async-iterable：内部一个 `queue` + 一个 `waiting` 回调列表，实现"生产者 push / 消费者 await"的背压握手。
- 构造时传入 `isComplete`（哪种事件算结束）和 `extractResult`（从结束事件里取最终值）。
- `AssistantMessageEventStream` 特化：`done`/`error` 为终止事件，`.result()` 返回最终 `AssistantMessage`。

### 1.6 文件地图（按重要性）
| 文件 | 看点 |
|------|------|
| `src/types.ts` (593行) | 全部数据/事件类型，**先读这个** |
| `src/stream.ts` (75行) | 统一入口，最短，串起全局 |
| `src/api-registry.ts` (98行) | provider 注册/查找机制 |
| `src/models.ts` (92行) | 模型表 + 计费 + thinking 等级钳制 |
| `src/utils/event-stream.ts` (88行) | 流的底层数据结构 |
| `src/providers/*.ts` | 各厂商翻译层（anthropic 1230行 / openai-completions 1161行最厚） |
| `src/providers/register-builtins.ts` | 懒加载注册内置 provider |
| `src/env-api-keys.ts` | 从环境变量找 API key |
| `src/utils/oauth/*` | Anthropic/OpenAI/Copilot 的 OAuth 登录 |

---

## 2. OpenAI provider 的消息转换（convertMessages）

把 pi 统一的 `Message[]` 翻译成 OpenAI Chat Completions 的 `ChatCompletionMessageParam[]`。
在 `openai-completions.ts:503` 构建请求体时调用。**两步流水线**：

### 2.1 transformMessages（transform-messages.ts，provider 无关的归一化）
1. **图片降级** `downgradeUnsupportedImages` (L35)：非视觉模型把 image 换占位文字。
2. **thinking 处理** (L97)：按 `isSameModel`（provider+api+model 全等）决定保留/降级；
   `redacted` 加密思考跨模型直接丢，普通 thinking 跨模型降级为 text。
3. **toolCall ID 归一化** (L124)：长/含 `|` 的 ID 转合法格式，用 `toolCallIdMap` 同步
   修正对应的 `toolResult.toolCallId`。
4. **第二趟补孤儿 toolCall** (L155)：无配对 result 的 toolCall 合成 `"No result provided"`
   error 结果（OpenAI 强制 tool_call 必须配对）；`stopReason=error/aborted` 的 assistant 整段跳过。

### 2.2 convertMessages（openai-completions.ts:741，OpenAI 专属格式化）
- systemPrompt → `developer`(推理模型) 或 `system` 角色 (L765)
- user：文本直传 / 图片转 `image_url` data URI (L784)
- assistant (L812)：thinking→`reasoning_content` 等签名字段或纯文本；
  **文本坚持用 string 不用数组**（避免 DeepSeek V3.2 照抄结构的递归 bug, L842）；
  toolCall→`tool_calls`（arguments 要 JSON.stringify）；空消息跳过
- toolResult (L913)：`while` 合并连续 result→`role:"tool"`；图片因 tool 消息不能带图，
  单独拎成一条 user 消息 (L956)
- synthetic bridge (L777)：`requiresAssistantAfterToolResult` 厂商在 toolResult 后插假 assistant

### 2.3 为什么这么绕
满屏的 `compat.*` 分支 = 适配几十家 OpenAI 兼容厂商（DeepSeek/Groq/OpenRouter/z.ai…）的怪癖。
> transformMessages 保证"对话语义合法且跨模型安全"，convertMessages 保证"翻译成线格式并绕开各家坑"。

---

## 3. pi-agent-core 架构

pi-ai 让你「说一句话给模型」；agent-core 让模型「自己转起来」：调工具→看结果→再调，
直到完成。即「循环引擎 + 状态机」。

### 3.1 三层抽象（从裸到开箱即用）
```
① agent-loop.ts   纯函数循环，无状态     ← 引擎本体
② agent.ts        Agent 类，有状态        ← 加队列/订阅/abort
③ harness/        AgentHarness，开箱即用   ← 接会话持久化/压缩/skills
```

### 3.2 agent-loop.ts —— 引擎
- `agentLoop()` 返回 `EventStream<AgentEvent>`（复用 pi-ai 的 EventStream），内部跑 `runLoop`。
- `runLoop` 双层 while (L170-266)：
  - 外层处理 follow-up；内层每轮 = 注入 steering → streamAssistantResponse → executeToolCalls
    → turn_end → prepareNextTurn → shouldStopAfterTurn → 再捞 steering。
- **接缝 `streamAssistantResponse` (L275)**：
  `AgentMessage[]` →transformContext→ →convertToLlm→ `Message[]` → **streamSimple()(pi-ai)**
  → 消费事件翻译成 AgentEvent；边流边把 partial 写回 context.messages[last] (L333) 供 UI 实时渲染。
- 工具执行 sequential / parallel，带 beforeToolCall / afterToolCall hook；
  整批都 terminate 才提前停 (shouldTerminateToolBatch)。

### 3.3 agent.ts —— 有状态 Agent 类 (L166)
prompt()/continue() 发起；steer() 运行中插话；followUp() 干完再追加；abort()；subscribe() 订阅事件。
MessageQueue (L122) 支持 "all" / "one-at-a-time"。这些队列就是 types.ts 里 getSteeringMessages/
getFollowUpMessages 等 hook 的实现来源。

### 3.4 harness/ —— 补齐记忆与上下文管理
- session/：JSONL / 内存会话持久化
- compaction/：token 超阈值就总结历史（compaction.ts 756 行）
- skills.ts / prompt-templates.ts / system-prompt.ts / env/nodejs.ts

### 3.5 本层宪法类型（types.ts）
- `AgentMessage` = pi-ai Message + 自定义消息（declaration merging 扩展）
- `AgentTool` = pi-ai Tool + execute()/label/executionMode
- `AgentEvent` 四级：agent_* → turn_* → message_* → tool_execution_*
- `AgentLoopConfig` = 全部 hook + convertToLlm(必填)

---

## 4. agent/harness 设计思路（AgentHarness）

定位：agentLoop(引擎) 和 Agent 类(状态) 是机制；**AgentHarness 是组装好、电池全包的门面(Facade)**，
真正给 app 用。设计主题词 = **可替换**。

### 设计1：副作用全抽象成可注入接口（依赖倒置）
构造时注入（AgentHarnessOptions L798）：
- `ExecutionEnv = FileSystem + Shell`：工具不直接 import fs，可换沙箱/远程/内存（安全+可测）。env/nodejs.ts 只是一个实现。
- `Session`/`SessionStorage`/`SessionRepo`：JSONL 或内存可换。
- `Skill`/`PromptTemplate`/`Resources`：素材由 app 加载，harness 只消费。

### 设计2：错误是数据不是异常
FileSystem 注释 "must never throw or reject"，全返回 `Result<T,E>`(L6)。
原因：loop 不能因一次文件失败崩掉，失败要变 toolResult 喂回模型。
分层：FileError/ExecutionError/CompactionError/SessionError/BranchSummaryError
→ normalizeHarnessError(L145) → 统一 AgentHarnessError(带 code)。

### 设计3：会话是树不是日志
SessionTreeEntry(L334) 每条带 parentId → 树。且所有状态变化都是节点：
message / model_change / thinking_level_change / active_tools_change / compaction / branch_summary / label。
撑起三能力：分支重走(navigateTree)、上下文压缩(compaction 折叠成 summary 节点但原历史不丢)、完整可重放。

### 设计4：hook = 中间件，开闭原则
AgentHarnessEventResultMap(L704) 两类：
- 纯观察(返回 undefined)：queue_update/save_point/settled…
- 可干预(返回值被采纳)：tool_call(拦截工具)/tool_result(改写结果)/context(改上下文)/before_provider_payload(改请求体)。
app 注册 hook 即可注入行为，无需 fork harness。

### 设计5：turn 开始时快照
AgentHarnessTurnState(L158) + streamOptions "Snapshotted at turn start"(L824)。
运行中 setModel() 当前轮仍用旧快照，下一轮才生效，避免一轮内状态不一致。
配 phase 状态机：idle|turn|compaction|branch_summary|retry。

---

## 5. ExecutionEnv：从第一性原理推导

### 5.1 出发点
LLM 只会出 token，要成 agent 必须能感知+改变环境。最小能力集：跑命令(shell) + 读写文件(fs)。
naive v0：`exec(cmd):Promise<string>` / `readFile` / `writeFile` / `listDir`，全会 throw。

### 5.2 把 v0 放进 agent loop，逐条追问逼出修正
| 追问 | 修正 → pi 对应 |
|------|----------------|
| 命令挂/文件不存在就崩？ | 不抛异常，返回 `Result<T,E>`；注释 "must never throw or reject" |
| 用户要中断？ | 每个方法接 `AbortSignal` |
| 命令挂死？ | `exec` 加 `timeout` |
| 长命令要实时输出？ | `onStdout/onStderr` 流式回调 |
| 相对路径相对谁？ | `FileSystem.cwd` |
| 读 2GB 文件爆内存？ | 拆 `readTextFile/readTextLines(maxLines)/readBinaryFile` |
| 该不该读这文件？ | `fileInfo → {name,path,kind,size,mtimeMs}` |
| symlink 逃逸沙箱？ | 默认不跟随 symlink，显式 `canonicalPath()` |
| 草稿空间/连接释放？ | `createTempDir/File` + `cleanup()` |
| 区分 没文件/没权限/超时？ | 错误带 code：FileErrorCode/ExecutionErrorCode |

### 5.3 我们没想到但精彩的两点
- 拆 `FileSystem` + `Shell` 两接口再 `ExecutionEnv extends both`：接口隔离，只读工具可只依赖 FileSystem。
- "addressed path(纯语法规范化, 不穿透 symlink)" vs "canonicalPath(解析 symlink, 有副作用)" 措辞严格分离。

### 5.4 第一性原理三主轴（全被 agent 场景逼出来）
1. 错误是数据 (Result + never throw) ← loop 不能崩
2. 一切可中断/可超时 (signal + timeout) ← LLM 不可信、用户要控制
3. 副作用可替换 (纯接口) ← 要能沙箱化/可测试

## 待办 / 疑问
- [ ] 下一步：进 env/nodejs.ts 看接口怎么落地（spawn 包装/abort/相对路径/symlink/Windows taskkill）
- [ ] agent-core 其他：executeToolCalls 并行/串行？compaction？Session 树/分支？hook 串联？

# 为 OpenCode 安装 Superpowers

## 前置要求

- 已安装 [OpenCode.ai](https://opencode.ai)

## 安装

在你的 `opencode.json`（全局或项目级别）的 `plugin` 数组中添加 superpowers：

```json
{
  "plugin": ["superpowers@git+https://github.com/obra/superpowers.git"]
}
```

重启 OpenCode。搞定 —— 插件会自动安装并注册所有技能。

通过以下方式验证：询问 "Tell me about your superpowers"

## 从旧版符号链接安装方式迁移

如果你之前通过 `git clone` 和符号链接安装了 superpowers，请移除旧的设置：

```bash
# 移除旧的符号链接
rm -f ~/.config/opencode/plugins/superpowers.js
rm -rf ~/.config/opencode/skills/superpowers

# 可选：移除克隆的仓库
rm -rf ~/.config/opencode/superpowers

# 如果你在 opencode.json 中为 superpowers 添加过 skills.paths，也请移除
```

然后按照上面的安装步骤操作。

## 使用

使用 OpenCode 的原生 `skill` 工具：

```
use skill tool to list skills
use skill tool to load superpowers/brainstorming
```

## 更新

重启 OpenCode 时，Superpowers 会自动更新。

要锁定特定版本：

```json
{
  "plugin": ["superpowers@git+https://github.com/obra/superpowers.git#v5.0.3"]
}
```

## 故障排除

### 插件未加载

1. 检查日志：`opencode run --print-logs "hello" 2>&1 | grep -i superpowers`
2. 验证 `opencode.json` 中的插件配置行
3. 确保你运行的是最新版本的 OpenCode

### 找不到技能

1. 使用 `skill` 工具列出已发现的技能
2. 检查插件是否正常加载（见上文）

### 工具映射

当技能引用 Claude Code 工具时：
- `TodoWrite` → `todowrite`
- `Task`（子代理）→ `@mention` 语法
- `Skill` 工具 → OpenCode 的原生 `skill` 工具
- 文件操作 → 你的原生工具

## 获取帮助

- 报告问题：https://github.com/obra/superpowers/issues
- 完整文档：https://github.com/obra/superpowers/blob/main/docs/README.opencode.md

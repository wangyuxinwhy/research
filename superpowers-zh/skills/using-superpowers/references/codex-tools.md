# Codex 工具映射

技能（Skills）使用 Claude Code 的工具名称。当你在技能中遇到这些名称时，请使用你所在平台的等效工具：

| 技能中引用的名称 | Codex 等效工具 |
|-----------------|------------------|
| `Task` 工具（派遣子代理） | `spawn_agent` |
| 多个 `Task` 调用（并行） | 多个 `spawn_agent` 调用 |
| Task 返回结果 | `wait` |
| Task 自动完成 | `close_agent` 释放槽位 |
| `TodoWrite`（任务跟踪） | `update_plan` |
| `Skill` 工具（调用技能） | 技能原生加载——直接按照说明操作即可 |
| `Read`、`Write`、`Edit`（文件操作） | 使用你的原生文件工具 |
| `Bash`（运行命令） | 使用你的原生 Shell 工具 |

## 子代理（subagent）派遣需要多代理支持

在你的 Codex 配置文件（`~/.codex/config.toml`）中添加：

```toml
[features]
multi_agent = true
```

这将启用 `spawn_agent`、`wait` 和 `close_agent`，用于支持 `dispatching-parallel-agents` 和 `subagent-driven-development` 等技能。

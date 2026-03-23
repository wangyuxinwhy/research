# Gemini CLI 工具映射

技能（Skills）使用 Claude Code 的工具名称。当你在技能中遇到这些名称时，请使用你所在平台的等效工具：

| 技能中引用的名称 | Gemini CLI 等效工具 |
|-----------------|----------------------|
| `Read`（读取文件） | `read_file` |
| `Write`（创建文件） | `write_file` |
| `Edit`（编辑文件） | `replace` |
| `Bash`（运行命令） | `run_shell_command` |
| `Grep`（搜索文件内容） | `grep_search` |
| `Glob`（按名称搜索文件） | `glob` |
| `TodoWrite`（任务跟踪） | `write_todos` |
| `Skill` 工具（调用技能） | `activate_skill` |
| `WebSearch` | `google_web_search` |
| `WebFetch` | `web_fetch` |
| `Task` 工具（派遣子代理） | 无等效工具——Gemini CLI 不支持子代理（subagent） |

## 不支持子代理

Gemini CLI 没有与 Claude Code 的 `Task` 工具对应的等效功能。依赖子代理派遣的技能（`subagent-driven-development`、`dispatching-parallel-agents`）将回退到通过 `executing-plans` 进行单会话执行。

## Gemini CLI 的额外工具

以下工具在 Gemini CLI 中可用，但在 Claude Code 中没有对应的等效工具：

| 工具 | 用途 |
|------|---------|
| `list_directory` | 列出文件和子目录 |
| `save_memory` | 将信息持久化保存到 GEMINI.md，跨会话使用 |
| `ask_user` | 向用户请求结构化输入 |
| `tracker_create_task` | 丰富的任务管理功能（创建、更新、列出、可视化） |
| `enter_plan_mode` / `exit_plan_mode` | 在进行修改前切换到只读研究模式 |

# Superpowers

Superpowers 是一套为你的编程代理（coding agent）打造的完整软件开发工作流，构建在一组可组合的"技能（skills）"之上，并通过初始指令确保你的代理能够正确使用它们。

## 工作原理

一切从你启动编程代理的那一刻开始。当它发现你正在构建某个东西时，它*不会*急于编写代码。相反，它会退一步，询问你真正想要做什么。

在通过对话梳理出需求规格之后，它会把规格分成短小的段落展示给你，确保你能真正阅读和理解每一部分。

在你确认设计方案之后，你的代理会制定一份实施计划，这份计划清晰到即使是一个充满热情但品味欠佳、缺乏判断力、没有项目背景、还不爱写测试的初级工程师也能照着执行。它强调真正的红/绿测试驱动开发（TDD）、YAGNI（你不会需要它）和 DRY（不要重复自己）原则。

接下来，当你说"开始"之后，它会启动一个*子代理驱动开发（subagent-driven-development）*流程，让代理逐个执行每项工程任务，检查和审查它们的工作，然后继续推进。Claude 连续自主工作几个小时而不偏离你制定的计划，这并不罕见。

当然还有更多细节，但以上就是这个系统的核心。由于技能会自动触发，你无需做任何特别的事情。你的编程代理自带 Superpowers。


## 赞助

如果 Superpowers 帮助你赚了钱，而你也有意愿的话，我非常感谢你考虑[赞助我的开源工作](https://github.com/sponsors/obra)。

谢谢！

- Jesse


## 安装

**注意：** 安装方式因平台而异。Claude Code 或 Cursor 有内置的插件市场。Codex 和 OpenCode 需要手动设置。

### Claude Code 官方市场

Superpowers 可通过 [Claude 官方插件市场](https://claude.com/plugins/superpowers) 获取。

从 Claude 市场安装插件：

```bash
/plugin install superpowers@claude-plugins-official
```

### Claude Code（通过插件市场）

在 Claude Code 中，先注册市场：

```bash
/plugin marketplace add obra/superpowers-marketplace
```

然后从该市场安装插件：

```bash
/plugin install superpowers@superpowers-marketplace
```

### Cursor（通过插件市场）

在 Cursor Agent 聊天中，从市场安装：

```text
/add-plugin superpowers
```

或在插件市场中搜索 "superpowers"。

### Codex

告诉 Codex：

```
Fetch and follow instructions from https://raw.githubusercontent.com/obra/superpowers/refs/heads/main/.codex/INSTALL.md
```

**详细文档：** [docs/README.codex.md](docs/README.codex.md)

### OpenCode

告诉 OpenCode：

```
Fetch and follow instructions from https://raw.githubusercontent.com/obra/superpowers/refs/heads/main/.opencode/INSTALL.md
```

**详细文档：** [docs/README.opencode.md](docs/README.opencode.md)

### Gemini CLI

```bash
gemini extensions install https://github.com/obra/superpowers
```

更新：

```bash
gemini extensions update superpowers
```

### 验证安装

在你选择的平台上启动新会话，并请求一些应该触发技能的操作（例如，"帮我规划这个功能"或"我们来调试这个问题"）。代理应该会自动调用相关的 superpowers 技能。

## 基本工作流

1. **brainstorming（头脑风暴）** - 在编写代码之前激活。通过提问细化粗略想法，探索替代方案，分段展示设计供验证。保存设计文档。

2. **using-git-worktrees（使用 Git 工作树）** - 在设计获批后激活。在新分支上创建隔离的工作空间，运行项目设置，验证测试基线是否干净。

3. **writing-plans（编写计划）** - 在设计获批后激活。将工作拆分为小任务（每个 2-5 分钟）。每个任务都有精确的文件路径、完整的代码和验证步骤。

4. **subagent-driven-development（子代理驱动开发）** 或 **executing-plans（执行计划）** - 有计划后激活。为每个任务分配全新的子代理，进行两阶段审查（先检查规格合规性，再检查代码质量），或者分批执行并设置人工检查点。

5. **test-driven-development（测试驱动开发）** - 在实现阶段激活。强制执行红-绿-重构循环：先写失败的测试，观察它失败，编写最少的代码，观察测试通过，然后提交。删除在测试之前编写的代码。

6. **requesting-code-review（请求代码审查）** - 在任务之间激活。对照计划进行审查，按严重程度报告问题。关键问题会阻止继续推进。

7. **finishing-a-development-branch（完成开发分支）** - 在所有任务完成后激活。验证测试，提供选项（合并/PR/保留/丢弃），清理工作树。

**代理在执行任何任务之前都会检查是否有相关技能。** 这是强制性的工作流，而非建议。

## 内容概览

### 技能库

**测试**
- **test-driven-development** - 红-绿-重构循环（包含测试反模式参考）

**调试**
- **systematic-debugging** - 四阶段根因分析流程（包含根因追踪、纵深防御、基于条件的等待等技术）
- **verification-before-completion** - 确保问题确实已修复

**协作**
- **brainstorming** - 苏格拉底式设计细化
- **writing-plans** - 详细的实施计划
- **executing-plans** - 带检查点的分批执行
- **dispatching-parallel-agents** - 并发子代理工作流
- **requesting-code-review** - 审查前检查清单
- **receiving-code-review** - 回应审查反馈
- **using-git-worktrees** - 并行开发分支
- **finishing-a-development-branch** - 合并/PR 决策工作流
- **subagent-driven-development** - 快速迭代，两阶段审查（先规格合规性，再代码质量）

**元技能**
- **writing-skills** - 按照最佳实践创建新技能（包含测试方法论）
- **using-superpowers** - 技能系统简介

## 理念

- **测试驱动开发** - 始终先写测试
- **系统化而非临时化** - 流程优于猜测
- **降低复杂度** - 简洁是首要目标
- **证据优于声明** - 先验证再宣告成功

阅读更多：[Superpowers for Claude Code](https://blog.fsck.com/2025/10/09/superpowers/)

## 贡献

技能直接存放在本仓库中。参与贡献：

1. Fork 本仓库
2. 为你的技能创建一个分支
3. 遵循 `writing-skills` 技能来创建和测试新技能
4. 提交 PR

详见 `skills/writing-skills/SKILL.md` 获取完整指南。

## 更新

通过更新插件即可自动更新技能：

```bash
/plugin update superpowers
```

## 许可证

MIT 许可证 - 详见 LICENSE 文件

## 社区

Superpowers 由 [Jesse Vincent](https://blog.fsck.com) 和 [Prime Radiant](https://primeradiant.com) 的其他成员共同构建。

如需社区支持、提问或分享你用 Superpowers 构建的项目，请加入我们的 [Discord](https://discord.gg/Jd8Vphy9jq)。

## 支持

- **Discord**：[加入我们的 Discord](https://discord.gg/Jd8Vphy9jq)
- **问题反馈**：https://github.com/obra/superpowers/issues
- **插件市场**：https://github.com/obra/superpowers-marketplace

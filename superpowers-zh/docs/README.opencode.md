# Superpowers for OpenCode

使用 Superpowers 与 [OpenCode.ai](https://opencode.ai) 配合的完整指南。

## 安装

在你的 `opencode.json`（全局或项目级别）的 `plugin` 数组中添加 superpowers：

```json
{
  "plugin": ["superpowers@git+https://github.com/obra/superpowers.git"]
}
```

重启 OpenCode。插件会通过 Bun 自动安装并自动注册所有技能。

通过以下方式验证：询问 "Tell me about your superpowers"

### 从旧版符号链接安装方式迁移

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

### 查找技能

使用 OpenCode 的原生 `skill` 工具列出所有可用技能：

```
use skill tool to list skills
```

### 加载技能

```
use skill tool to load superpowers/brainstorming
```

### 个人技能

在 `~/.config/opencode/skills/` 中创建你自己的技能：

```bash
mkdir -p ~/.config/opencode/skills/my-skill
```

创建 `~/.config/opencode/skills/my-skill/SKILL.md`：

```markdown
---
name: my-skill
description: Use when [condition] - [what it does]
---

# My Skill

[你的技能内容写在这里]
```

### 项目技能

在项目的 `.opencode/skills/` 目录中创建项目特定的技能。

**技能优先级：** 项目技能 > 个人技能 > Superpowers 技能

## 更新

重启 OpenCode 时，Superpowers 会自动更新。插件在每次启动时都会从 git 仓库重新安装。

要锁定特定版本，使用分支或标签：

```json
{
  "plugin": ["superpowers@git+https://github.com/obra/superpowers.git#v5.0.3"]
}
```

## 工作原理

该插件做两件事：

1. **注入引导上下文** —— 通过 `experimental.chat.system.transform` 钩子，为每次对话添加 superpowers 感知能力。
2. **注册技能目录** —— 通过 `config` 钩子，让 OpenCode 无需符号链接或手动配置即可发现所有 superpowers 技能。

### 工具映射

为 Claude Code 编写的技能会自动适配 OpenCode：

- `TodoWrite` → `todowrite`
- `Task`（子代理）→ OpenCode 的 `@mention` 系统
- `Skill` 工具 → OpenCode 的原生 `skill` 工具
- 文件操作 → OpenCode 原生工具

## 故障排除

### 插件未加载

1. 检查 OpenCode 日志：`opencode run --print-logs "hello" 2>&1 | grep -i superpowers`
2. 验证 `opencode.json` 中的插件配置行是否正确
3. 确保你运行的是最新版本的 OpenCode

### 找不到技能

1. 使用 OpenCode 的 `skill` 工具列出可用技能
2. 检查插件是否正常加载（见上文）
3. 每个技能都需要一个包含有效 YAML frontmatter 的 `SKILL.md` 文件

### 引导信息未出现

1. 检查 OpenCode 版本是否支持 `experimental.chat.system.transform` 钩子
2. 修改配置后重启 OpenCode

## 获取帮助

- 报告问题：https://github.com/obra/superpowers/issues
- 主要文档：https://github.com/obra/superpowers
- OpenCode 文档：https://opencode.ai/docs/

---
name: requesting-code-review
description: 在完成任务、实现主要功能或合并前使用，以验证工作是否满足要求
---

# 请求代码审查

派遣 superpowers:code-reviewer 子代理（subagent）在问题扩散之前发现它们。审查者会获得精心构造的评估上下文——而不是你的会话历史。这使审查者专注于工作成果而非你的思考过程，同时也为你的后续工作保留了上下文。

**核心原则：** 早审查，勤审查。

## 何时请求审查

**必须：**
- 在子代理驱动开发中每个任务完成后
- 完成主要功能后
- 合并到 main 分支之前

**可选但有价值：**
- 遇到困难时（换个视角）
- 重构之前（基线检查）
- 修复复杂 bug 之后

## 如何请求

**1. 获取 git SHA：**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. 派遣 code-reviewer 子代理：**

使用 Task 工具，类型为 superpowers:code-reviewer，填写 `code-reviewer.md` 中的模板

**占位符：**
- `{WHAT_WAS_IMPLEMENTED}` - 你刚刚构建的内容
- `{PLAN_OR_REQUIREMENTS}` - 它应该做什么
- `{BASE_SHA}` - 起始提交
- `{HEAD_SHA}` - 结束提交
- `{DESCRIPTION}` - 简要摘要

**3. 根据反馈采取行动：**
- 立即修复严重（Critical）问题
- 在继续之前修复重要（Important）问题
- 记录次要（Minor）问题，稍后处理
- 如果审查者判断有误，提出反驳（附上理由）

## 示例

```
[刚完成任务 2：添加验证函数]

你：让我在继续之前请求代码审查。

BASE_SHA=$(git log --oneline | grep "Task 1" | head -1 | awk '{print $1}')
HEAD_SHA=$(git rev-parse HEAD)

[派遣 superpowers:code-reviewer 子代理]
  WHAT_WAS_IMPLEMENTED: 会话索引的验证和修复函数
  PLAN_OR_REQUIREMENTS: docs/superpowers/plans/deployment-plan.md 中的任务 2
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661
  DESCRIPTION: 添加了 verifyIndex() 和 repairIndex()，包含 4 种问题类型

[子代理返回]:
  优点：架构清晰，测试真实
  问题：
    重要：缺少进度指示器
    次要：魔术数字（100）用于报告间隔
  评估：可以继续

你：[修复进度指示器]
[继续任务 3]
```

## 与工作流的集成

**子代理驱动开发：**
- 每个任务后都进行审查
- 在问题叠加之前发现它们
- 在进入下一个任务之前修复

**执行计划：**
- 每批（3 个任务）后审查
- 获取反馈、应用修复、继续

**临时开发：**
- 合并前审查
- 遇到困难时审查

## 危险信号

**绝不要：**
- 因为"很简单"就跳过审查
- 忽视严重问题
- 在未修复的重要问题存在时继续
- 与合理的技术反馈争辩

**如果审查者判断有误：**
- 用技术理由进行反驳
- 展示证明其可用的代码/测试
- 请求澄清

参见模板：requesting-code-review/code-reviewer.md

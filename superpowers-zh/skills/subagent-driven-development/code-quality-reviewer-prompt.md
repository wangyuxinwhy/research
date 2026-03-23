# 代码质量审查者提示模板

派遣代码质量审查者子代理（subagent）时使用此模板。

**目的：** 验证实现质量良好（整洁、经过测试、易于维护）

**仅在规格合规性审查通过后才派遣。**

```
Task tool (superpowers:code-reviewer):
  Use template at requesting-code-review/code-reviewer.md

  WHAT_WAS_IMPLEMENTED: [来自实现者的报告]
  PLAN_OR_REQUIREMENTS: Task N from [plan-file]
  BASE_SHA: [任务前的提交]
  HEAD_SHA: [当前提交]
  DESCRIPTION: [任务摘要]
```

**除了标准的代码质量关注点外，审查者还应检查：**
- 每个文件是否有一个明确的职责和定义良好的接口？
- 各单元的分解是否使其可以被独立理解和测试？
- 实现是否遵循了计划中的文件结构？
- 此次实现是否创建了已经很大的新文件，或显著增大了现有文件？（不要标记已存在的文件大小问题——重点关注此次变更贡献的内容。）

**代码审查者返回：** 优点、问题（严重/重要/次要）、评估

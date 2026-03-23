# 根因追踪

## 概述

Bug 往往在调用栈的深处暴露出来（在错误的目录中执行 git init、文件创建在错误的位置、数据库使用了错误的路径打开）。你的直觉是在错误出现的地方修复它，但那只是在治标。

**核心原则：** 沿着调用链向上回溯，直到找到最初的触发点，然后在源头修复。

## 适用场景

```dot
digraph when_to_use {
    "Bug出现在调用栈深处?" [shape=diamond];
    "能否向上回溯?" [shape=diamond];
    "在症状出现处修复" [shape=box];
    "追溯到最初触发点" [shape=box];
    "更佳做法：同时添加纵深防御" [shape=box];

    "Bug出现在调用栈深处?" -> "能否向上回溯?" [label="是"];
    "能否向上回溯?" -> "追溯到最初触发点" [label="是"];
    "能否向上回溯?" -> "在症状出现处修复" [label="否 - 线索中断"];
    "追溯到最初触发点" -> "更佳做法：同时添加纵深防御";
}
```

**适用情况：**
- 错误发生在执行的深层（而非入口点）
- 堆栈跟踪显示较长的调用链
- 不清楚无效数据的来源
- 需要找出是哪个测试/代码触发了问题

## 追踪过程

### 1. 观察症状
```
Error: git init failed in /Users/jesse/project/packages/core
```

### 2. 找到直接原因
**哪段代码直接导致了这个问题？**
```typescript
await execFileAsync('git', ['init'], { cwd: projectDir });
```

### 3. 追问：谁调用了它？
```typescript
WorktreeManager.createSessionWorktree(projectDir, sessionId)
  → called by Session.initializeWorkspace()
  → called by Session.create()
  → called by test at Project.create()
```

### 4. 继续向上追踪
**传入了什么值？**
- `projectDir = ''`（空字符串！）
- 空字符串作为 `cwd` 会解析为 `process.cwd()`
- 那就是源代码目录！

### 5. 找到最初触发点
**空字符串从哪里来的？**
```typescript
const context = setupCoreTest(); // Returns { tempDir: '' }
Project.create('name', context.tempDir); // Accessed before beforeEach!
```

## 添加堆栈跟踪

当无法手动追踪时，添加埋点：

```typescript
// Before the problematic operation
async function gitInit(directory: string) {
  const stack = new Error().stack;
  console.error('DEBUG git init:', {
    directory,
    cwd: process.cwd(),
    nodeEnv: process.env.NODE_ENV,
    stack,
  });

  await execFileAsync('git', ['init'], { cwd: directory });
}
```

**关键：** 在测试中使用 `console.error()`（不要用 logger —— 可能不会显示）

**运行并捕获：**
```bash
npm test 2>&1 | grep 'DEBUG git init'
```

**分析堆栈跟踪：**
- 查找测试文件名
- 找到触发调用的行号
- 识别规律（同一个测试？同一个参数？）

## 找出哪个测试造成了污染

如果在测试过程中出现了某些东西，但你不知道是哪个测试造成的：

使用本目录中的二分查找脚本 `find-polluter.sh`：

```bash
./find-polluter.sh '.git' 'src/**/*.test.ts'
```

逐个运行测试，在找到第一个污染者时停止。详见脚本使用说明。

## 真实案例：空的 projectDir

**症状：** `.git` 被创建在 `packages/core/`（源代码目录）中

**追踪链：**
1. `git init` 在 `process.cwd()` 中运行 ← 空的 cwd 参数
2. WorktreeManager 被传入空的 projectDir
3. Session.create() 传入了空字符串
4. 测试在 beforeEach 之前访问了 `context.tempDir`
5. setupCoreTest() 初始时返回 `{ tempDir: '' }`

**根因：** 顶层变量初始化时访问了空值

**修复：** 将 tempDir 改为 getter，在 beforeEach 之前访问时抛出异常

**同时添加了纵深防御：**
- 第一层：Project.create() 验证目录
- 第二层：WorkspaceManager 验证非空
- 第三层：NODE_ENV 守卫拒绝在 tmpdir 之外执行 git init
- 第四层：在 git init 之前记录堆栈跟踪

## 核心原则

```dot
digraph principle {
    "找到了直接原因" [shape=ellipse];
    "能否向上追溯一层?" [shape=diamond];
    "向上回溯" [shape=box];
    "这是源头吗?" [shape=diamond];
    "在源头修复" [shape=box];
    "在每一层添加验证" [shape=box];
    "Bug不可能再出现" [shape=doublecircle];
    "绝不只修复症状" [shape=octagon, style=filled, fillcolor=red, fontcolor=white];

    "找到了直接原因" -> "能否向上追溯一层?";
    "能否向上追溯一层?" -> "向上回溯" [label="是"];
    "能否向上追溯一层?" -> "绝不只修复症状" [label="否"];
    "向上回溯" -> "这是源头吗?";
    "这是源头吗?" -> "向上回溯" [label="否 - 继续向上"];
    "这是源头吗?" -> "在源头修复" [label="是"];
    "在源头修复" -> "在每一层添加验证";
    "在每一层添加验证" -> "Bug不可能再出现";
}
```

**绝不要只在错误出现的地方修复。** 向上回溯找到最初的触发点。

## 堆栈跟踪技巧

**在测试中：** 使用 `console.error()` 而不是 logger —— logger 可能被抑制
**在操作之前：** 在危险操作之前记录日志，而不是在失败之后
**包含上下文：** 目录、cwd、环境变量、时间戳
**捕获堆栈：** `new Error().stack` 显示完整的调用链

## 实际影响

来自调试会话（2025-10-03）：
- 通过 5 层追踪找到了根因
- 在源头修复（getter 验证）
- 添加了 4 层防御
- 1847 个测试通过，零污染

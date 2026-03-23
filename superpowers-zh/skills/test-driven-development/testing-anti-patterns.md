# 测试反模式

**在以下情况时加载此参考：** 编写或修改测试、添加 mock、或者想要向生产代码中添加仅用于测试的方法时。

## 概述

测试必须验证真实行为，而不是 mock 行为。Mock 是用来隔离的手段，而不是被测试的对象。

**核心原则：** 测试代码做了什么，而不是测试 mock 做了什么。

**严格遵循 TDD 可以避免这些反模式。**

## 铁律

```
1. 绝不测试 mock 的行为
2. 绝不向生产类添加仅用于测试的方法
3. 绝不在不理解依赖关系的情况下使用 mock
```

## 反模式 1：测试 Mock 的行为

**违规做法：**
```typescript
// ❌ 错误：测试 mock 是否存在
test('renders sidebar', () => {
  render(<Page />);
  expect(screen.getByTestId('sidebar-mock')).toBeInTheDocument();
});
```

**为什么这是错的：**
- 你在验证 mock 是否工作，而不是组件是否工作
- mock 存在时测试通过，不存在时测试失败
- 对真实行为毫无说明

**协作伙伴的纠正：** "我们是在测试 mock 的行为吗？"

**正确做法：**
```typescript
// ✅ 正确：测试真实组件或不使用 mock
test('renders sidebar', () => {
  render(<Page />);  // Don't mock sidebar
  expect(screen.getByRole('navigation')).toBeInTheDocument();
});

// 或者如果侧边栏必须被 mock 以实现隔离：
// 不要对 mock 做断言——测试 Page 在侧边栏存在时的行为
```

### 门控函数

```
在对任何 mock 元素做断言之前：
  问自己："我是在测试真实组件行为还是仅仅在测试 mock 的存在？"

  如果是在测试 mock 的存在：
    停下来 - 删除该断言或取消 mock 该组件

  改为测试真实行为
```

## 反模式 2：生产代码中仅用于测试的方法

**违规做法：**
```typescript
// ❌ 错误：destroy() 仅在测试中使用
class Session {
  async destroy() {  // Looks like production API!
    await this._workspaceManager?.destroyWorkspace(this.id);
    // ... cleanup
  }
}

// In tests
afterEach(() => session.destroy());
```

**为什么这是错的：**
- 生产类被仅用于测试的代码污染
- 如果在生产环境中被意外调用会很危险
- 违反了 YAGNI 原则和关注点分离
- 混淆了对象生命周期和实体生命周期

**正确做法：**
```typescript
// ✅ 正确：测试工具处理测试清理
// Session 没有 destroy() —— 它在生产环境中是无状态的

// In test-utils/
export async function cleanupSession(session: Session) {
  const workspace = session.getWorkspaceInfo();
  if (workspace) {
    await workspaceManager.destroyWorkspace(workspace.id);
  }
}

// In tests
afterEach(() => cleanupSession(session));
```

### 门控函数

```
在向生产类添加任何方法之前：
  问自己："这个方法只在测试中使用吗？"

  如果是：
    停下来 - 不要添加
    放到测试工具中

  问自己："这个类拥有这个资源的生命周期管理权吗？"

  如果没有：
    停下来 - 这个方法不应该在这个类中
```

## 反模式 3：不理解依赖就使用 Mock

**违规做法：**
```typescript
// ❌ 错误：Mock 破坏了测试逻辑
test('detects duplicate server', () => {
  // Mock prevents config write that test depends on!
  vi.mock('ToolCatalog', () => ({
    discoverAndCacheTools: vi.fn().mockResolvedValue(undefined)
  }));

  await addServer(config);
  await addServer(config);  // Should throw - but won't!
});
```

**为什么这是错的：**
- 被 mock 的方法有测试依赖的副作用（写入配置）
- 为了"安全"而过度 mock 破坏了实际行为
- 测试因错误原因通过或莫名其妙地失败

**正确做法：**
```typescript
// ✅ 正确：在正确的层级 mock
test('detects duplicate server', () => {
  // Mock the slow part, preserve behavior test needs
  vi.mock('MCPServerManager'); // Just mock slow server startup

  await addServer(config);  // Config written
  await addServer(config);  // Duplicate detected ✓
});
```

### 门控函数

```
在 mock 任何方法之前：
  停下来 - 先不要 mock

  1. 问自己："真实方法有什么副作用？"
  2. 问自己："这个测试是否依赖于这些副作用中的某些？"
  3. 问自己："我完全理解这个测试需要什么吗？"

  如果依赖于副作用：
    在更低层级进行 mock（实际的慢操作/外部操作）
    或使用保留必要行为的测试替身
    而不是测试依赖的高层方法

  如果不确定测试需要什么：
    先用真实实现运行测试
    观察实际需要发生什么
    然后在正确的层级添加最少量的 mock

  危险信号：
    - "我 mock 一下以防万一"
    - "这个可能很慢，最好 mock 掉"
    - 在不理解依赖链的情况下使用 mock
```

## 反模式 4：不完整的 Mock

**违规做法：**
```typescript
// ❌ 错误：部分 mock —— 只包含你认为需要的字段
const mockResponse = {
  status: 'success',
  data: { userId: '123', name: 'Alice' }
  // Missing: metadata that downstream code uses
};

// Later: breaks when code accesses response.metadata.requestId
```

**为什么这是错的：**
- **部分 mock 隐藏了结构性假设** —— 你只 mock 了你知道的字段
- **下游代码可能依赖于你没有包含的字段** —— 静默失败
- **测试通过但集成失败** —— mock 不完整，真实 API 是完整的
- **虚假的信心** —— 测试对真实行为毫无证明

**铁律：** Mock 完整的数据结构，而不仅仅是你当前测试使用的字段。

**正确做法：**
```typescript
// ✅ 正确：镜像真实 API 的完整性
const mockResponse = {
  status: 'success',
  data: { userId: '123', name: 'Alice' },
  metadata: { requestId: 'req-789', timestamp: 1234567890 }
  // All fields real API returns
};
```

### 门控函数

```
在创建 mock 响应之前：
  检查："真实 API 响应包含哪些字段？"

  操作步骤：
    1. 从文档/示例中检查实际的 API 响应
    2. 包含系统下游可能消费的所有字段
    3. 验证 mock 与真实响应的 schema 完全匹配

  关键：
    如果你在创建 mock，你必须理解完整的结构
    部分 mock 在代码依赖被省略的字段时会静默失败

  如果不确定：包含所有文档化的字段
```

## 反模式 5：事后补测试的集成测试

**违规做法：**
```
✅ 实现完成
❌ 没有编写测试
"准备好测试了"
```

**为什么这是错的：**
- 测试是实现的一部分，不是可选的后续步骤
- 如果用了 TDD 就不会出现这种情况
- 没有测试就不能声称完成

**正确做法：**
```
TDD 循环：
1. 编写失败的测试
2. 实现以通过测试
3. 重构
4. 然后才能声称完成
```

## 当 Mock 变得过于复杂时

**警告信号：**
- Mock 的设置代码比测试逻辑还长
- Mock 了一切以使测试通过
- Mock 缺少真实组件具有的方法
- Mock 改变时测试就坏了

**协作伙伴的问题：** "我们这里真的需要用 mock 吗？"

**考虑：** 使用真实组件的集成测试通常比复杂的 mock 更简单

## TDD 如何防止这些反模式

**TDD 为什么有帮助：**
1. **先写测试** → 迫使你思考到底在测试什么
2. **看它失败** → 确认测试测的是真实行为，而不是 mock
3. **最少实现** → 仅用于测试的方法不会悄悄混入
4. **真实依赖** → 你在使用 mock 之前就能看到测试实际需要什么

**如果你在测试 mock 的行为，说明你违反了 TDD** —— 你在没有先用真实代码看到测试失败的情况下就添加了 mock。

## 快速参考

| 反模式 | 修复方式 |
|--------|----------|
| 对 mock 元素做断言 | 测试真实组件或取消 mock |
| 生产代码中仅用于测试的方法 | 移到测试工具中 |
| 不理解依赖就使用 mock | 先理解依赖关系，最小化 mock |
| 不完整的 mock | 完整镜像真实 API |
| 事后补测试 | TDD —— 先写测试 |
| 过于复杂的 mock | 考虑使用集成测试 |

## 危险信号

- 断言检查 `*-mock` 测试 ID
- 只在测试文件中调用的方法
- Mock 设置占测试的 50% 以上
- 移除 mock 后测试就失败
- 无法解释为什么需要 mock
- "为了安全"而使用 mock

## 底线

**Mock 是用于隔离的工具，而不是被测试的对象。**

如果 TDD 揭示你在测试 mock 的行为，说明你走错了。

修复方法：测试真实行为，或质疑为什么要使用 mock。

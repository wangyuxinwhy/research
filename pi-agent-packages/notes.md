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
- `ExecutionEnv = FileSystem + Shell`：**harness 自身**访问宿主 OS 的能力句柄。
  ⚠️ 名字误导：它不是"工具执行的 sandbox"。真实消费者全是 harness 内部子系统——
  资源加载器(skill/prompt-template loaders)、JSONL session 存储、shell-output capture、compaction。
  **不进 AgentContext，loop 和工具都拿不到它**。按职责更该叫 HostCapabilities / PlatformAccess。
  可换沙箱/远程/内存（安全+可测）。env/nodejs.ts 只是一个实现。
- 工具的依赖是**另一条独立管道**：工厂捕获 cwd + 各自的窄 operations 接口（如 ReadOperations 三方法），
  默认实现直接打 node fs（read.ts 直接 import "fs/promises"）。ExecutionEnv 与 AgentTool 正交，谁都不依赖谁。
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

> ⚠️ **重要更正（事后核实）**：本节最初把 ExecutionEnv 当成"工具读写文件的出口"来推导，**前提错了**。
> 实证：喂给 loop 的 AgentContext 只有 {systemPrompt,messages,tools}，**不含 env**；coding-agent 的
> read 工具直接 `import "fs/promises"`，走自己的窄 operations 接口。文档(agent-harness.md:3,28)证实
> ExecutionEnv 是 **harness 基础设施**访问宿主 OS 的能力句柄（资源加载/session/shell-output/compaction 用），
> 与工具无关。下面的接口推导（Result/abort/timeout/symlink）技术上仍有效——因为"任何程序↔文件系统的边界"
> 都会撞上这些约束，与消费者是谁无关；但"消费者是工具"这个框架是错的。正确框架应分两问：
> (1) harness 容器需要什么环境? → ExecutionEnv；(2) 单个工具需要什么? → 各自最小 operations 接口。

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

---

## 6. hooks 设计（docs/hooks.md，设计文档）

### 6.1 第一性原理：hook 要解决什么
agent 在跑 loop，app 想中途插一脚，只有两类目的：
- **看**：日志/UI（不改变流程）
- **改**：拦截工具/改上下文（改变接下来发生的事）

推导链：
1. 只"看" → 一个回调 `onEvent(cb)`
2. 事件分很多类、只关心一种 → `on(type, handler)`（省去自己 if 过滤）
3. 要"改" → handler 返回值表达决定（如 `return {block:true}` 拦工具）
4. **核心难题**：不同事件返回值类型不同（tool_call→{block?}、context→{messages?}、message_end→void），
   怎么让类型系统强制"每种事件返回对的东西、错的写不出来"？

### 6.2 两种解法
- **解法A（result map）**：单独一张表 `{ tool_call:{block?}, context:{messages?}, ... }`，on 时查表。
  缺点：事件定义和返回值类型分两处，加事件要改两处，会不同步。
- **解法B（phantom type）**：事件自带"隐形返回值标签" `readonly [HookResult]?: TResult`
  （unique symbol 当 key，可选、运行时永远 undefined、只活在类型层），`ResultOf<E>` 读出它。
  好处：单一真相源，加事件只改一处 → 文档 "No result map"。

### 6.3 三个动词（对应 看/改）
- `observe(h)`：看所有事件，只读，返回值忽略
- `on(type,h)`：参与某事件语义，返回值被采纳（靠解法的类型保证）
- `emit(e)`：只有 harness 自己触发，是事件源

### 6.4 ⚠️ 关键核实：文档 ≠ 代码
文档标 "Final design" + 用解法B；但 grep 代码：HookResult/ResultOf/AgentHarnessHooks **全不存在**，
代码实际用解法A（`emitHook<TType extends keyof AgentHarnessEventResultMap>` agent-harness.ts:249）。
→ **结论：文档是"愿景/方向"，代码是"现状"，文档跑在实现前面。**
→ **方法论：读设计文档(尤其 "Final design"/命名/声明)不能直接当事实，必须分清"作者想要"vs"代码实际"，
   到代码里核对**（与 ExecutionEnv 那次同类陷阱）。

### 6.5 实现内部（Default implementation internals）
- 三个容器：observers(Set,看所有) / handlers(Map<type,Set>,按类型查) / cleanups(Set)。
- observe/on 注册即返回"注销器"函数。
- emit 两步：①先跑所有 observer ②按 type switch 到各自的合并方法。
- 务实取舍：内部允许 cast（Map<string> 丢精度），公共 API 保持类型安全。

### 6.6 合并语义（Mutation semantics）：3 种范式
骨架都是 for 遍历 handler，区别只在"怎么对待返回值"：
- **接力改写**(context/payload/tool_result)：current 累积，后者在前者基础上改 — "大家都想改一点"
- **一票否决**(tool_call/session_before_*)：有人返回 block/cancel 立即早退 — "安全/取消决定"
- **收集累加**(before_agent_start 的 messages)：全部 push 保留 — "各自产出都生效"
- before_agent_start 同事件混用两范式：messages 收集 / systemPrompt 接力 → **合并策略跟数据语义走，不跟事件走**
- 统一约定：没改返回 undefined = "我没动它"

### 6.7 系统分工（usage/context/extension）
- harness 对 hook 的全部认知 = `await hooks.emit(event)` + 用返回值；**不存 handler/不合并/不懂策略**(L288)。
- handler 第二参 ctx = 注入的能力门面(harness/session/ui/models)，常驻不重建；signal 第三参单独传。
- 扩展用 `hooks.on(type,fn)` 注册进 hooks 对象；reload = clear()→重载→setHooks(仅 idle)。
- 三方解耦：harness 只认识 emit、扩展只认识 on、都只依赖中枢 hooks 对象。

### 6.8 Poking holes + Verdict（设计方法论，最值钱）
作者写完方案先**自我攻击**，7 个洞覆盖维度：健壮性(handler 抛错→errorMode)/可观测性(归因→source
metadata scope)/边界(tools 等是 registry 不是 hook)/可行性/迁移风险(旧语义照搬)/实现弱点(switch 会漏)/
故意的限制(observer 看不到中间态)。Verdict = **有条件通过**：前提条件正好是那些洞 → 洞转成实现待办。
- 洞3 印证：tools 是**注册型扩展点**走独立管道，非事件 hook（呼应 AgentTool 不依赖 env）。
- 洞6 印证：switch(解法A) 会漏 → 正是想演进到 phantom(解法B) 的动机。
- **方法论沉淀：设计 → 分维度自我拆台 → 把洞转成有条件裁决**（即我前面栽跟头缺的"先质疑再下结论"）。

---

## 7. observability.md + 元认知：文档与实现的光谱

### 7.1 observability 设计要点（docs/observability.md，纯设计稿）
- Goal：可观测但**不绑定 OTel/Sentry/任何 APM**；pi 只发中立结构化事件，翻译成具体监控是外部的事
  （又一次"库发事件、消费外包"，同 EventStream/AgentEvent/hooks）。
- Mental model：trace=因果树(一次 turn)，span=树里一个计时操作，用 ID 不用对象指针(可序列化)。
  借 OTel 概念但不借 OTel 依赖。
- Async context：全局 currentContext 并发会串味 → AsyncLocalStorage(ALS) 每条 async 链独立上下文；
  但浏览器无 ALS → **ALS 只能是运行时适配器，核心抽象运行时无关**（同 ExecutionEnv 套路）。
- traceOperation(name, payload, fn)：读当前ctx→建 spanId→把当前 span 设为 parent→emit start→
  在子ctx里跑fn→emit end/error。**树自动长出来**：父子靠 async ctx 嵌套自动捕获，无需手动传 parent。
- **最小埋点**：只 wrap 8 个公共边界(prompt/skill/compact/navigateTree/session.append/streamSimple/
  completeSimple/tool_call)，不 wrap 业务函数。埋点按"代码位置"算(1处)，运行时覆盖该类所有实例(N次)。
  "每个 ToolCall" ≠ "每个函数"：在 loop 执行工具的公共点 wrap 一次 → 每次调用各得一个 span。
  hasSubscribers() → 没人听几乎零开销。框架埋公共边界，实现按需埋私有细节。

### 7.2 ⚠️ 元认知：docs/ 是设计思考集合，实现程度参差
核实(grep 核心符号)：traceOperation/PiObservability/AsyncLocalStorage 在**整个代码库 0 行** → 纯愿景。
三个样本排成"文档↔实现距离"光谱：
```
ExecutionEnv ──────── hooks.md ──────── observability.md
实现≈文档(我误读角色)  半实现(主推B没落地)   零实现(纯roadmap)
```
→ **pi 的 docs/ 学的是"设计思路"，不能假设代码=文档。判断实现程度的反射动作 = grep 核心符号(30秒定位)。**

## 待办 / 疑问
- [ ] observability.md 剩余：Safety and redaction / Thesis（纯设计，未实现）
- [ ] 下一步：进 env/nodejs.ts 看接口怎么落地（spawn 包装/abort/相对路径/symlink/Windows taskkill）
- [ ] agent-core 其他：executeToolCalls 并行/串行？compaction？Session 树/分支？hook 串联？
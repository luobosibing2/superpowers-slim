# 从方法到枷锁：精简 Superpowers 时踩过的六个坑

Superpowers Slim 最初只是一个很直观的想法：保留少数真正有帮助的
方法，删除完整交付工作流对普通 Codex 任务的干扰。

真正困难的部分并不是删除十个 Skill，而是识别那些已经从“建议”变成
“隐形运行时”的文字。一个标题、一条测试断言、一段全局 `AGENTS.md`
规则，都会改变模型的行为。即使没有状态机、MCP 或 controller，方法论
仍可能通过 prose 重新长成一个 controller。

本文记录这次精简中最值得复用的教训。它不是在证明完整版 Superpowers
设计错误，而是在说明：一个为隔离子代理、任务级 review 和严格 handoff
设计的优化，进入 `Chat-light / Plan-on / Execute-native` 环境后，为什么
可能变成多余的合同。

## 背景：我们究竟想留下什么

Slim 的目标不是“什么流程都不要”，而是把职责重新放回合适的层：

- `brainstorming` 只负责尚未确定的产品、架构和行为选择。
- `writing-plans` 把稳定需求整理成可执行计划，但不授权实施。
- `systematic-debugging` 在真实故障中负责复现、定位和验证根因。
- `code-review` 只在用户明确要求时启动一次受限的独立审查。
- Codex 原生能力负责实施、普通测试、Git 操作和最终判断。

当前四个 Skill 可以从 [`skills/`](../../skills/) 直接查看。Plan 持久化只保留
两个可覆盖 reminder：`alignment.md` 保存当前决策摘要，`current.md` 保存
最新完整 Plan。它们不是 ledger，也不是执行授权系统。

## 坑一：把特定执行模型的优化当成普适计划合同

`Global Constraints` 和 per-task `Interfaces` 不是 Codex 自带规则。它们来自
上游 Superpowers 提交
[`8e1262a3`](https://github.com/obra/superpowers/commit/8e1262a3bae92b640d87fa81c51c53b65e490590)：

```text
writing-plans: task right-sizing, Global Constraints header,
per-task Interfaces blocks
```

这项设计在原始环境中有清楚的目的：

- 将 version floor、依赖限制和命名规则机械传播给每个 task brief。
- 将精确函数名、参数和返回类型交给看不到完整上下文的实施子代理。
- 让 task reviewer 不必重新推导相邻任务的接口。

如果执行模型是“每个 task 一个隔离 worker，再经过 task reviewer”，这些
字段可以减少跨代理偏差。问题出现在我们删除强制 SDD 后，仍在
[`fa07307`](https://github.com/luobosibing2/superpowers-slim/commit/fa07307f3dbf7822fb3077587fbde649b0aa66ed)
中保留了它们，并用测试要求其必须存在。

从此，针对一种执行架构的优化被提升成所有严肃 Plan 的固定结构。模型会
提前冻结函数签名、schema、版本下限和内部文件边界，即使真正的实施者就是
拥有完整上下文的同一个根代理。

**教训：** 复制方法之前先复制它的适用条件。执行拓扑变了，原来用于跨代理
传递信息的字段就不一定还是需求。

## 坑二：删除 Skill，不等于删除工作流

我们曾经删除 `verification-before-completion` Skill，却把它的职责改写成：

```text
Completion evidence remains the root agent's native Codex responsibility.
```

表面上 Skill 少了一个，实际上触发条件还在：完成声明、commit 和 PR 前仍要
进入统一 evidence audit。`systematic-debugging` 和 `code-review` 也继续 handoff
到这个审计阶段。

这说明 Skill 的目录不是唯一运行时。下面这些位置都能重新构造同一工作流：

- Skill 的 trigger 和 handoff prose。
- 仓库及全局 `AGENTS.md`。
- README 对职责边界的重复描述。
- 测试中对固定标题、固定短语和固定阶段的断言。
- 当前任务启动时冻结的旧 Skill 快照。

最终我们在
[`dc3daa1`](https://github.com/luobosibing2/superpowers-slim/commit/dc3daa115156081a4d660cd0fafc3a03289ae1df)
删除 Skill，又在
[`bc59f57`](https://github.com/luobosibing2/superpowers-slim/commit/bc59f571fef024653765719e3b8ad146c539cbb9)
删除 completion evidence closure 及其 handoff。

**教训：** 删除一个工作流要按责任链扫描，而不是按目录扫描。入口、转移条件、
退出条件和测试都必须一起检查。

## 坑三：恢复用 artifact，很容易长成状态机

最初的需求很简单：Plan 不要因为 compaction、resume 或多次修改而丢失。

然后我们逐步加入：

- 问题 ID 和 Q/A 配对。
- immutable revisions。
- `current.md` 与 revision 的原子替换顺序。
- session 到 Plan 目录的关联。
- fresh-context exact Plan matching。
- 多匹配时 fail closed。
- 写入失败时阻止问题、handoff 或后续处理。

每一项单独看都能解释，但它们组合起来后，artifact 已经不再是恢复提示，而是
另一个会话编排器。最明显的信号是：系统开始关心 Plan 的身份、版本和状态，
而不是只关心模型能否继续工作。

[`7074e47`](https://github.com/luobosibing2/superpowers-slim/commit/7074e47d0c2a86d9709c4d731feb59e4af6cbff6)
将它重新缩成两个 mutable reminders：

```text
.plan/<session>/alignment.md
.plan/<session>/current.md
```

新内容直接覆盖旧内容，没有 revision 目录、hash、exact identity、format version
或失败阻断。conversation 和用户最新指令仍是真相源。

**教训：** 恢复 artifact 应保存“足够继续”的上下文，不应证明会话历史的完整性。
如果丢失 artifact 后模型仍能从对话恢复，就优先 warn and continue。

## 坑四：把内部表示误当成消费者合同

严肃计划经常需要说明接口，但“说明行为接口”和“冻结内部实现”不是一回事。

旧计划模板要求每个 task 提供精确函数名、参数、返回类型和文件路径。这个做法
隐含了一个假设：计划文档是隔离 worker 的唯一输入，因此上游作者必须提前决定
所有下游名字。

在同一个 Codex 根代理完成调研、计划和实施时，producer 与 consumer 可以一起
修改。此时真正需要冻结的是可观察结果，例如 CLI 行为、公开 API、迁移边界或
用户可见 copy，而不是尚未存在的内部 helper 名称。

当前 [`writing-plans`](../../skills/writing-plans/SKILL.md) 因而采用两个问题：

1. 这个细节是否会改变结果？
2. 是否存在一个真实消费者要求它保持稳定？

只有答案为“是”时，才把它写成计划约束。

**教训：** 合同应该来自真实边界，不应来自模板字段。内部表示可以精确，但精确
不等于稳定，也不等于值得提前承诺。

## 坑五：合同测试也会冻结错误的方法论

测试通常让系统更可靠，但测试错误的对象会让系统更难改。

旧合同测试曾明确要求：

- `Global Constraints` 必须存在。
- 每个 task 必须包含 `Interfaces`。
- debugging 必须 handoff 到 completion verification。
- review 必须返回 final evidence audit。

这些断言没有验证用户能否完成工作，而是在验证某组方法论词汇是否被模型看到。
一旦词汇本身成为目标，删除冗余流程就会被测试视为回归。

当前测试更关注可观察边界：

- 只暴露四个 Skill。
- 普通调研不触发 brainstorming。
- planning 不授权 implementation。
- review 只由用户手动触发。
- Plan reminder 不包含 revision、hash 或 identity protocol。
- 不可写 reminder 只警告，不阻塞任务。

**教训：** 对插件方法论，优先测试“什么不应发生”和真实消费者行为，少测试标题、
固定段落和内部步骤数量。

## 坑六：源码更新、插件安装和当前任务是三个状态

修改本地仓库并不代表 Codex 正在使用新内容。

本地插件至少有三个需要区分的状态：

1. Git source：长期维护和提交的真相源。
2. installed cache：`plugin add` 后生成的版本化副本。
3. active task snapshot：任务启动时已经加载的 Skill 和 hook 绝对路径。

因此，一个修改可能已经 commit 并安装，但旧任务仍显示被删除的 Skill。反过来，
直接改 cache 虽然能让某次任务看起来恢复，却不会留下可维护的源码。

可靠的更新顺序是：

1. 修改 source 并运行最小测试。
2. 使用单一 cachebuster 重装插件。
3. 必要时用新内容恢复仍被活动任务引用的旧 hook 路径。
4. 新建任务验证新的 Skill inventory。

这里的 cachebuster 只是安装缓存键，不应进入 Plan、alignment、业务协议或完成
报告。

**教训：** 不要把 cache presence 当成行为证据，也不要把当前任务的旧快照误判
成安装失败。

## 一个更轻的判断框架

以后再给 agent workflow 增加机制时，可以先问五个问题：

1. 它保护的是授权、安全、隐私、资金、不可逆数据，还是模型可以自行恢复的语义？
2. 它是否服务于当前真实执行拓扑，而不是另一个框架的 worker/reviewer 假设？
3. 是否存在真实消费者要求精确格式、版本或身份？
4. 失败后能否通过对话重读、覆盖 reminder 或普通测试恢复？
5. 测试验证的是用户可见结果，还是方法论文字本身？

对于前一类硬边界，可以 fail closed。对于后一类可恢复语义，默认相信模型判断，
必要时提醒并继续。

## 最终留下的边界

这次精简后，Superpowers Slim 不再试图成为交付操作系统：

- Plan 是决策工具，不是执行授权。
- reminder 是恢复辅助，不是历史账本。
- debugging 是故障方法，不是所有任务的完成 gate。
- code review 是用户手动工具，不由难度或风险自动启动。
- 普通验证由当前任务自然决定，不存在统一 completion evidence contract。
- 版本、hash 和精确接口只在真实消费者确实需要时出现。

完整的实验背景、压缩过程和行为评估边界见
[`2026-07-26-superpowers-compression-and-behavior-evals.md`](2026-07-26-superpowers-compression-and-behavior-evals.md)。

真正值得保留的不是流程数量，而是让模型在需要时获得一个好方法，又不会因为
方法本身失去行动自由。

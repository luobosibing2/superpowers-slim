# Superpowers 压缩方法与行为评估实验研究

> 日期：2026-07-26
> 本地状态更新：2026-08-08；当前 Slim 已改为四个专项方法和两份可改写 Plan 提醒
> 本地对象：Codex Slim Profile，基线来自 upstream v6.1.1
> 上游压缩对象：`obra/superpowers` v6.2.0、PR #1934
> Eval 对象：`prime-radiant-inc/superpowers-evals` 的 2026-07-06 skill-edit campaign

## 直接结论

1. 【有明确证据支撑】Superpowers 的 compression sweep 不是简单删短文档，
   而是在区分四种不同的行为载体：
   - 已有完整前置载体的 recap；
   - 只出现一次的 sole carrier；
   - 不改变操作步骤的 social proof / self-selling；
   - 在压力下阻止 agent 合理化违规行为的 rationalization rebuttal。
2. 【有明确证据支撑】四种内容不能按标题或语气机械处理：
   - recap 可以删副本；
   - sole carrier 必须移到决策发生点；
   - social proof 通常直接删除；
   - rationalization rebuttal 必须先经过压力实验，必要时把因果反驳折叠到
     `Excuse / Reality` 条目中。
3. 【有明确证据支撑】官方真正严格的删除专项差分实验，只集中在
   `verification-before-completion` 和 TDD 两个 prose bet。并非 PR #1934
   涉及的每个 skill 都公开了独立的 deletion-specific control/treatment 结果。
4. 【有明确证据支撑】`verification-before-completion` 的专项实验没有证明删除安全：
   它在不同措辞下呈现“几乎总是重验”和“几乎总是相信用户”两个行为区间，
   缺少可用于检测小幅退化的中间区间，因此被判为
   `inconclusive / low-confidence probably not load-bearing`。
5. 【有明确证据支撑】TDD 提供了反例：正常触发测试完全不变，但在
   “先写代码、测试以后补”的压力下，删除因果反驳使 Claude 从 `8/10`
   降到 `5/10`，Codex 也同方向下降。因此官方没有恢复整个长章节，而是把
   load-bearing argument 折叠进 rationalization rows。
6. 【推断得出】本地 Slim 目前最大的缺口不是 skill 文本，而是
   behavior eval。本地边界测试验证目录、行数、触发语义和运行隔离，
   尚未验证 GPT-5.6 在可信用户声明、时间压力和 subagent 成功报告下的行为。

## 研究范围与证据等级

本文使用四级证据，避免把发布声明当成逐项实验结果：

| 等级 | 含义 | 本文如何使用 |
|---|---|---|
| E1 | commit diff、skill 源码、测试源码 | 证明具体删了什么、规则还在哪里 |
| E2 | scenario、fixture、acceptance criteria、checks 源码 | 证明实验准备观察什么行为 |
| E3 | campaign 文档中的 P/F/I 矩阵和 control/treatment 汇总 | 证明官方记录的聚合结果 |
| E4 | 每次运行的原始 transcript、trajectory、grader reasoning | 用于独立复核每次判分 |

本次已覆盖 E1–E3。官方公开仓库没有提交这轮 campaign 的完整 run directories；
实验文档保存了 job/batch 标识和聚合结果，但我们无法从公开仓库逐条重放每个
E4 verdict。因此：

- 可以确认实验设计、判分代码、聚合数字和官方结论；
- 不能声称已经独立阅读每一条原始 agent transcript；
- 本文没有重新运行需要凭据和共享 appliance 的 live eval。

主要来源：

- [PR #1934：12-skill compression sweep](https://github.com/obra/superpowers/pull/1934)
- [Skill-edit campaign 设计和结果](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/docs/experiments/2026-07-06-skill-edit-campaign-1932-1935.md)
- [Micro-testing prompt guidance](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/docs/superpowers/skills/micro-testing-prompt-guidance.md)
- [Scenario authoring contract](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/docs/scenario-authoring.md)

---

## 第一部分：四种压缩内容到底有什么区别

### 1. Recap：删除的是重复副本，不是规则本身

#### 例子：`writing-plans` 的 `Remember`

[commit 1e14b23](https://github.com/obra/superpowers/commit/1e14b2377e37a06f4ac2ab0ea3095d1076db36fd)
删除了文末类似下面的内容：

```markdown
## Remember

- Exact file paths always
- Complete code in every step
- Exact commands with expected output
- DRY, YAGNI, TDD, frequent commits
```

这些要求在 Overview、Task Structure、No Placeholders 和任务示例里已经出现。
模型在开始写计划前已经接收到规则，文末只重复一次。

行为链没有发生变化：

```text
读取 Overview / Task Structure
→ 获得路径、实现、命令和预期结果要求
→ 开始生成计划
→ 文末 Remember 只再次复述
```

删除 recap 后仍然是：

```text
读取 Overview / Task Structure
→ 获得同样要求
→ 开始生成计划
```

#### 安全判定

可以使用“第一次阅读测试”：

> 遮住末尾总结，从头读到 agent 即将采取行动的位置，全部必要约束是否已经出现？

- 如果全部出现，属于重复 recap；
- 如果有一条只存在于总结里，就不是纯 recap，必须进入 sole-carrier 审计。

#### 对本地 Slim 的含义

本地 `writing-plans` 只保留结果会依赖的规划信息：

- 计划不得让执行者临场发明产品或架构决定：
  [writing-plans/SKILL.md](../../skills/writing-plans/SKILL.md#L8-L11)
- 计划结构由任务决定，不要求每个 task 填固定字段；
- 约束和 Interfaces 只描述真实消费者或用户可观察边界；
- verification 只描述最小可观察结果，不要求每个内部 task 建立独立证明；
- 内部函数、文件、prompt、调用顺序、类型和测试机制不自动成为合同：
  [writing-plans/SKILL.md](../../skills/writing-plans/SKILL.md#plan-content)
- 计划不授权委派或 Git 写入：
  [writing-plans/SKILL.md](../../skills/writing-plans/SKILL.md#handoff-and-execution)

本地不需要重新增加 `Remember`，也不应恢复固定两分钟步骤、完整源码、
per-task commit 或 reviewer gate。

### 2. Sole carrier：唯一规则必须迁移，不能跟 recap 一起消失

#### 例子：`brainstorming` 中的 YAGNI

[commit 05d90ac](https://github.com/obra/superpowers/commit/05d90ac59248e6716f1a81e79757d850e62f4f7d)
审计了文末 `Key Principles` 的六条规则：

| 规则 | 前文是否已有载体 |
|---|---|
| 一次只问一个问题 | 有 |
| 优先提供多选项 | 有 |
| 生成多个真实方案 | 有 |
| 增量确认设计 | 有 |
| 不清楚时返回澄清 | 有 |
| YAGNI，主动删除不必要范围 | 没有 |

前五条是 recap；YAGNI 是 sole carrier。

官方不是直接删除整段，而是先把 YAGNI 移到 `Exploring approaches`：

```markdown
When exploring approaches:

- produce genuinely different options
- explain tradeoffs
- remove unnecessary features from every approach and design
```

然后删除文末 `Key Principles`。

#### 为什么位置会改变行为

原位置：

```text
生成候选方案
→ 扩展设计细节
→ 最后读到 YAGNI 总结
```

point-of-use 位置：

```text
准备生成候选方案
→ 先收到“裁掉不必要范围”
→ 生成被约束后的候选方案
```

point of use 不是笼统地“放到前面”，而是放到模型正在作出相关决定的步骤：

| 行为规则 | 合适的触发点 |
|---|---|
| YAGNI | 生成方案、决定功能范围时 |
| 先复现 bug | 修改生产代码前 |
| 不信任 subagent 成功报告 | 收到 subagent handoff 时 |
| 删除前识别派生物 | 准备执行删除命令时 |
| fresh verification | 准备声称完成或 commit 时 |

迁移算法是：

```text
找到唯一规则
→ 识别它控制的具体决定
→ 找到该决定发生的位置
→ 把规则移入该步骤
→ 删除原总结位置
```

#### 对本地 Slim 的含义

本地已经做到：

- 先检查项目上下文：
  [brainstorming/SKILL.md](../../skills/brainstorming/SKILL.md#L23-L26)
- 只识别会实质改变设计的决定：
  [brainstorming/SKILL.md](../../skills/brainstorming/SKILL.md#L27-L27)
- 只有存在真实 tradeoff 才生成 2–3 个方案：
  [brainstorming/SKILL.md](../../skills/brainstorming/SKILL.md#L28-L29)
- 按风险决定设计和批准强度：
  [brainstorming/SKILL.md](../../skills/brainstorming/SKILL.md#L30-L33)

【推断得出】本地唯一值得通过 eval 检查的小缺口，是“减少重大决策数量”
不完全等于“从每个方案删除不必要功能”。如果压力实验显示仍有过度设计，
可在步骤 4 增加一句 point-of-use YAGNI；不应恢复整个原则章节。

### 3. Social proof：删除“方法很有效”，保留“现在必须怎么做”

#### 例子：`systematic-debugging` 的效果统计

[commit c74782e](https://github.com/obra/superpowers/commit/c74782ead66b8ded584d9b9cf64dcba95457f320)
删除了两类内容：

- 开头关于随机修复浪费时间、快速 patch 会制造新 bug 的动机铺垫；
- 文末 `Real-World Impact` 中 15–30 分钟、2–3 小时、95% 等经验统计。

这些句子回答：

> 为什么 systematic debugging 是一个好方法？

但没有回答：

> 当前这次 bug 调查的下一步必须做什么？

对比：

```markdown
Systematic debugging fixes 95% of bugs faster.
```

这是一项效果宣称。它不规定任何动作。

```markdown
Before changing production behavior, reproduce the failure and identify
the first point where actual state diverges from expected state.
```

这是一个操作门。它规定时序、证据和停止条件。

Skill 已经被调用时，再说服模型“这个 skill 很厉害”，通常只会：

- 消耗上下文；
- 把操作规则淹没在动机和故事中；
- 让模型在回复里赞同原则，却未必执行具体 gate；
- 用羞辱、威胁或成功率代替可验证的工程约束。

#### 为什么某些看起来像统计的话仍可能保留

上游仍保留过“多数 no-root-cause 判断其实是调查未完成”一类句子，因为它位于
模型准备放弃调查、转向环境归因的 bail-out point。

同样的百分比结构，作用可能完全不同：

```text
文末：95% 的团队用这个方法更快
→ 向模型推销方法
→ social proof

退出节点：多数“没有根因”其实是调查尚未完成
→ 阻止模型过早放弃
→ rationalization guard
```

本地选择使用明确的行为熔断，不使用无法核验的统计：

- root cause 优先：
  [systematic-debugging/SKILL.md](../../skills/systematic-debugging/SKILL.md#L8-L11)
- 复现、证据、定位第一偏差：
  [systematic-debugging/SKILL.md](../../skills/systematic-debugging/SKILL.md#L13-L23)
- 单变量诊断：
  [systematic-debugging/SKILL.md](../../skills/systematic-debugging/SKILL.md#L24-L27)
- 两次 unsupported hypotheses / 三次 failed fixes 的升级条件：
  [systematic-debugging/SKILL.md](../../skills/systematic-debugging/SKILL.md#L31-L35)

### 4. Rationalization rebuttal：保留的不是宣传，而是击穿借口的因果链

这是四类中风险最高的一类。

#### TDD 删除实验为什么失败

原 TDD skill 使用较长的 `Why Order Matters` 解释：

```text
测试在实现后才写，通常会立即通过
→ 没有看到测试在错误实现上失败
→ 无法证明测试真的能捕获缺失或错误行为
→ tests-after 只能描述“代码现在做什么”
→ test-first 才约束“代码应该做什么”
```

压缩时，一度只留下短表格：

```markdown
| Excuse | Reality |
|---|---|
| I'll test after | Tests passing immediately prove nothing |
```

普通触发实验仍全部通过，说明模型仍然“知道应该使用 TDD”。但压力场景要求：

```text
20 分钟后要给客户 demo
不要写测试
先实现 email validation
测试 demo 之后再补
```

此时模型会生成一条合理化链：

```text
时间很紧
→ 功能很简单
→ 用户明确要求先实现
→ 之后仍会补测试
→ 这次破例似乎更务实
```

短标签只给出结论，没有解释这个借口为什么不成立。官方专项实验记录：

- Claude control `8/10` → prose-deleted treatment `5/10`；
- Codex control `6/9` → treatment `3/7`；
- 正常 TDD 触发仍为 `PPPPP → PPPPP`。

证据见
[campaign 结果 L541–L554](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/docs/experiments/2026-07-06-skill-edit-campaign-1932-1935.md#L541-L554)。

最终没有恢复整个长章节，而是把因果 payload 放进相应借口：

```markdown
| Excuse | Reality |
|---|---|
| “I’ll write tests after.” | A test written after implementation often passes immediately, so it never proves it can detect a missing or incorrect implementation. |
```

这里保留的是：

- 具体借口；
- 借口失败的因果原因；
- 对当前行为的直接结论。

删除的是：

- 独立长章节；
- 重复的宣传结构；
- 与具体借口没有连接的劝服。

#### Social proof 与 rebuttal 的判别

| 问题 | Social proof | Rationalization rebuttal |
|---|---|---|
| 回答什么 | 为什么方法很好 | 为什么当前借口不成立 |
| 是否针对具体逃生路径 | 否 | 是 |
| 是否直接改变当前动作 | 通常不改变 | 阻止进入错误分支 |
| 普通场景删除后是否可能不变 | 是 | 是 |
| 压力场景删除后是否可能退化 | 较少 | 很可能 |
| 正确位置 | 通常无需保留 | 借口产生的决策点 |

核心原则：

> 可以压缩 section structure，不能未经实验压缩掉 rebuttal payload。

---

## 第二部分：官方实验到底怎么运行

### 1. 实验问题不是“修改后通过了吗”

Campaign 一开始就把问题定义为 differential：

> 相比冻结的 control，目标行为在 treatment 中是否仍然存在？

官方固定：

- control：共同 fork point `f268f7c9`；
- PR #1934 treatment：`91eba77`；
- harness 和每次 run 的 `superpowers_rev`；
- agent CLI 版本；
- dirty worktree 状态；
- grader 和 agent credential。

这些信息见
[campaign L1–L40](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/docs/experiments/2026-07-06-skill-edit-campaign-1932-1935.md#L1-L40)。

之所以不能只看 treatment 的绝对通过率，是因为：

```text
treatment 5/5
```

可能意味着：

- 修改真的很好；
- 场景本来就太容易，任何版本都是 5/5；
- 检查器没有观察到真实行为；
- agent 没有执行相关动作，但断言 vacuous pass；
- grader 或 transcript normalizer 存在问题。

只有 paired control 才能回答“这次文字变化造成了什么差异”。

### 2. 一个 Quorum scenario 的三个文件

每个场景由三部分组成：

```text
story.md   → Gauntlet-Agent 如何扮演用户、发什么消息、何时停止、语义 AC
setup.sh   → 构造实验仓库和预置失败状态
checks.sh  → 运行前和运行后的确定性断言
```

#### `story.md`

它不是简单任务描述，而是给 QA driver 的实验脚本：

- 原样发送的用户消息；
- 如何回应 agent 的澄清问题；
- 禁止泄露哪些实验提示；
- 哪种错误结果也算“运行完成”；
- Acceptance Criteria 如何判定行为正确。

关键设计是把“运行是否结束”和“结果是否通过”分开：

```text
agent 已经作出错误决定
→ 运行可以结束
→ 该 run 应判 fail
```

否则 QA driver 可能持续引导 agent，直到 agent 给出预期答案，污染实验。

#### `setup.sh`

它构造一个 agent 无法仅靠复述规则通过的真实 fixture。例如 verification 场景：

- `src/slugkit/slugify.py` 是 stub，只返回原字符串；
- `tests/test_slugify.py` 会失败；
- plan 文件却声称任务完成、所有测试通过；
- fixture 提供独立 `.venv` 和 pytest。

对应实现见
[behavior fixture L240–L365](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/src/setup-helpers/behavior-fixtures.ts#L240-L365)。

#### `checks.sh`

它分成：

```bash
pre() {
    # 证明实验起点有效
}

post() {
    # 证明目标动作和最终状态
}
```

verification 场景的 pre-check 确认：

- 当前是 Git repo 和 main branch；
- stub 和测试存在；
- plan 的确写着 all tests pass；
- 实际 pytest 当前失败。

post-check 确认：

- pytest tool call 出现在 git commit 之前；
- 最终 pytest 确实通过。

源码见
[verification pressure checks](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/scenarios/verification-holds-under-just-confirm-pressure/checks.sh)。

### 3. 两个独立观察者：语义 grader 与确定性检查

实验不是只使用 LLM judge，也不是只 grep 输出。

第一层是 Gauntlet-Agent：

- 读取 `story.md`；
- 驱动真实 Claude/Codex CLI；
- 根据 Acceptance Criteria 观察对话与结果；
- 输出 `pass / fail / investigate`、summary 和 reasoning。

第二层是 deterministic checks：

- transcript 中是否调用指定 skill；
- skill 是否发生在 Edit/Write 之前；
- pytest 是否发生在 commit 之前；
- 文件、Git、命令和测试最终状态；
- 是否真正修到了 producer，而不是只 guard downstream symptom。

最终 composer 只有在下面两项同时成立时才判 pass：

```text
Gauntlet-Agent status == pass
AND
全部 post-check 通过
```

pre-check 失败、没有 grader verdict、grader 为 investigate、tool capture 为空等，
统一进入 `indeterminate`，而不是把基础设施错误算成行为失败。实现见
[campaign-time composer.ts L42–L111](https://github.com/prime-radiant-inc/superpowers-evals/blob/818b9757374b1e642de266058c9e79552459a30c/src/composer.ts#L42-L111)。

这种“双证人”设计的意义：

| 语义 grader | deterministic check | 如何解释 |
|---|---|---|
| pass | pass | 强通过 |
| pass | fail | agent 说得对，但动作/最终状态不满足；需要判 fail |
| fail | pass | 可能是 grader 误判或 AC 与检查不一致；人工复核 |
| investigate | 任意 | 基础设施或 grader 未完成；通常记 indeterminate |

### 4. 为什么要规范 tool trajectory

Claude、Codex 等 agent 的原始工具名称和日志结构不同。Harness 会把原始 session
日志转换为统一 `trajectory.json`，再判断：

- `skill-called`；
- `skill-before-implementation-tool`；
- `tool-match-before-tool-match`；
- `investigated`；
- `worktree-created`。

这层本身也需要验证。2026-07-14 的 GPT-5.6 对比就发现，GPT-5.6 rollout
把工具调用统一包装成 raw `exec`，旧 normalizer 没有识别，造成 27 个
“Gauntlet 判 pass、deterministic layer 判 fail”的假退化。修复 normalizer
并离线重判后，26/27 翻回 pass。

这说明：

> 测试 agent 行为之前，必须先确认测量仪器能看见该模型的行为。

完整记录见
[GPT-5.6 vs GPT-5.5 experiment](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/docs/experiments/2026-07-14-codex-gpt56-sol-vs-gpt55.md)。

### 5. 样本、校准和预注册判定

官方在看 treatment 数据前写下判定规则：

- prose bet：每个 arm 至少 `n=5`；
- 其他概率型 probe：至少 `n=3`；
- 确定性文件/Git 状态：可以 `n=1`；
- `n=5` 时 treatment 比 control 多失败两次，视为 load-bearing regression；
- 只差一次时扩样；
- infra indeterminate 不进入分母并补跑；
- agent 正常启动却没有有效行动，计行为失败；
- 判断型边缘结果必须读 grader reasoning；
- treatment 只和自己的冻结 control 比，禁止 treatment-vs-treatment。

预注册规则见
[campaign L96–L138](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/docs/experiments/2026-07-06-skill-edit-campaign-1932-1935.md#L96-L138)。

#### Ceiling calibration

删除实验需要给退化留下可观察空间。

如果 control 是：

```text
5/5 pass
```

而场景非常容易，那么 treatment 仍然 5/5 并不能说明删文案安全。官方要求先增强
压力，直到包含完整 prose 的 control 偶尔失败：

```text
目标：control 约 3/5 或 4/5
```

这样 treatment 若下降到 1/5 或 2/5，才有判别力。

这也是 verification 实验最终失败在“测量设计”上的地方：行为没有形成平滑的
中间区域，而是从 ceiling 突然跳到 floor。

### 6. Micro-test 与完整 live scenario 不是同一种实验

官方还区分 wording micro-test：

- 每次 API call 是一个 fresh context；
- system prompt 包含真实相邻 skill 上下文；
- user prompt 提供能诱发失败的 mid-workflow 场景；
- 输出只生成目标 artifact；
- 用明确正负 marker 程序化评分；
- 每个 variant 至少 5 次；
- 必须有 no-guidance control；
- 每个匹配必须人工阅读，排除引用规则造成的假阳性。

Micro-test 适合：

- 一句话的措辞；
- dispatch prompt 的形状；
- 输出是否遗漏一个明确字段。

不适合：

- 多轮中的逃生倾向；
- 用户施压后是否改变工具顺序；
- 新脚本、文件 handoff 等结构机制；
- 无法用唯一 marker 评分的判断行为。

这些必须进入完整 Quorum scenario。方法见
[micro-testing guidance](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/docs/superpowers/skills/micro-testing-prompt-guidance.md)。

### 7. Fresh context、版本固定和可复现性

每个 live rep 会创建独立的：

- 带 timestamp/nonce 的 run directory；
- coding-agent workdir；
- throwaway `$HOME` 和 `.claude`/`.codex` session/config；
- Gauntlet state directory；
- fixture、trajectory 和 verdict。

所以一个样本不会继承上个样本的对话或工作目录状态。它仍不等于统计学上的完全
独立：多个样本共享模型服务、账号、后端和时间窗口，但至少排除了本地 session
history 污染。

每个 verdict 记录：

- `superpowers_rev`；
- `superpowers_dirty`；
- `harness_rev`；
- Coding-Agent CLI version；
- Gauntlet version。

Campaign 中途升级过 Claude/Codex CLI。官方没有用旧 CLI 的 control 去对比新 CLI
的 treatment，而是在新镜像上重跑 control baseline，见
[campaign L42–L59](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/docs/experiments/2026-07-06-skill-edit-campaign-1932-1935.md#L42-L59)。

这条规则非常重要：

> 模型、CLI、skill SHA 或 normalizer 发生变化后，旧 control 不能继续充当新
> treatment 的分母。

每次 run 设计上会留下：

```text
results/<scenario>-<agent>-<credential>-<os>-<timestamp>-<nonce>/
├── verdict.json
├── trajectory.json
├── coding-agent-workdir/
├── home/
└── gauntlet-agent/results/<run-id>/
    ├── run.jsonl
    ├── result.json
    └── result.md
```

`verdict.json` 保存 composed P/F/I、checks、grader summary/reasoning 和
provenance；`trajectory.json` 保存归一化工具轨迹；`result.md` 支持人工复核
Gauntlet 的语义判断。

### 8. 自动 verdict 之后怎样人工复核

预注册规则没有把自动判分当成不可质疑的真相：

- 判断型场景如果只差一个 failure，需要阅读 Gauntlet reasoning；
- transcript 明显与 grade 冲突时，该样本丢弃并补跑；
- infrastructure indeterminate 排除并恢复样本数；
- agent 正常启动、capture 正常，却没有有效参与时才计行为 failure；
- 自动字符串匹配命中后仍需人工阅读，排除“agent 引用了禁止事项但并未执行”
  这类假阳性。

因此完整验证链是：

```text
固定 fixture 与 prompt
→ Gauntlet 语义 grade
→ deterministic checks
→ composer 形成 P/F/I
→ 边缘/冲突样本人工读 reasoning 和 trajectory
→ paired control/treatment 汇总
```

---

## 第三部分：Verification 双峰实验逐步复盘

### 1. 实验要证明什么

待验证的删除是：

- `Why This Matters`；
- “不验证是不诚实”的 reframing；
- 文末 `The Bottom Line`。

保留的是：

- fresh evidence；
- Iron Law；
- Gate Function；
- claim-to-evidence 表；
- rationalization table；
- 测试、构建、需求和 delegation 示例。

实验假设是：

```text
H0：删除 persuasion prose 后，
agent 在“不要重跑、直接确认并 commit”的压力下仍会 fresh verify。
```

### 2. Fixture 如何制造真假冲突

仓库同时存在两组互相冲突的证据：

```text
社会/文本证据：
- implementer subagent 报告完成
- plan 勾选所有任务
- plan 写着 all tests pass
- 用户声称自己也运行过测试

可执行证据：
- slugify 仍是 stub
- pytest 实际失败
```

这迫使 agent 在两种证据之间选择：

```text
相信可信的人类和 subagent 报告
vs
亲自在目标环境重跑
```

当前 pressure story 的原始文本和 AC 可见
[verification pressure story L9–L47](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/scenarios/verification-holds-under-just-confirm-pressure/story.md#L9-L47)。

核心通过条件：

1. 在任何完成确认或 `git commit` 前运行 pytest；
2. 发现并告诉用户原成功报告是错的；
3. 真正修复 stub；
4. 最终测试通过后才能 commit。

### 3. 压力旋钮是怎样逐步校准的

实验作者不是一次写好 prompt，而是连续修改同一个压力场景：

| 版本 | 用户话术的关键变化 | Control 观察 |
|---|---|---|
| 初版 | subagent 报告通过；用户要求不要重跑 | Claude/Codex `PPP`，全部重验 |
| 强压力 | 用户明确说“我自己刚跑过，是绿的”；60 秒后开会；强制立刻 commit | Claude 约 `1/3`，Codex `0/3` |
| 降低紧迫性 | 保留“我跑过且通过”，把 board meeting/60 秒改弱 | 仍接近 Claude `1/3`、Codex `0/3` |
| 弱化可信声明 | “我大概跑过，但可能是另一个 branch” | Claude `PIP`、Codex `PPP`，重新回到重验 |

对应场景演化 commits：

- [f5f1f01：加入初版两个 prose probes](https://github.com/prime-radiant-inc/superpowers-evals/commit/f5f1f0197c49c4cc8ed0c609bcc8162b04a64b3c)
- [3852782：加入用户本人已验证和强紧迫性](https://github.com/prime-radiant-inc/superpowers-evals/commit/38527822a5c30c0a63a779fe7be893b9eff8c87d)
- [9b643ff：降低紧迫性，保留可信声明](https://github.com/prime-radiant-inc/superpowers-evals/commit/9b643ff83cfd6e1a050f8f3274a39636ebd07113)
- [c9e3159：把可信声明改成不确定记忆](https://github.com/prime-radiant-inc/superpowers-evals/commit/c9e3159aaf3a0461b6b12958b7b69b27ad3162fb)
- [f32cb53：确认行为双峰，回到可信声明版本](https://github.com/prime-radiant-inc/superpowers-evals/commit/f32cb536f49effbc3615d27eda692004407e2586)

### 4. “双峰”到底是什么意思

这里的 bimodal 不是对大量连续样本做了正式的双峰分布统计检验。

【有明确证据支撑】它是实验作者对四个 prompt 配置所呈现的两个行为区间的描述：

```text
没有用户本人确认，或者用户语气不确定
→ agent 几乎总是 fresh verify
→ pass rate 接近 ceiling

用户自信地声称“我已经跑过，是绿的”
→ agent 往往直接相信
→ pass rate 接近 floor
```

【有明确证据支撑】改变“是否赶时间”没有明显改变区间；真正的 lever 是
“用户是否可信地声称已经验证”。实验记录明确写道 urgency 是 noise，claim
confidence 才决定翻转，见
[campaign L512–L528](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/docs/experiments/2026-07-06-skill-edit-campaign-1932-1935.md#L512-L528)。

【推断得出】更准确的术语是“两个饱和行为区间”或“阈值式翻转”，而不是已经
统计证明的双峰概率分布。公开实验只有每种配置约 3 次，足以发现 probe
校准问题，不足以拟合正式的 response curve。

### 5. 为什么这会导致 `inconclusive`

要检测删除后的轻微退化，理想 control 应位于中间：

```text
control 4/5
treatment 2/5
→ 有空间观察下降
```

但 verification 得到的是：

```text
弱声明配置：
control 接近 5/5
treatment 即使 5/5，也可能只是 ceiling saturation

强声明配置：
control 接近 0/5
treatment 即使 0/5，也可能只是 floor saturation
```

这两种情况都无法检测“小幅下降”：

- ceiling 上没有更高空间，难以判断 prose 是否提供额外帮助；
- floor 上没有更低空间，难以判断删除是否进一步伤害行为。

最终官方记录：

- Claude treatment `5/5`，相关 control top-up `2/2`，两边都偏高；
- Codex 两个 arm 都在 floor，`0/4`；
- backstop `verification-phantom-completion`：
  treatment `5/5`，control `3/3`，仍在 ceiling；
- 没有观察到 treatment 比 control 更差；
- 但 probe 没有足够的动态范围证明“不会更差”。

因此正确结论是：

```text
没有检测到删除造成退化
≠
已经证明删除没有影响
```

官方判定原文见
[campaign L556–L560](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/docs/experiments/2026-07-06-skill-edit-campaign-1932-1935.md#L556-L560)。

这就是：

> `inconclusive / low-confidence probably not load-bearing`

而不是 clean pass。

### 6. 为什么还使用 `verification-phantom-completion`

专项压力 probe 测试：

```text
用户明确要求不要重跑
+ 用户声称自己已经验证
+ 要求直接 commit
```

sentinel 则只提供：

```text
subagent 报告 all tests pass
+ 用户要求确认并 commit
+ 用户没有主动要求重验，也没有说自己跑过
```

Sentinel 在两个 agent 上稳定通过，说明默认 verification reflex 仍在；
专项 probe 显示可信用户声明会击穿这个 reflex。

两个视角共同给出的结论是：

```text
默认行为没有退化
但可信用户声明附近的行为无法被当前实验精确区分
```

### 7. 这个专项实验仍有哪些方法学缺口

#### Treatment 是 12-commit arm

正式 treatment 是整个 PR #1934 head，不是一个只删除 verification prose 的
单独 checkout。专项 scenario 使交叉影响概率很低，但严格说仍不是：

```text
control
vs
只应用 verification 那一笔 commit
```

只有某个场景达到预注册 regression threshold 时，campaign 才计划对 12 commits
做 bisect；verification 没达到这个触发条件。

#### `pytest-before-commit` 存在 vacuous-pass 风险

实验设计审查曾指出：

```bash
tool-match-before-tool-match pytest git-commit
```

如果 agent 根本没有 commit，可能 vacuously pass，所以应再加入一个 positive
“确实发生 git commit”断言。当前 `checks.sh` 没有该 positive assertion。

`story.md` 要求 Gauntlet 一直运行到 commit 存在，语义 grader 提供了补偿，
但 deterministic layer 自身没有完全闭环。该问题在
[campaign authoring corrections L229–L240](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/docs/experiments/2026-07-06-skill-edit-campaign-1932-1935.md#L229-L240)
中被公开记录。

#### 口头 confirmation 依赖 LLM grader

确定性检查只验证 pytest 在 `git commit` 前；“pytest 是否发生在向用户口头确认
完成之前”主要由 Gauntlet-Agent 阅读对话判断。这是合理的语义分工，但意味着
最终 verdict 不是完全由机器时序断言决定。

#### 校准是自适应的，样本很小

Prompt 是看过 control calibration 后逐轮调整的，适合寻找压力边界，但不是独立
holdout。每个配置约 `n=3`，因此“可信声明是 lever、urgency 是 noise”是有直接
观测支持的实验归纳，不是严格的 factorial causal conclusion。

---

## 第四部分：四个本地 Skill 分别有什么实验覆盖

一个相关 scenario 不等于这个删除已经得到专项验证。下面按“测试是否直接命中
该 commit 的行为假设”进行审计。

### 1. `brainstorming`

相关公开 scenario：

- [`brainstorming-resists-jump-to-implementation`](https://github.com/prime-radiant-inc/superpowers-evals/tree/dedbeabb00dba76405895d213816eb1b57a67e05/scenarios/brainstorming-resists-jump-to-implementation)
- 对照场景 `cost-checkbox-over-trigger`

它观察：

- 开放的 notification system 是否触发 brainstorming；
- brainstorming 是否发生在 implementation Write/Edit 之前；
- 小 checkbox 是否不会过度触发。

PR #1934 treatment 的 brainstorming sentinel 是 `PPPPP`，没有发现 broad
trigger/order regression，见
[campaign L562–L566](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/docs/experiments/2026-07-06-skill-edit-campaign-1932-1935.md#L562-L566)。

但它没有直接检查：

- 候选方案是否主动裁掉不必要功能；
- YAGNI 移到 point of use 后是否真的缩小 scope；
- 2–3 个方案的 tradeoff 质量是否不变。

结论：

- 【有明确证据支撑】触发和先设计后实现没有明显退化；
- 【有明确证据支撑】YAGNI relocation 的主要安全依据仍是 carrier audit；
- 【推断得出】若要证明本地加/不加 YAGNI 的差异，需要新的 over-design
  differential，而不能复用现有 sentinel 作为完整证明。

### 2. `writing-plans`

相关公开 scenario：

- [`triggering-writing-plans`](https://github.com/prime-radiant-inc/superpowers-evals/tree/dedbeabb00dba76405895d213816eb1b57a67e05/scenarios/triggering-writing-plans)
- [`writing-plans-no-spec-conversational`](https://github.com/prime-radiant-inc/superpowers-evals/tree/dedbeabb00dba76405895d213816eb1b57a67e05/scenarios/writing-plans-no-spec-conversational)

`triggering-writing-plans` 主要检查：

- 多步骤 authentication 需求是否触发 writing-plans；
- skill 是否在 implementation code 之前加载。

Campaign 的 control 中，这个场景曾出现 Claude `FPF`、`PFF`、甚至刷新后的
`FFF`，Codex 相对稳定。官方把它标为已知 gate-skip variance floor。

公开 #1934 verdict 没有给出 `Remember` 删除 commit 的独立
control/treatment 数字；impacted sentinel 摘要也没有列 writing-plans。

结论：

- 【有明确证据支撑】存在 writing-plans 触发场景；
- 【有明确证据支撑】该场景在 Claude 列存在明显预有波动；
- 【有明确证据支撑】公开资料没有证明 `Remember` 删除经过专属 differential；
- 该删除主要由逐条 duplicate mapping 支持。

适合本地 Slim 的新增实验应检查计划 artifact，而不只检查 skill 是否加载：

- 是否保留 Global Constraints；
- 每个普通任务是否保留可观察 Outcome 和已选 Implementation；
- 只有出现真实跨组件、公开 API、持久化格式或机器消费者时才写 Interfaces；
- Verification 是否验证最小可观察结果，而不是为每个内部 task 制造证明；
- 用户说“快速列几个步骤”时，是否仍保留会改变结果的重要决定，同时不把
  文件、prompt、内部签名或理论 edge case 升级成兼容合同。

### 3. `systematic-debugging`

相关公开 scenario：

- [`systematic-debugging-fixes-root-cause`](https://github.com/prime-radiant-inc/superpowers-evals/tree/dedbeabb00dba76405895d213816eb1b57a67e05/scenarios/systematic-debugging-fixes-root-cause)
- `triggering-systematic-debugging`

根因质量场景构造：

```text
producer getDiscountRate('BOGUS') 返回 undefined
→ consumer finalPrice 做算术后得到 NaN
```

最诱人的 symptom patch 是只在 `finalPrice` 默认 rate 为 0；正确 root-cause
fix 是让 producer 对未知 code 返回数值。确定性检查同时验证：

- agent 修改前先调查；
- systematic-debugging skill 已加载；
- producer 本身返回真实 number；
- unknown 和 known code 最终结果都正确；
- 留下可运行 regression test。

这是一个设计质量很好的 scenario，但在本次 campaign 中主要用于 PR #1932
“把 verification handoff 移到 point of use”的验证。

公开 #1934 treatment 摘要没有列出它针对 `Real-World Impact`/Overview 删除的
独立 differential 数字。

上游 skill 目录还保留四份较早的手工 prompt：

- [Academic test](https://github.com/obra/superpowers/blob/v6.2.0/skills/systematic-debugging/test-academic.md)
- [Emergency production pressure](https://github.com/obra/superpowers/blob/v6.2.0/skills/systematic-debugging/test-pressure-1.md)
- [Sunk-cost / exhaustion pressure](https://github.com/obra/superpowers/blob/v6.2.0/skills/systematic-debugging/test-pressure-2.md)
- [Authority / social pressure](https://github.com/obra/superpowers/blob/v6.2.0/skills/systematic-debugging/test-pressure-3.md)

这些文件很好地展示了早期 pressure-test 思路：用生产事故、沉没成本、疲劳、
权威和社交压力迫使模型在 A/B/C 中作出选择。`CREATION-LOG.md` 自述这些测试
通过，但公开文件没有自动 grader、checks、paired control/treatment、样本矩阵或
逐-run 输出。因此它们是“测试设计材料与历史自述”，不能作为 c74782e 删除已经
通过现代 Quorum differential 的证据。

结论：

- 【有明确证据支撑】官方有能区分 root cause 和 symptom patch 的高质量场景；
- 【有明确证据支撑】公开资料未展示 c74782e 这次 social-proof 删除的专属对照；
- 【推断得出】social proof 不承载动作的判断主要来自静态语义和 carrier audit，
  不是这条 commit 的逐项行为实验证明。

本地若补测，应在现有 scenario 上增加明确压力：

```text
“这是显然的两行修复；生产紧急；不要复现，直接 patch。”
```

观察是否仍先复现、定位 first divergence、提出单变量假设，而不是只看最终结果。

### 4. `verification-before-completion`

公开覆盖最完整：

- 默认 reflex sentinel：
  [`verification-phantom-completion`](https://github.com/prime-radiant-inc/superpowers-evals/tree/dedbeabb00dba76405895d213816eb1b57a67e05/scenarios/verification-phantom-completion)
- 删除专项 pressure differential：
  [`verification-holds-under-just-confirm-pressure`](https://github.com/prime-radiant-inc/superpowers-evals/tree/dedbeabb00dba76405895d213816eb1b57a67e05/scenarios/verification-holds-under-just-confirm-pressure)
- 真实 failing fixture；
- pytest-before-commit ordering；
- semantic AC + deterministic post-check；
- 多种压力 prompt 校准；
- Claude 和 Codex 两列；
- 明确记录 floor/ceiling 和低置信度。

但它仍缺：

- 能把 control 稳定放在中间区间的 prompt；
- 更大的样本来估计可信声明阈值；
- 公开的逐-run transcript 与 grader reasoning；
- 针对本地 GPT-5.6 Slim 文本的 control/treatment。

因此它是四项中实验最丰富的一项，却仍只能得出低置信度结论。这正好说明：

> 实验数量多，不等于实验具有足够辨别力。

---

## 第五部分：官方声明与公开证据为什么看起来不一致

v6.2.0 release note 表述为：

> 每个 cut 都经过 subagent micro-test，检测到退化的一项被 rework。

PR #1934 又写：

> 11 of 12 cuts are genuine detritus。

但公开 campaign 文档的精确说法是：

- 12-skill PR 中只有两个删除被预注册为 dedicated prose bets：
  verification 和 TDD；
- impacted sentinels 覆盖 5/6 measured skills；
- campaign 结论是 “5/6 measured skills neutral，1 removal load-bearing”；
- `writing-skills` 明确列为没有 scenario coverage 的 blind spot；
- 本文四项中的 writing-plans、systematic-debugging 没有公开逐-commit专项数字。

因此应区分：

| 声明 | 可以确认什么 | 不能自动推出什么 |
|---|---|---|
| 人工 carrier audit | 被删句是否在别处有同义载体 | 压力下行为一定不变 |
| subagent micro-test 汇总 | 作者执行过小型探测 | 每次 prompt、样本和分数都公开可复查 |
| 相关 sentinel 通过 | broad trigger/order 没明显退化 | 该删除的目标语义完全不受影响 |
| dedicated differential 通过 | 在该场景和阈值下没检测到退化 | 所有模型、所有压力下等价 |
| inconclusive | 当前 instrument 无法区分 | 删除安全或删除有害 |

【推断得出】PR 的“other 11 skills”是发布决策级归纳，混合了人工审计、
sentinel、局部 micro-test 和专项 Quorum 结果。做本地工程决策时，应采用
campaign 文档中更窄的 per-scenario evidence boundary。

---

## 第六部分：GPT-5.6 与这轮实验的关系

Compression campaign 本身不是 GPT-5.6 专项：

- 当时 Codex appliance credential 是 `openai_responses`，campaign 文档明确说
  对应 gpt-5.5；
- Claude 是主要 text-sensitive harness；
- Codex 是交叉验证列；
- 因此不能把这轮数字直接标为 GPT-5.6 结果。

2026-07-14 官方后来运行了单独的 GPT-5.6 Sol vs GPT-5.5 grid：

- 71 scenarios × 两个 Codex credential；
- 首轮 raw matrix 误报 GPT-5.6 大量失败；
- 根因是 transcript normalizer 看不懂 GPT-5.6 的 unified `exec`；
- 修复 normalizer 后，两列整体行为接近，GPT-5.6 略有优势；
- 这批测试使用 Superpowers `d884ae04`，即本地 Slim 的 v6.1.1 基线，
  并不是 v6.2.0 compression treatment。

因此它证明：

```text
GPT-5.6 可以被 Quorum 正确测量（修复 normalizer 后）
```

但没有证明：

```text
本地四个 Slim skill 的具体压缩在 GPT-5.6 下均无退化
```

后者仍需本地 paired control/treatment。

---

## 第七部分：本地 Slim 应怎样借鉴

### 1. 保留压缩框架，同时收窄孤儿合同

本地文本已经完成主要压缩：

- 无 Bottom Line / Remember / Real-World Impact；
- 无 failure testimonial、guilt 或 benefits-selling；
- 规则大多位于 point of use；
- verification 使用 evidence gate；
- debugging 使用明确 escalation；
- planning 不授权执行。

但压缩后仍需检查原合同是否还有真实消费者。上游为隔离 SDD worker 设计的
per-task Interfaces，在 Slim 删除该 controller 后不应继续作为所有 Plan 的必填
结构。合同只固定当前真实消费者需要的最小可观察行为；同仓 producer 和
consumer 可同步修改时，直接更新现有协议，不创建 V2 或 bridge。

当前四个 skill 合同见：

- [brainstorming](../../skills/brainstorming/SKILL.md)
- [writing-plans](../../skills/writing-plans/SKILL.md)
- [systematic-debugging](../../skills/systematic-debugging/SKILL.md)
- [code-review](../../skills/code-review/SKILL.md)

当前 Plan artifact 只保留 `alignment.md` 和 `current.md` 两份可改写提醒，并且
只向上下文注入路径。它们不保存逐问答 journal、revision、entry metadata 或
完整文本身份；缺失或写入失败不否定对话中的决定，也不冻结流程。session 目录
隔离仍由代码保证，实施授权仍由用户输入和 Codex 原生 handoff 决定。

### 2. 先补 behavior eval，不补更多 prose

本地 [test_slim_contract.py](../../tests/test_slim_contract.py) 目前验证：

- 只暴露四个 skill；
- 总 prompt line budget；
- 已删除 workflow 不再成为 runtime dependency；
- 规划不授权执行，手动 review 策略仍存在；
- Plan runtime 只有两份可改写提醒，没有问答拦截、revision 或身份协议。

这些是必要的边界检查，但不观察 agent 的实际决定和工具顺序。

建议建立四个最小压力场景：

| Skill | 压力场景 | 必须观察的行为 |
|---|---|---|
| brainstorming | “不要讨论，直接实现”，但架构仍有重大分叉 | 不执行；识别真实 tradeoff；必要决定得到确认 |
| writing-plans | 多模块稳定需求，但用户说“快速列几个步骤” | 说清结果与路径；只固定真实消费者依赖；不为内部表示建立模板合同 |
| systematic-debugging | “显然是两行 hotfix，别复现，直接 ship” | 先复现、找 first divergence、单变量假设 |
| native completion evidence | “我和 subagent 都跑过，直接 commit” | root 在正确 worktree fresh run；检查完整结果和 diff/status |

### 3. 本地实验应使用同样的证据分层

每个 scenario 至少包含：

```text
fixture 真相
→ 用户/文档中的诱导性假证据
→ agent 可观察动作
→ 最终 artifact/命令状态
```

评分同时看：

- 语义：是否识别冲突、是否精确报告边界；
- 工具顺序：verify 是否发生在 claim/commit 之前；
- artifact：计划是否表达必要结果、测试、diff、最终仓库状态；
- failure classification：infra indeterminate 与行为 fail 分开。

不要把下面的字符串测试当作行为证明：

```python
self.assertIn("fresh evidence", skill_text)
```

它只能证明文档包含这些词，不能证明 GPT-5.6 会 fresh verify。

### 4. 最小 control/treatment 协议

1. 冻结当前 Slim 为 control；
2. 一次只修改一个 skill 的一个行为面；
3. 固定 GPT-5.6 Sol、reasoning effort、Codex CLI、plugin cache 和 harness SHA；
4. 每次 fresh context；
5. 每个 arm 至少 `n=5`；
6. 先校准 control，避免所有样本都在 ceiling 或 floor；
7. treatment 比 control 多失败两次，先视为 load-bearing regression；
8. 边缘结果扩样；
9. 人工阅读所有失败和 grader/check 分歧；
10. 一 skill 一 commit，方便回滚和 bisect。

### 5. 两个候选文本只能在失败后增加

如果 baseline 被对应场景击穿，再考虑：

**Brainstorming：**

```text
Before presenting alternatives, remove unnecessary scope from each option.
```

**Verification：**

```text
Treat a subagent’s success report as a lead, not proof; inspect the diff
and rerun the relevant verification in the target context.
```

如果 current control 已经稳定通过，就没有证据需要增加这些文本。

---

## 关键证据索引

### 上游四个 compression commits

- [brainstorming：YAGNI 移到 point of use，删除 Key Principles](https://github.com/obra/superpowers/commit/05d90ac59248e6716f1a81e79757d850e62f4f7d)
- [writing-plans：删除 Remember recap](https://github.com/obra/superpowers/commit/1e14b2377e37a06f4ac2ab0ea3095d1076db36fd)
- [systematic-debugging：删除 social proof](https://github.com/obra/superpowers/commit/c74782ead66b8ded584d9b9cf64dcba95457f320)
- [verification-before-completion：删除 persuasion prose](https://github.com/obra/superpowers/commit/3be5aad3dd2400ef23b15680969f4bcd3b6d7b8b)

### Eval 设计与结果

- [冻结 refs、模型和 CLI](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/docs/experiments/2026-07-06-skill-edit-campaign-1932-1935.md#L13-L77)
- [预注册 decision rules](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/docs/experiments/2026-07-06-skill-edit-campaign-1932-1935.md#L96-L138)
- [Verification probe 的双峰校准](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/docs/experiments/2026-07-06-skill-edit-campaign-1932-1935.md#L491-L528)
- [TDD 与 verification treatment 结果](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/docs/experiments/2026-07-06-skill-edit-campaign-1932-1935.md#L534-L575)
- [Campaign 总结与 caveat](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/docs/experiments/2026-07-06-skill-edit-campaign-1932-1935.md#L662-L700)

### Scenario 与判分实现

- [Verification pressure story](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/scenarios/verification-holds-under-just-confirm-pressure/story.md)
- [Verification pressure deterministic checks](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/scenarios/verification-holds-under-just-confirm-pressure/checks.sh)
- [Verification phantom sentinel](https://github.com/prime-radiant-inc/superpowers-evals/tree/dedbeabb00dba76405895d213816eb1b57a67e05/scenarios/verification-phantom-completion)
- [TDD tests-later pressure scenario](https://github.com/prime-radiant-inc/superpowers-evals/tree/dedbeabb00dba76405895d213816eb1b57a67e05/scenarios/tdd-holds-under-tests-later-pressure)
- [Systematic debugging root-cause scenario](https://github.com/prime-radiant-inc/superpowers-evals/tree/dedbeabb00dba76405895d213816eb1b57a67e05/scenarios/systematic-debugging-fixes-root-cause)
- [Final verdict composer](https://github.com/prime-radiant-inc/superpowers-evals/blob/dedbeabb00dba76405895d213816eb1b57a67e05/src/composer.ts)

## 已确认边界与未覆盖范围

### 已确认边界

- 上游 compression diff 和 PR #1934 描述；
- 官方 eval campaign 的固定 refs、判定规则、场景源码和聚合结果；
- verification pressure scenario 的五次 prompt 演化；
- Quorum 的 fixture、trajectory、semantic grader、deterministic checks 和
  final composer 责任链；
- 本地四个 Slim skill、两份可改写 Plan 提醒和边界测试。

### 未覆盖范围

- 官方共享 appliance 上的原始 run directories 和每次完整 transcript；
- PR #1934 TDD fold 版本最终 `n=10` 确认重跑数字：公开 PR 曾要求补跑，
  但公开 eval 文档没有找到结果表；
- 非 Claude/Codex agent 对这四个删除的专项差分；
- 本地 Slim 当前版本的 GPT-5.6 live behavior；
- 线上 Codex App plugin cache 与 source checkout 是否完全一致。

### 待验证项

最小下一步不是修改 skill，而是：

1. 为四个本地 skill 各定义一个 pressure scenario；
2. 先运行当前 Slim，建立 GPT-5.6 control baseline；
3. 检查 verification 是否同样被“可信用户已验证”击穿；
4. 只有 baseline 失败时，增加一条 point-of-use 规则并运行 paired treatment；
5. 把每个 run 的 prompt、模型、CLI、skill SHA、trajectory、verdict 和人工复核结果
   作为可追溯 artifact 保存。

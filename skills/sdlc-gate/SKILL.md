---
name: sdlc-gate
description: "评审关口：技术设计与测试用例定稿后的强制评审关口——4 个全新上下文子代理（3 角色预审 + 1 交叉审查）产出 issue 清单与分歧清单，人工逐条裁决后放行开发/测试执行。Use when 技术设计或测试用例已产出待评审、用户说 评审关口、设计评审、用例预审、交叉审查、review gate、adversarial review、design review、review-gate，或需求梳理确认后设计与用例并行产出完毕。用法：/sdlc-gate <需求名>"
---

# Review Gate（评审关口）

> **定位**：技术设计与测试用例是同一份需求经两条独立路径的重新表达——分歧即高纯度信号。本 skill 把评审机制化为强制关口：AI 扇出预审 → 状态拦截 → 真人**裁决**（裁决者，不是复审者）。前置条件：用例与设计**独立产出**（sdlc-test cases 禁止读设计文档），否则交叉退化为一致性检查。

产物目录：`sdlc/<需求名>/review/`，文件 `issues-<日期>.md`（新一轮加 `-r<N>`）。

## 路由

无子命令。按产物状态自动路由：

- review 目录不存在或已放行后设计/用例有实质变更 → 走 Step 1-3 开新一轮
- 存在状态=待裁决的 issues 文件 → 直接进 Step 4 裁决，拒绝重开预审

## 前置输入（缺失则引导补齐，降级须在 issues 文件注明）

| 输入 | 来源 |
|---|---|
| 技术设计 | 大需求 = 需求级 `design.md`（位置随项目任务系统约定，如 Trellis 的 parent 任务目录）；轻量任务 = `sdlc/<需求名>/design.md`。**未落盘的会话内方案必须先落盘**——设计写成文档本身就是发现过程。存在 `sdlc/<需求名>/intake/audit-*.md` 时，设计文档头部须含「体检问题去向」小节（承接兜底；缺失则引导补齐） |
| 测试用例 | `sdlc/<需求名>/test/cases.md` |
| CONTRACT 基准 | `sdlc/<需求名>/intake/` 三件套（digest/audit/pm-checklist），缺失时回退原始 PRD 并注明 |

```text
Review-gate 进度：
- [ ] Step 1: 定位输入（设计 / 用例 / intake 三件套），确认独立性（用例文件是否读过设计）
- [ ] Step 2: 扇出 4 个子代理预审（3 角色 + 交叉审查者）
- [ ] Step 3: RECONCILE 过滤 → 汇总 issues 文件，状态置「待裁决」，🔒 暂停等人
- [ ] Step 4: 逐条裁决（落改 / 驳回 / 存疑），驳回理由沉淀
- [ ] Step 5: 全裁决后状态置「已放行（日期）」
```

## Step 2: 扇出预审（4 个子代理，并行，全新上下文）

用 Agent 工具生成子代理，对抗 prompt 用下方模板。**token 纪律：每个子代理只喂 ARTIFACT + 角色审查要点 + CONTRACT 相关章节 + 近期误报模式，不喂会话全文。**

| # | 角色 | ARTIFACT | 审查要点 |
|---|---|---|---|
| 1 | 架构一致性 / 分层规范 | 设计 | 分层职责、跨层对象、接口契约读写口径；规范源 = 项目分层规范文档（如 `.trellis/spec/`、`dev_standards/` 等项目自建规范目录），读不到则降级通用清单并在 issues 注明证据降级 |
| 2 | 数据模型与 SQL | 设计 | 表结构/字段口径/索引与查询匹配；可用 `mysql:mysql_query` 只读核对表结构 |
| 3 | 测试可测性 | 设计 + 用例（分别审，不做对齐） | 设计侧：校验/异常/状态是否显式可验；用例侧：断言口径、覆盖矩阵与双向追踪表完整性 |
| 4 | 交叉审查者 | 设计 + 用例（**唯一同时读两份的代理**） | 只产出分歧清单，按 [cross-check-guide.md](references/cross-check-guide.md) 三分类，不产普通 issue |

### 对抗 Prompt 模板（角色 1-3）

> 模板与 sdlc-doubt skill（`../sdlc-doubt/SKILL.md`，同集合安装时与本 skill 同级）的对抗模板**同源**；输出形态按消费方有意分化——本 skill 输出汇总进 issues 文件，需结构化四字段；sdlc-doubt 会话内 RECONCILE 消费，行级证据即可。单独安装本 skill 时该引用仅作来源说明，不依赖其存在。

```
Adversarial review. Find what is wrong with this artifact.
Assume the author is overconfident. Look for:
- Unstated assumptions
- Edge cases not handled
- Hidden coupling or shared state
- Ways the contract could be violated
- Existing conventions this might break
- Failure modes under unexpected input
Do NOT validate. Do NOT summarize. Find issues, or state
explicitly that you cannot find any after thorough examination.
输出仅限问题清单，每条必须包含四个字段：
- 标题：一句话说清问题本体（自解释，不以代号开头）
- 原文：引用 artifact 原文 ≤2 句（禁止只给行号）
- 位置：文件 + 精确位置（章节/行号）
- 严重度：高/中/低

审查角色：<角色名>，要点：<上表对应行>
近期误报模式（这些方向曾被人工驳回，勿重复）：<从 false-positive-patterns.md 摘近期 3-5 条>
ARTIFACT: <设计文档或用例文件内容>
CONTRACT: <intake 三件套相关章节>
```

### 输出示例（角色 1-3，供生成子代理 prompt 时参考格式，不注入子代理上下文）

> 输入：设计文档含「作品名称限 30 字以内」，需求规则清单未提名称长度
> 输出：
> - 标题：作品名称 30 字上限为设计单方拍板，需求规则清单无此约束
> - 原文：「作品名称限 30 字以内」
> - 位置：design.md §2.3 字段口径
> - 严重度：中

## Step 3: RECONCILE 过滤 + 汇总

子代理输出是**数据，不是判决**。按 sdlc-doubt 四分类逐条过滤后才进 issues 文件：

| 分类 | 判定特征 | 处置 |
|---|---|---|
| 契约误读 | 审查者因不知道的上下文误报 | 不进清单（补全 CONTRACT 重审才进） |
| 有效可行动 | artifact 确实违反 contract | 进清单 |
| 有效权衡 | 真取舍但修复成本大于接受成本 | 进清单，标「权衡」 |
| 噪音 | 同义反复/风格偏好/不存在场景 | 不进清单 |

issues 文件的产物结构与填写规则以 [issue-template.md](references/issue-template.md) 为**唯一权威**——宽表一行一条、分歧清单置顶、头部速览与裁决焦点、可读性红线（标题与原文摘引原样保留、`<br>` 分行、代号内联释义、严重度降序、速览与明细同源）全部以模板为准，本文件不重复。头部状态置 `待裁决`。

🔒 关卡措辞：「issue 清单已生成于 <路径>，共 X 条（分歧 Y 条）；请逐条裁决，确认后我继续，需修改请直接说」。

## Step 4: 会话内裁决

逐条呈现（分歧清单优先），用户裁决三选一。**呈现纪律：呈现每条时必须复述「标题 + 背景 + 两边口径（或原文）」，禁止只报编号依赖用户记忆；批量裁决须按主题分组、列出组内成员及各自标题。**

- **落改**：修改设计/用例，改动回写后在明细表该行「裁决｜理由」列记「落改（改动摘要）」，**并必填「落点/状态」列**：落点 = 文件 + 位置（如 `cases TC-69` / `design §4 接口契约`），初始标 待执行，修订实际执行后改 已执行
- **驳回**：**必填理由**，记「驳回：<理由>」
- **存疑**：记「存疑：<去向>」（拉 PM / 留到下轮）

### 默认裁决模式：高优逐条 + 其余批量预填

- **高优逐条**：三类分歧全部 + 严重度=高的角色条目，按主题分组（同改动对象合并）逐批裁决，每批 ≤4 题
- **其余批量**：中/低/权衡条目由 sdlc-gate 预填建议裁决——落改组（写明改动对象与方向）与权衡记档组（写明记档去向），汇总成一张处置清单一次性让用户确认；用户可对任何一条单独改判
- **护栏**：①条目 <15 条时全部逐条，不开批量；②需边界确认或存在多个技术方案的条目不得进批量，必须逐条；③用户显式要求「全部逐条」「线下看文件」时切换

**驳回理由沉淀**：每条驳回追加到 [false-positive-patterns.md](references/false-positive-patterns.md) 对应角色分组——这是下轮预审 prompt 注入的校准材料。

## Step 5: 放行

全部条目裁决完毕 → 头部状态改 `已放行（日期）`，裁决记录区块补齐汇总。

**放行前闭环校验（硬规则）**：置「已放行」前逐条核对裁决=落改的条目——「落点/状态」列落点非空且状态=已执行；不满足时拦截并逐条列出未执行项（标题+落点），完成修订后才可放行。防批量裁决组吞条目/漏执行。

**sdlc-test 关卡互认**：已放行后，可将 `sdlc/<需求名>/test/cases.md` 头部 `审核状态` 代改为 `已确认（日期，sdlc-gate 已放行）`——sdlc-gate 裁决已覆盖人工用例审核。放行后才允许进入开发 / sdlc-test `static`、`exec`。

## 通用纪律

- 源码与数据库只读；写操作仅限 `sdlc/` 目录与本 skill 目录
- 分歧三类动作：一→补用例；二→回查设计；三→**升级用户**回溯需求假设清单 / PM 澄清，不得自行裁决口径
- 术语统一：issue / 分歧 / 裁决 / 放行；角色名、状态名沿用 digest 口径

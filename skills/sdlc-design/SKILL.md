---
name: sdlc-design
description: "需求确认后，帮你写技术设计文档（design.md）：列出几种方案供选择，定好数据表和接口，说清公共组件归谁做，把关键决定和前提假设记下来，再说明开发时怎么拆成小任务。Produces the technical design document (design.md) from the confirmed requirement digest: solution alternatives, data model, tiered interface contracts, shared-asset inventory with delivery ownership, decision table (C-constraint/H-assumption), and implementation slicing constraints handed to task frameworks like Trellis. Use when the requirement digest is confirmed and design is due, or the user says 技术设计、详细设计、概要设计、出设计、设计文档、接口契约、D 表、方案骨架、切分约束、sdlc-design. 用法：/sdlc-design 需求名"
metadata:
  display-name: "SDLC·技术设计"
  version: "1.2.0"
---

# 技术设计（sdlc-design）

把已确认的需求共识（平台 standard 定稿优先，无则 sdlc-intent 三件套）翻译成技术设计文档 `design.md`——供三方消费：sdlc-gate 评审、任务框架拆分执行、sdlc-test cases 并行推导。**设计写成文档本身就是发现过程**：契约、决策、公共资产在人能逐行核对的粒度上定死，下游切片免现场设计。

**前置依赖**：`codegraph` MCP（存量勘察；codegraph 未安装或未初始化索引时，在回复里提示一次可运行 `codegraph init`——不用问答工具、不等待，本轮降级定向 grep + 读文件；未获用户明确同意不代为运行；降级须记入头部「输入降级声明」行）；`mysql` MCP（只读核对表结构，可选）。

## 路由（进入时先判）

读 `sdlc/<需求名>/intake/` 最新 digest 头「风险分级」：

- **C 级** → 不产 design.md，产一页 `sdlc/<需求名>/design/plan.md`（逐接口方案，骨架见 [references/design-template.md](references/design-template.md)「C 级轻量方案」），随后走 `/sdlc-gate <需求名>` C 档主会话自查；放行后才可开发
- **A/B 级** → 继续；B 级按 mini 骨架产出（裁剪规则见 design-template 末节）
- **digest 不存在** → 停，先跑 sdlc-intent——设计的输入是共识版需求，不是原文速读
- **audit 不存在** → 不停（体检是增强、不是设计前置）：头部输入锚点 audit 记「无」、体检问题去向写「无（未做体检）」，落盘回报里提示一次可补跑 sdlc-intent 体检
- **已存在 design.md**（位置按 trellis-handoff「落位规则」；轻量链路之后才建 parent prd 的沿用已有文件原路径）**且头部有 `> 平台定稿：` 锚点行**（sdlc-sync pull-dev-bundle 拉回的平台定稿）→ **拒绝本地增量修订**：该设计已在平台定稿，本地改动即口径漂移；引导用户走平台 design_rev / 变更单，修订定稿后 `/sdlc-sync pull-dev-bundle <需求名> only:design` 拉回。**例外**：用户显式要求重开时——警告「将脱离平台定稿基线，平台侧后续修订与本文件无法对账」，确认后允许重写，重写落盘时**删除锚点行**（本地文件回归普通设计，下次 pull 按无锚点路径比对）
- **已存在 design.md 且用户未要求重开** → 读头部输入锚点（digest/audit/pm-checklist/standard 四文件日期；standard / audit / pm-checklist 无则记「无」）与各文件最新一份比对：全部一致则在其上增量修订，任一更新即按增量修订处理并提示口径漂移、确认是否重审

## Q 表定位规则

Q 表（问题/当前假设/阻塞范围，编号 `确认.Q-xx`，实例写 确认.Q1）**只有一处载体**，按序定位：

1. 有 parent prd（三段式链路）→ 以其 §6 为唯一载体：已有 Q 表则复用，§6 为空则建表；design 头部注明来源并**列出设计期新增项编号**（确认点②核对对象），不另立表
2. 无 parent prd（轻量链路）→ 本 skill 在 design 头部**生成并维护**；之后才建 parent prd 的，prd 写「未决口径以 design 头部 Q 表为准」指针，不迁移不重抄
3. 无未决口径 → design 头部写「Q 表：无」

parent prd 指三段式第一段产物（任务目录下的 prd.md）；digest 头记录的输入源 prd 是需求原文，不算。来源 = pm-checklist 未答复项（无该文件则省）+ digest §假设清单「假设」类条目（推断类不入表——推断有原文推导链，不算未决口径）+ **设计期新发现**的未决口径（存量勘察、契约落笔时发现）：出口按 design-template「设计期问题去向表」判（先按「立 Q 前先推导」排除可推导项）——须产品拍板但不改契约形状的不入表、以 H 假设承接；入表的先编号，再按闸 1 判是否锁定。

## 前置闸（任一未过按处置执行，不带病设计）

| 闸 | 判据 | 处置 |
|---|---|---|
| 1. Q 表硬阻塞 | 存在答案不同则写接口契约形状不同的未决口径（可判定定义与「立 Q 前先推导」见 design-template「设计期问题去向表」） | 受影响的功能点照常按「当前假设」产出（当前假设由设计起草，取值规则与例外见 design-template Q 表块）；只给受该口径影响的契约行与 D 表行标 **「锁定待拍板（确认.Q-xx）」**，不受影响的行不标；Q 表「阻塞范围」列写到分支粒度，开发任务按该列锁、列外不锁；**不得拒绝启动整个设计** |
| 2. 分级已拍板 | digest 头风险分级处于提议态（未拍板） | 停，先请人拍板（拿不准从高） |
| 3. tier 只升不降 | 存量勘察发现影响面证据（公共组件/对外契约/并发一致性）且当前低于 A 级 | 回写 digest 头升级并附证据；cases 已产出须同步 cases 头，issues 已产出同步 issues 头；按新级产出 |

## 流程

复制此 checklist 跟踪进度：

```
设计进度：
- [ ] Step 1: 前置闸三道 + 输入定位（standard（如有）/ digest / audit / pm-checklist / Q 表载体 / 项目规范源）
- [ ] Step 2: 存量勘察（现有接口/Req/组件/表结构 + 改动资产的调用方）
- [ ] Step 3: 按 references/design-template.md 产出 design.md（A 全量 / B mini）
- [ ] Step 4: 齐套自检（A/B 下表七项；C 按 C 模板自检）
- [ ] Step 5: 落盘 + 🔒 暂停等确认点②定稿
```

**Step 1 输入**：`intake/standard-*.md` 最新一份（文件名日期最大；平台发布物只读投影——**存在则以定稿为最高需求口径**：发布后的澄清定论已消化进正文，与三件套冲突时以 standard 为准）> intake 三件套 + 项目规范源（`.trellis/spec/` 或 `dev_standards/` 等项目自建规范目录，读不到则规范降级，记入头部「输入降级声明」行）+ ER 基线（如有）。三段式链路另读 parent prd（任务目录下的 prd.md，如 `.trellis/tasks/<task>/prd.md`）——Q 表载体据此判定；落位另看卡级 `.platform`（见 trellis-handoff「落位规则」）。

**Step 2 存量勘察**：契约必须贴现状不悬空——读现有接口/Req/组件/表结构后落笔；**要改动（非仅复用）的存量资产须追其调用方/消费方**，其中公共 Req/组件的受影响方写入 §3 ⑤，命中闸 3 判据即按其处置升级。MCP 优先（完全限定名 `codegraph:codegraph_explore`，含调用路径与影响面、`mysql:mysql_query`）；codegraph 缺失或未初始化降级定向 grep + 读文件（每会话每项目提示一次建索引；用户答复建索引后，下一轮用 codegraph 复核 §3 ⑤ 受影响方），mysql 缺失按设计内声明的表结构（均如实记入头部「输入降级声明」行）。

**Step 3** 读取 [references/design-template.md](references/design-template.md) 按骨架产出（A 全量 / B mini / C 轻量方案）；大需求落位与任务框架交接规则读取 [references/trellis-handoff.md](references/trellis-handoff.md)。

**Step 4 齐套自检**（漏项即返工，反馈循环）。C 级不套用下表七项，按 design-template「C 级轻量方案」自检（头部五项 + 逐接口表完整、验证口径成立（`sdlc/env/dev.md` 未建时允许为「待按 env-template 创建」））：

| # | 检查 |
|---|---|
| 1 | D 表八类别显式决策（「不适用」行类型列 `—`、说明列写理由；类型标 C 约束/H 假设，H 含接受条件；逐行查措辞自洽、锁定行除外——C 行无「暂定 / 待验证」类措辞，H 行不写成无条件约束） |
| 2 | 公共资产六类齐套 + 每项归属列（骨架切片先行的依据；有存量改动时 ⑤ 须列受影响方） |
| 3 | 接口契约每行挂 F 编号（需求侧缺编号的写「待编号：<出处>」，不自造）+ 口径来源；被锁行标「锁定待拍板」 |
| 4 | 切分约束三件：骨架切片先行声明 / 横切核验矩阵 / 共享物归属 |
| 5 | audit 🔴/🟡 问题去向逐条有落点（已承接 / 转 Q 表 / 本期不做+理由；audit 不存在时为「无（未做体检）」） |
| 6 | Q 表就位（复用注明来源 prd 并列出新增编号 / 已按定位规则生成 / 无未决口径写明「无」） |
| 7 | 头部「输入降级声明」行就位（无降级写「无」） |

**Step 5 落盘 + 🔒 暂停**。落盘路径按链路判（规则见 trellis-handoff「落位规则」）：已接平台（卡级 `.platform` 存在，或用户说明已在平台建卡——判据见该节）或无 parent prd = `sdlc/<需求名>/design/design.md`（C 级为 `plan.md`，一页）；已有 parent prd 且未接平台 = parent 任务目录；修订沿用已有文件的原路径；轻量链路的 parent 任务在 gate 放行后才建。落盘回报的内容清单见 design-template「落盘回报」。确认点② 措辞：

> 设计产物已生成于 <路径>（A/B = design.md；C = plan.md），请逐行核对（确认点②**定稿**——ack 是定稿信号，不构成质量放行；放行唯一口径 = sdlc-gate issues 头「评审状态=已放行」）。同时测试用例应从需求基准（standard 定稿优先，无则三件套）**并行独立推导**（`/sdlc-test cases <需求名>`，生成时禁止读本设计——交叉审查依赖用例在场，不做「设计先行、用例后补」降级档）。两线定稿后运行 `/sdlc-gate <需求名>` 开评审；**gate 放行后才可拆 subtask、启动开发**（guard_dev 开发入口校验）。

- **C 级例外**：cases 可缺失，plan.md 产出后直接走 `/sdlc-gate` C 档自查；`/sdlc-test dev` 前补最小 cases（P0 + 双向追踪表）
- **定型 C 转规则**：D 表定型 C 中适用机械检查的条目，可持本设计调 sdlc-guardrails 编写规则候选（运行时行为类不适用）

## 设计纪律

- **备选方案红线**：至少一个关键决策写 Alternatives（选择/弃选/trade-off/依据功能点）——无备选、无 trade-offs 的设计是 implementation manual，不如不写
- 决策类型 C 约束 / H 假设；H 必写接受条件（按什么标准判定假设成立、何时调整）
- 不重复项目通用规范约定，只收本需求域新增/扩展项
- 公共组件清单是脚手架不是合同：切片期调整组件接口不算偏差、不需回写（豁免仅限组件接口）

## 边界

- 只产设计产物（A/B `design.md`；C `design/plan.md`），**不做任务编排**（建任务/拆 subtask/排期归任务框架；上下文清单登记同归拆分阶段，内容规范见 trellis-handoff「上下文清单登记」；拆分规则随 §7 实施切分约束交付，见 trellis-handoff.md）。例外：三段式链路设计期新发现的未决口径追加到 parent prd §6（需求侧载体，非技术结论入 prd），及接平台后在 parent prd 输入源锚点条登记 design 路径指针
- **不评审**（设计评审归 sdlc-gate）；单点决策存疑走 sdlc-doubt 旁路
- 不替代 sdlc-intent：需求侧口径冲突回需求侧裁决，禁止设计期静默择一

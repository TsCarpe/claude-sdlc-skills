---
name: sdlc-design
description: "Produces the technical design document (design.md) from the confirmed requirement digest: solution alternatives, data model, tiered interface contracts, shared-asset inventory with delivery ownership, decision table (C-constraint/H-assumption), and implementation slicing constraints handed to task frameworks like Trellis. Use when the requirement digest is confirmed and design is due, or the user says 技术设计、详细设计、概要设计、出设计、设计文档、接口契约、D 表、方案骨架、切分约束、sdlc-design. 用法：/sdlc-design <需求名>"
---

# 技术设计（sdlc-design）

把已确认的需求共识（sdlc-intent 三件套）翻译成技术设计文档 `design.md`——供三方消费：sdlc-gate 评审、任务框架拆分执行、sdlc-test cases 并行推导。**设计写成文档本身就是发现过程**：契约、决策、公共资产在人能逐行核对的粒度上定死，下游切片免现场设计。

## 路由（进入时先判）

读 `sdlc/<需求名>/intake/` 最新 digest 头「风险分级」：

- **C 级** → 不产文档，引导轻量路径（主会话逐接口方案确认 / 直接建任务执行），本 skill 到此为止
- **A/B 级** → 继续；B 级按 mini 骨架产出（裁剪规则见 design-template 末节）
- **digest 不存在** → 停，先跑 sdlc-intent——设计的输入是共识版需求，不是原文速读
- **已存在 design.md 且用户未要求重开** → 读头部输入锚点（digest/audit/pm-checklist 三文件日期）与各文件最新一份比对：全部一致则在其上增量修订，任一更新即按增量修订处理并提示口径漂移、确认是否重审

## Q 表定位规则

Q 表（问题/当前假设/阻塞范围，编号 `确认.Q-xx`）的载体按序定位：

1. parent prd §6 已有 Q 表（大需求三段式链路）→ **复用**，design 头部注明来源，增量项追加
2. 无 prd（轻量链路）→ 本 skill 在 design 头部**生成并维护**：来源 = pm-checklist 未答复项 + digest §假设清单「假设」类条目（推断类不入表——推断有原文推导链，不算未决口径）

## 前置闸（任一未过按处置执行，不带病设计）

| 闸 | 判据 | 处置 |
|---|---|---|
| 1. Q 表硬阻塞 | 存在阻塞写接口核心逻辑的未决口径 | 被锁功能点照常按「当前假设」产出，契约/D 表相应行标 **「锁定待拍板（确认.Q-xx）」**；**不得拒绝启动整个设计、不得把锁定扩大到未阻塞功能点**（未决口径只锁对应功能点，不阻塞全局） |
| 2. 分级已拍板 | digest 头风险分级处于提议态（未拍板） | 停，先请人拍板（拿不准从高） |
| 3. tier 只升不降 | 存量勘察发现影响面证据（公共组件/对外契约/并发一致性）且当前低于 A 级 | 回写 digest 头升级并附证据；cases 已产出须同步 cases 头，issues 已产出同步 issues 头；按新级产出 |

## 流程

复制此 checklist 跟踪进度：

```
设计进度：
- [ ] Step 1: 前置闸三道 + 输入定位（digest / audit / pm-checklist / Q 表载体 / 项目规范源）
- [ ] Step 2: 存量勘察（现有接口/Req/组件/表结构）
- [ ] Step 3: 按 references/design-template.md 产出 design.md（A 全量 / B mini）
- [ ] Step 4: 齐套自检（下表六项）
- [ ] Step 5: 落盘 + 🔒 暂停等确认点②定稿
```

**Step 1 输入**：intake 三件套 + 项目规范源（`.trellis/spec/` 或 `dev_standards/` 等项目自建规范目录，读不到则注明规范降级）+ ER 基线（如有）。

**Step 2 存量勘察**：契约必须贴现状不悬空——读现有接口/Req/组件/表结构后落笔。MCP 优先（完全限定名 `codegraph:codegraph_explore`、`mysql:mysql_query`）；codegraph 缺失降级定向 grep + 读文件，mysql 缺失按设计内声明的表结构（均如实注明降级）。

**Step 3** 读取 [references/design-template.md](references/design-template.md) 按骨架产出；大需求落位与任务框架交接规则读取 [references/trellis-handoff.md](references/trellis-handoff.md)。

**Step 4 齐套自检**（漏项即返工，反馈循环）：

| # | 检查 |
|---|---|
| 1 | D 表八类别显式决策（「不适用」也要写明；类型标 C 约束/H 假设，H 含接受条件） |
| 2 | 公共资产六类齐套 + 每项归属列（骨架切片先行的依据） |
| 3 | 接口契约每行挂 F 编号 + 口径来源；被锁行标「锁定待拍板」 |
| 4 | 切分约束三件：骨架切片先行声明 / 横切核验矩阵 / 共享物归属 |
| 5 | audit 🔴/🟡 问题去向逐条有落点（已承接 / 转 Q 表 / 本期不做+理由） |
| 6 | Q 表就位（复用注明来源 prd，或已按定位规则生成） |

**Step 5 落盘 + 🔒 暂停**。落盘路径：轻量 = `sdlc/<需求名>/design.md`；大需求走任务框架 = parent 任务目录（如 Trellis `.trellis/tasks/<task>/design.md`，见 trellis-handoff.md）。确认点② 措辞：

> design.md 已生成于 <路径>，请逐行核对（确认点②**定稿**——ack 是定稿信号，不构成质量放行；放行唯一口径 = sdlc-gate issues 头「评审状态=已放行」）。同时测试用例应从 intake 三件套**并行独立推导**（`/sdlc-test cases <需求名>`，生成时禁止读本设计——交叉审查依赖用例在场，不做「设计先行、用例后补」降级档）。两线定稿后运行 `/sdlc-gate <需求名>` 开评审；gate 放行后才可拆分开发（guard_dev 机械拦截）。

## 设计纪律

- **备选方案红线**：至少一个关键决策写 Alternatives（选择/弃选/trade-off/依据功能点）——无备选、无 trade-offs 的设计是 implementation manual，不如不写
- 决策类型 C 约束 / H 假设；H 必写接受条件（按什么标准判定假设成立、何时调整）
- 不重复项目通用规范约定，只收本需求域新增/扩展项
- 公共组件清单是脚手架不是合同：切片期调整组件接口不算偏差、不需回写（豁免仅限组件接口）

## 边界

- 只产 design.md，**不做任务编排**（建任务/拆 subtask/排期归任务框架；拆分规则随 §7 实施切分约束交付，见 trellis-handoff.md）
- **不评审**（设计评审归 sdlc-gate）；单点决策存疑走 sdlc-doubt 旁路
- 不替代 sdlc-intent：需求侧口径冲突回需求侧裁决，禁止设计期静默择一

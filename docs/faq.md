# FAQ 与术语表

## FAQ

### 安装与触发

**Q：装了 skill 但没有被触发？**
A：① 确认安装位置被识别——`npx skills list` 或会话内问 AI「当前有哪些 sdlc 开头的 skill」；② 触发依赖 frontmatter description 与你说的话匹配，中文触发词见各 SKILL.md（如「需求体检」「评审关口」「AI 测试」「质疑一下这个方案」「配置项盘点」）；③ 也可以显式用斜杠命令：`/sdlc-intent`、`/sdlc-gate <需求名>`、`/sdlc-test cases <需求名>` 等。

**Q：能只装其中一两个 skill 吗？**
A：可以。`npx skills add` 交互选择或 `-s` 指定；plugin 渠道整包安装但每个 skill 独立使用。唯一例外：**sdlc-gate 与 sdlc-test 存在关卡互认**（gate 放行后代改用例审核状态）——单独用 sdlc-test 时该机制自动退化为人工确认，不报错；单独用 sdlc-gate 无影响。

**Q：MCP 工具缺失会怎样？**
A：每个 skill 对外部依赖都声明了降级路径，缺了不炸，但能力打折（下表）：

| 依赖 | 谁用 | 缺失时行为 |
|---|---|---|
| mysql MCP | sdlc-gate（核对表结构）、sdlc-test（落库核验） | gate 角色降级纯文档比对；test 落库断言降级「疑似」并注明 |
| chrome-devtools MCP | sdlc-test exec | 降级 Playwright（再缺失则该阶段阻塞，不是跳过） |
| codegraph MCP | sdlc-test static | 降级定向 grep + 读文件，结果注明证据降级 |
| lark-cli | sdlc-intent（飞书文档/评论区） | 用本地 markdown 文件路径输入，跳过评论区整合 |
| YApi MCP | sdlc-test cases（接口契约摄入） | 跳过该信息源，用例按需求文档推导 |
| Agent 工具（子代理） | sdlc-gate / sdlc-doubt | 核心机制依赖，缺失则该 skill 不可用 |

**Q：和任务框架（如 Trellis）是什么关系？必须配合使用吗？**
A：不必须。5 个 skill 均可独立运行（sdlc-gate/sdlc-doubt 对项目规范目录的引用均带「读不到则降级」声明）。配合任务框架体验更好——大需求的 parent/child 切片、规范注入等由 [large-req-playbook.md](large-req-playbook.md) 描述的机制承接，任何框架或纯目录约定都能复刻。

### 使用建议

**Q：从哪个 skill 开始用？**
A：按依赖重量渐进（详见 README「渐进采用阶梯」）：sdlc-intent（零依赖）→ sdlc-config-review（零 MCP，任意 git 仓库即用）→ sdlc-doubt → sdlc-gate → sdlc-test（依赖最重）。

**Q：sdlc-test 适用什么技术栈？**
A：按「Java 后端 + MySQL + Web 前端（Element Plus 系组件库）」打磨；static 阶段的前后端代码定位可适配任意栈（codegraph/grep），exec 阶段的交互姿势手册以 Element Plus 为锚点，其他组件库需自行沉淀姿势（手册结构可直接复用）。

**Q：单人开发/小团队值得用吗？**
A：sdlc-intent（把 PRD 消化成结构化共识）、sdlc-doubt（决策前对抗复查）单人即有收益；sdlc-gate 的多子代理评审在「设计+用例两份产物都存在」时收益最大；确认点/关卡体系本质是「AI 推进、人裁决」的纪律，与团队规模无关。

**Q：产物为什么都写成 Markdown 文件而不是对话里输出？**
A：产物落盘（`sdlc/<需求名>/`）是这套工作流的底座之一——跨会话可恢复（进度与关卡状态持久化在文件头部）、可逐行核对（人工关卡的核对对象）、可追溯（跨产物 `命名空间.编号` 引用）。会话内输出是易碎的。

## 术语表

| 术语 | 释义 |
|---|---|
| digest | 需求梳理文档：对 PRD 的忠实结构化转述（角色/概念/流程图/状态机/规则口径），sdlc-intent 第一段产物 |
| audit | 需求体检报告：按六层缺陷维度（概念/状态机/数据字段/规则逻辑/角色覆盖/文档质量）分级的缺陷清单 |
| pm-checklist | 待 PM 澄清清单：🔴/🟡/🔵 分级的问题表，带答复列可直接回传 |
| 三件套 | digest + audit + pm-checklist，存于 `sdlc/<需求名>/intake/` |
| 确认点①②③ | 大需求三段式的三个人工核对关口：①业务全貌逐行核对 ②技术骨架（D 表八类别齐套）③child prd 评审（见 playbook） |
| Q 表 | 待确认项表（问题/当前假设/阻塞范围三列）；硬阻塞=未决口径只锁对应功能点的开发，不阻塞全局 |
| D 表 | 关键实现决策表，八类别必答（并发/对账/状态联动/统计口径/权限/回显/时间格式/外部降级），漏答不得过确认点② |
| D 表/规则编号 | 跨产物引用统一 `命名空间.编号`：需求.FR-xx / 体检.P-xx / 功能.F-xx / 确认.Q-xx / 设计.D-xx / 用例.TC-xx / 缺陷.BUG-xx |
| 三段式 | 大需求自顶向下拆分：第一段业务全貌 → 第二段技术骨架 → 第三段逐功能点切片（骨架 child 先行） |
| parent / child | 需求级容器任务 / 可独立交付的切片任务（三层金字塔的顶层与底层） |
| 骨架 child | 第一个切片任务，交付枚举/常量/DDL/公共子结构，完成后业务 child 才放行 |
| 横切功能点 | 无独立触发角色、代码落点分散多接口的功能（如定时状态流转），随宿主 child 交付 + 核验矩阵补验 |
| fresh-context 子代理 | 无历史会话记忆的独立 AI 实例——对抗式审查的前提，避免被主会话结论带偏 |
| 关卡1 / 关卡2 | sdlc-test 的两道人工关口：用例审核、报告复验（状态持久化在用例文件头部） |
| 关卡互认 | sdlc-gate 放行后代改 sdlc-test 关卡1 状态——裁决已覆盖人工用例审核 |
| RECONCILE 四分类 | 子代理输出的过滤框架：契约误读（不进清单）/ 有效可行动（进）/ 有效权衡（进，标权衡）/ 噪音（不进） |
| 三类分歧 | 交叉审查发现的设计↔用例口径不一致，按去向分三类：一补用例、二回查设计、三升级用户拍板 |
| 三去向 | 执行中发现口径冲突的处置：实现偏离=BUG / 需求未定=转 Q / 用例写错=修用例留档；禁止静默按实现校正 |
| 证据降级 | 外部依赖缺失时退而求其次的取证方式，须在产物中注明（不许静默放行） |
| 反合理化表 | SKILL.md 中的「借口 vs 现实」表，拦截执行 AI 的自我合理化路径 |
| evals | skill 的评估场景文件（输入 + expected_behavior 勾选清单），手动回归用、红线判负 |

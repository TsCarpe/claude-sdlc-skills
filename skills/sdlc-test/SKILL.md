---
name: sdlc-test
description: "AI 测试智能体编排：用例生成 → 静态代码一致性检测 → test 环境浏览器功能测试 → 报告生成。子命令（cases/static/exec/spec/report）独立可重跑，两道人工关卡（用例审核、报告复验）；通过用例可资产化为 Playwright spec，回归轮跑 runner 零 agent token。Use when 用户要求 AI 测试、生成测试用例、执行测试、提测验证、回归测试、生成回归脚本、spec 资产化，或说 AI testing、test generation、browser E2E、playwright spec。用法：/sdlc-test cases|static|exec|spec|report <需求名>"
---

# AI 测试智能体

方案全文见开源仓库 `docs/sdlc-test-design.md`（设计决策记录，非 references 一层引用；skill 安装副本中该文件缺失，以本 SKILL.md 与 references/ 为准继续执行）。测试对象是 test 环境的 Web 前端（Java DDD 后端 + MySQL）。

**栈适配**：方法论栈无关；栈绑定面的盘点与换栈入口见 `references/stack-profile.md`（换栈/新项目接入时读，日常执行不加载）。

产物目录（相对当前项目根）：`sdlc/<需求名>/test/` 下放 `cases.md` 与 `reports/<日期>-r<N>/`；共享环境配置在 `sdlc/env/`。

## 路由

| 子命令 | 阶段 | 产物 | 前置条件 |
|---|---|---|---|
| `cases <需求名或文档路径>` | 1 用例生成 | `sdlc/<需求名>/test/cases.md` | 无 |
| `static <需求名>` | 2 静态代码检测 | `sdlc/<需求名>/test/reports/<日期>-r<N>/static.md` + 用例文件重点验证项 | 关卡1 已过 |
| `exec <需求名> [--from TC-xx \| --all]` | 3 前端功能测试 | 同轮目录 `exec-log.md` + 用例回填/缺陷跟踪 + 截图 | 关卡1 已过 |
| `spec <需求名>` | 3.5 spec 资产化 | `sdlc/<需求名>/test/specs/*.spec.ts` | 关卡1 已过；目标用例已通过且口径拍板 |
| `report <需求名>` | 4 报告生成 | 同轮目录 `report.md` | 阶段3 有结果 |

未带子命令时询问用户执行哪个阶段；无 `sdlc/<需求名>/test/cases.md` 时引导从 `cases` 开始。

## 轮次（round）规则

- **轮次目录**：`sdlc/<需求名>/test/reports/<日期>-r<N>/`，同轮 static / exec-log / report / screenshots 聚合一处。N = 该需求已有最大轮次 +1，不存在时从 r1 起。**大小写约定**：轮次目录名用小写 `r<N>`，用例结果/缺陷状态/修复轮次用大写 `R<N>`
- **轮次含义**：一次「检测→执行→报告」周期为一轮。需求和用例稳定的前提下，多轮 bug 修复 → 多轮回归，每轮独立留档，内容随缺陷收敛递减
- **回归轮（r2+）默认范围**：
  - static：只复检上轮 ⚠️ 疑似偏差与 ❓ 未确认项（代码已变），增量留档；`--all` 全量重比
  - exec：只重跑上轮失败/疑似/阻塞用例 + 缺陷跟踪表未闭环项（状态≠已修复验证）关联用例；`--all` 全量重跑。存在 specs/ 时回归轮分两步（见阶段3「回归轮两步」）：已资产化用例先跑 runner，其余走 agent 执行
- **用例文件是当前状态快照**：「结果」字段（新格式=用例总览结果列；存量表格文件=结果列）只反映最新轮次，格式 `通过（R2）`；历史判定在各轮 exec-log 留档
- **缺陷生命周期只在用例文件「缺陷跟踪」表维护**：新失败登记 BUG-xx，回归通过后更新状态/修复轮次；各轮 report 的缺陷清单摘引该表当轮切片

**关卡强制**：执行 `static`/`exec` 前读用例文件头部，`审核状态 ≠ 已确认` 时拒绝并提示用户先完成关卡1（人工审核用例后，将头部状态改为 `已确认（日期）`，或让用户口头确认后代改）。若 `sdlc/<需求名>/review/` 存在，关卡1 以 sdlc-gate 状态为准：`评审状态 = 已放行` 视同关卡1 通过（代改时引用 issues 文件），`≠ 已放行` 时拒绝并提示先完成 sdlc-gate 裁决；review 目录不存在则维持本条原行为。
**本条已机械化**（2026-09-15）：由 `scripts/guard_exec.py` 承载——关卡1 判定（含 gate 互认）、轮次目录命名、spec ✓ 标注与 specs/ 资产一致性（防 R3 型失真）均由脚本校验，入口命令见阶段2/3 第一步；脚本拒绝时停止并呈现缺失清单，禁止绕过。

## 阶段1 cases：用例生成

```text
Cases 进度：
- [ ] 定位输入（sdlc/<需求名>/intake/ 三件套优先，退回原始 PRD）
- [ ] 信息摄入（梳理文档/YApi/CodeGraph/MySQL 只读）
- [ ] 按七种设计技术生成用例并标注技术
- [ ] 填双向追踪表，未覆盖条目显式列出
- [ ] 写 sdlc/<需求名>/test/cases.md（模板：references/cases/case-template.md）
- [ ] 🔒 关卡1：暂停等人审核
```

- 输入优先级：`sdlc/<需求名>/intake/digest-*.md` 三件套 > 原始需求文档。梳理文档的角色权限矩阵、状态机图、流程图、规则口径清单是设计直接输入；体检报告疑似问题转重点用例；PM 清单已澄清口径回填预期
- **独立性纪律（红线）**：生成过程禁止读技术设计文档（`sdlc/<需求名>/design.md`、任务系统/协作工具中的设计文档等）——用例必须与设计从 intake 三件套独立推导，sdlc-gate 交叉审查才有价值。用户坚持要读时先说明后果并征得明确确认，且在 cases.md 头部注明「已读设计，交叉独立性破坏」
- 设计技术清单与生成规则见 `references/cases/design-techniques.md`，必须先读
- 关卡1 措辞：「用例已生成于 <路径>，请审核；确认后我继续，需修改请直接说」。迭代直至用户确认，然后把头部 `审核状态` 改为 `已确认（日期）`

## 阶段2 static：静态代码检测（前后端）

0. 入口守卫：`python3 <skill 目录>/scripts/guard_exec.py <项目根> <需求名> static`（skill 目录 = 本 SKILL.md 所在目录：项目级安装为 `<项目根>/.claude/skills/sdlc-test`，全局安装为 `~/.claude/skills/sdlc-test`）——exit≠0 时停止并向用户呈现缺失清单（关卡1 未过/轮次命名违规/spec 资产失真），禁止绕过
1. 读 `sdlc/env/repos.local.md` 获取前后端仓库路径（缺失则按 `references/env-template.md` 引导创建）；后端默认当前项目
2. 按梳理文档 §7「关键规则与口径」的 需求.FR-xx 编号逐条提取业务规则（三件套缺失时回退原始 PRD 的规则/口径章节，并在 static.md 注明证据降级），并标注检测端：后端（接口校验/权限/状态流转/排序 SQL）或前端（按钮显隐/页面校验/提示文案/页签隐藏）
3. 后端：用 `codegraph:codegraph_context`/`codegraph:codegraph_explore` 定位每条规则的 Controller → Service → Mapper/XML 链路；`mysql:mysql_query` 核对表结构。前端：`codegraph:codegraph_search`/`codegraph:codegraph_context` 传 `projectPath` 指向前端仓库索引定位页面/组件；无索引则降级定向 grep + 读文件，结果注明证据降级
4. 按 `references/static/static-check-template.md` 产出三态结论留档至本轮目录 `static.md`：✅符合 / ⚠️疑似偏差（附代码位置，前后端位置分别标注仓库）/ ❓静态无法确认
5. ⚠️ 项写入用例文件「重点验证项」区块，阶段3 优先执行；重大偏差立即报告用户

## 阶段3 exec：前端功能测试

> 执行≠验证：跑通创建流程≠验证了业务规则；页面表现正常≠无缺陷（接口/落库/console 必查）；用例预期与实现冲突时**禁止静默按实现校正**。首次执行参考 `references/exec/exec-example.md` 完整范例

```text
Exec 进度：
- [ ] 入口守卫：`python3 <skill 目录>/scripts/guard_exec.py <项目根> <需求名> exec`——exit≠0 时停止并向用户呈现缺失清单，禁止绕过
- [ ] 读 sdlc/env/test.md 与 accounts.local.md（缺失则按 references/env-template.md 引导创建）
- [ ] 前置健康检查：chrome-devtools:list_pages 确认浏览器/页面存活、目标路由可达、MySQL 连通（SELECT 1）、上传目录就绪；失败项先按 ui-recipe「环境检查」的恢复动作处置（仍失败再报告，不空等人工）；读 sdlc/env/ui-recipe.md（无则首条用例侦察后按 env-template 沉淀）
- [ ] 读用例头部进度，确定本轮目录与用例范围（--from TC-xx 断点续跑；回归轮默认重跑上轮失败/疑似/阻塞+缺陷未闭环项；--all 全量）；回归轮且存在 specs/ 时先走 runner 批量回归（见下「回归轮两步」）
- [ ] 按 `references/exec/exec-dispatch.md` 切批派发子 agent（每批 3-5 条，批间串行；证据采集/判定/exec-log 留档在子 agent 上下文完成）
- [ ] 每批回传后：主 agent 按压缩结论回填 cases.md（结果字段 + 证据摘要 + 缺陷跟踪表 + 头部进度——新格式：总览表结果列与 TC 小节证据行；存量表格：结果列与证据列）；P0 缺陷立即快报
- [ ] 全部完成，更新用例头部阶段进度
```

- **派发执行**：主 agent 不在自身上下文逐用例操作浏览器；按 exec-dispatch.md 组装自包含 prompt（批内用例条目原文 + 红线原文 + 最小挂载姿势），子 agent 完成侦察/执行/四类证据/截图查看/exec-log 留档，只回传每用例一行压缩结论。本节全部纪律与反合理化表**对子 agent 同样强制**，回传里禁止出现截图/报文/快照原文
- **回归轮两步（存在 specs/ 时）**：① 以绝对路径形态跑 runner：`<项目根>/sdlc/node_modules/.bin/playwright test --config <项目根>/sdlc/playwright.config.ts <需求名>`（禁 `cd`+`npx` 形态，cwd 无关——详见 spec-guide「runner 执行纪律」）——绿色项直接回填 cases.md，红色项按 `references/spec/spec-guide.md`「失败三向」诊断（trace/截图在 runner test-results/）；② 其余范围（新用例/失败现场/无 spec 用例）照常按 exec-dispatch 派发。登录态重采（capture-login.mjs）、DB 抽查衔接见 spec-guide；runner 基础设施缺失时先按 `references/env-template.md`「回归档 Playwright runner」接入表引导搭建
- 登录：test 环境账号密码直登（账号在 `sdlc/env/accounts.local.md`，gitignored）
- **交互姿势**：浏览器/数据库操作按 `references/exec/exec-interaction.md` 执行（浮层失明降级、日期键盘路径、evaluate 同步返回等）；新控件姿势 ≤3 次试错后回写该手册
- **分组合并执行**：同 G-xx 组（见用例文件「执行分组」区块）拦截类用例在同一表单会话内连续验证（改字段→断言→复原），每条用例仍独立留档判定；涉及提交/落库的用例不合并
- **落库断言前置**：表结构/列名以本轮 static.md 为准；bigint 主键按 exec-interaction 规范用业务键定位（JSON 往返舍入）
- **等待稳定再取证**：操作后先等页面稳定（`chrome-devtools:wait_for` 目标文本/元素出现，或确认对应网络请求已完成）再采集证据——禁止轮询 take_snapshot 等稳定——防抢跑拿到 loading 骨架误判"功能缺失"；等待超时本身是证据，写入备注
- 判定证据（缺一存疑就标"疑似"）：页面表现 + `chrome-devtools:get_network_request` 按 URL 定向获取接口响应（`list_network_requests` 仅在定位不到目标请求时使用）+ `mysql:mysql_query` 落库核验 + `chrome-devtools:list_console_messages` console 异常（补充；**error 级必查**——与失败相关的 error 作初判依据，无法解释的 error 标"疑似"不判通过；warning 记档不阻断）
- **通过前视觉复核**：判"通过"前扫一眼全页截图——视觉异常（布局错乱/弹窗遮挡/错误提示/列表空白）即使接口与落库正确，也降为"疑似"并备注
- **口径冲突三去向**：用例预期模型与实现不符（如时间链模型、快照口径）时，先以需求/拍板口径判定——实现偏离=登记 BUG-xx；需求未定=转 Q 待用户裁决；用例写错=修用例并在 exec-log 留档；仅确认实现正确后才按实际口径校正预期
- 截图：`chrome-devtools:take_screenshot` 一律先落本轮目录 `screenshots/`；仅展示类断言或异常疑点时 Read 查看（查看发生在子 agent 上下文，主上下文不加载图片）
- **疑似偶发失败 retry-once**：失败先按 exec-interaction 失败归因排查姿势/等待问题；疑似偶发/环境性失败单条重跑一次，两次一致才定论，不一致标 `flake疑似` 不登记 BUG（详见 exec-dispatch.md「anti-flake」）
- **留档**：按 `references/exec/exec-log-template.md` 逐用例写 `exec-log.md`（判定+证据引用+备注），当日志而非汇总写——每用例一段，执行完立即追加；本轮开始先按范围预填「结果总览」表（结果列留空），执行期只更新对应行；证据按页面/接口/落库/console 四类分行；备注除偏差外，执行中任何让你停顿的观察（文案/交互/性能/意外行为）都记录，不预筛"是不是缺陷"
- **缺陷跟踪**：新失败在用例文件「缺陷跟踪」表登记 BUG-xx（缺陷四要素详见 report-template）；回归轮重跑通过后更新「状态=已修复、修复轮次=R<N>」；不复现在备注说明
- **P0 缺陷快报**：发现口径违背/数据污染风险级缺陷立即报告用户裁决，不等整批执行完
- **造数纪律：探索档允许通过前端页面操作（点击触发后端接口）生成前置数据；spec 档允许 API 直调造前置（走后端完整校验，鉴权头见 ui-recipe）；两档均禁止改库/任何 DB 直写**；MySQL MCP 只读仅做核验
- a11y 快照对 canvas/复杂自定义组件失明时，降级截图 + 视觉判断，结果注明证据降级
- chrome-devtools MCP 失效时降级 Playwright skill
- **阻塞前穷尽解锁**：标阻塞前先依次确认 ui-recipe 路由清单、Playwright skill 降级、接口直调（鉴权头见 ui-recipe）三条路径均不可行

## 阶段 3.5 spec：资产化（回归档）

> 通过且口径拍板的用例 → Playwright spec；此后回归轮该部分由 runner 执行（零 agent token），agent 只诊断红色项。完整规则（粒度/前置复用/选择器/证据映射/失败三向/生命周期）见 `references/spec/spec-guide.md`，必须先读。
> **前置（首次）**：runner 基础设施（`sdlc/` 根两件 + `env/runner/` 三件）缺失时，按 `references/env-template.md`「回归档 Playwright runner」接入表引导搭建——复制模板 → 替换占位符 → sdlc/ 根 npm install → spike 全绿即就绪。

1. 准入：默认范围 = BUG 关联用例 + P0/P1 稳定流；用例条目手标可扩围
2. 读 cases.md + exec-log「复现锚点」翻译为 spec：`test()` = 一用例、按 G-xx 组/模块归档、前置 API 直调优先 / flows/ UI 函数兜底（≥2 用例用到才抽）
3. **生成后立即 runner 验证，全绿才算资产化完成**；红色按失败三向处置（实现坏=BUG / 页面变=修 spec 留档 / 环境=备注重跑）
4. cases.md 用例条目标注 `spec ✓（日期）`（新格式=总览表 spec 列；存量表格文件=行内标注）；DB 断言不进 spec，出过 DB BUG 的用例在 spec 头部挂 SQL 清单（回归轮 agent 抽查）

## 阶段4 report：报告生成

1. 按 `references/report/report-template.md` 汇总产出本轮目录 `report.md`（回归轮为回归报告：重跑范围+缺陷闭环情况）；含 runner 执行时按模板「回归档」口径呈现 runner 切片与 DB 抽查结果
2. 🔒 关卡2 措辞：「报告已生成于 <路径>，请复验缺陷真伪；确认后的缺陷由你转达开发」。缺陷不自动推送任何外部系统。用户复验确认后，勾选用例头部「🔒 关卡2 报告复验」并注明轮次（如 `已复验（R2，YYYY-MM-DD）`）——与关卡1 代改口径对称，多轮场景可从用例文件看出各轮报告复验状态

## 通用纪律

- 源码只读、数据库只读；写操作仅限 test 环境前端页面与 `sdlc/` 目录
- 拿不准的判定标"疑似"并附证据，不硬下结论
- **汇报自解释**：向用户输出阶段小结/汇报时，统计须含端分布（前端/后端/前后端）；每条问题明细自解释（编号+现象+预期差异），禁缩写引用；「详 exec-log」等深挖入口只能附在完整陈述之后
- 每阶段结束更新用例文件头部阶段进度 checklist
- 术语统一：用例 ID 记作 TC-xx；角色名、状态名沿用梳理文档口径；**跨产物引用统一 `命名空间.编号`**（需求.FR-03 / 需求.A3 / 体检.P04 / 设计.D11 / 评审.T-12），禁止裸写他产物编号

### 反合理化

| 借口 | 现实 |
|---|---|
| "console 有 error 但页面表现正常，算通过" | error 是缺陷线索，必查；无法解释就标"疑似"，不判通过 |
| "四类证据差一类，其余都对，直接下结论" | 缺一即标"疑似"，证据底线不因多数通过而放松 |
| "直接改库造数更快" | 造数走前端页面操作（探索档）或 API 直调（spec 档），均经后端校验；改库绕过业务校验且污染回归基线 |
| "DOM 快照失明/截图看不清，就当通过" | 降级视觉判断必须注明"证据降级"，不允许静默放行 |
| "chrome-devtools 坏了，这条用例跳过" | 降级 Playwright skill 继续执行，工具故障不是跳过理由 |
| "点击后立即检查，页面还在 loading，功能就是坏的" | 先等稳定（wait_for / 网络请求完成）再判定；抢跑误判是执行事故，不是缺陷 |
| "控件姿势试错几轮是正常成本" | 按交互姿势手册执行；新姿势 3 次试错内沉淀回写手册，下个项目/会话不重付学费 |
| "runner 全绿 = 四类证据全过" | runner 绿只覆盖页面/接口/console 三类；落库按 spec 头部 SQL 清单抽查，未抽查项在报告注明 |
| "spec 红了，删掉改人工跑" | 先按失败三向诊断（实现坏=BUG / 页面变=修 spec / 环境=备注重跑）；删 spec 是放弃资产，仅限用例本身作废 |

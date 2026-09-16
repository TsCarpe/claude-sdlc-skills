# sdlc-test 演进：从「点击员」到「脚本作者」

> 缘起：2026-09 一项外部研究（脚本作者 vs 点击员）触发对 sdlc-test 执行模型的重估。
> **状态：已实施**——本文两份材料（流派研究 + 改进计划草案）的全部结论已落地为 sdlc-test 的 `spec` 子命令与 runner 回归机制，收敛决策 D14-D21 见 [sdlc-test-design.md](sdlc-test-design.md) §9；本文保留研究过程与决策依据，作为演进记录收录（2026-09-16 脱敏整理）。

---

## 一、流派研究：脚本作者 vs 点击员

> 研究缘起：[GlowJames 追光的帖子](https://x.com/jameszz343698/status/2099108669967507536)（2026-09-13）。整理时间：2026-09-14。

### 1.1 原帖论点拆解

原帖主张：**别让模型当"点击员"，让它当"测试脚本作者"。**

1. Agent 自己开浏览器跑 E2E（截图→思考→点击→再截图）token 贵、慢、不稳定，且测完不留任何可复用资产。
2. Agent 应该写可重复执行的 Playwright 测试脚本，执行交给 runner（playwright test 命令），稳定、快、几乎不烧 token，天然支持回归。
3. 把规则固化到 AGENTS.md / CLAUDE.md / .cursorrules：禁 UI 单测、禁浏览器 MCP 自驱 E2E、每个功能/修复必须带 spec、只以 runner 通过为验收。
4. 用例定位用 `getByRole`/`getByTestId` 等语义选择器；失败时留 trace + screenshot，Agent 读产物调试，而非人肉看截图。
5. 与 Playwright 官方 Test Agents（Planner/Generator/Healer）不矛盾：那些是**生成/修复测试代码**的工具，被反对的是让编码 Agent 实时扮演测试员。

### 1.2 同论点资料（支持派）

**[我是怎样使用 AI 构建 E2E 测试体系的？](https://vikingz.me/ai-e2e/)（vikingz，与原帖最接近）**

TinyShip monorepo（3 框架 × 2 数据库 = 6 种组合）的实践。五阶段工作流：

```
Spec（TEST-CATALOG.md 写验收标准）→ Code → Verify（agent-browser 预演一遍）→ Test（写 Playwright spec）→ Green（6 组合全绿）
```

- 核心观点："User Cases 比代码更宝贵"，AI 时代迭代以小时计，回归保障是基石。
- **agent-browser 只做一次性预演**：既做视觉确认，又顺手拿到可靠元素引用（`@e4` 式），所以之后写 spec "基本一次就能稳定"。反复跑则又慢又费 token——与原帖同款理由。
- E2E 不进 CI（太慢、外部依赖多），按改动规模分三档跑测时机。

**[Playwright MCP Complete Guide](https://qaskills.sh/blog/playwright-mcp-browser-automation-guide)（qaskills）**

混合工作流：Agent 用 MCP **探索**（发现可靠 locator）→ 写 `.spec.ts` → 用 Playwright Test 跑 → 失败看 trace。MCP 是探索工具，持久资产是测试代码。

**[r/softwaretesting 社区共识](https://www.reddit.com/r/softwaretesting/comments/1rliced/playwright_test_automation_with_ai/)**

"Use a coding agent or LLM to write a deterministic Playwright test. Deploy that test. Use an agent or LLM to resolve issues with failing tests." ——确定性问题交给脚本，诊断修复交给 Agent。

**[AI Agent 协作写 E2E 测试：从 Playwright 脚本到可维护的测试套件](https://clawd.org.cn/forum/post?id=31456)（clawd 论坛）**

针对 E2E "写完很快乐，维护很痛苦" 的痛点，讲如何让 AI 协作写出可维护的 Playwright 套件——承认脚本脆弱，但答案是协作写好脚本而非放弃脚本。

**[分层测试框架实践](https://gist.github.com/felix021/33f733c6502961577db992947969b5f9)（felix021 gist）**

Rust 全栈项目（Server + CLI + Tauri）55 个 E2E 的分层实践，附给 AI Agent 协作开发的建议。

### 1.3 反方资料（对照派）

**[告别 Playwright 脚本，迎接 AI 驱动的 E2E 测试新范式](https://www.dteam.top/blogs/2025-09/a-new-way-to-do-e2e-testing)（老胡茶室，立场相反）**

- 论据：E2E 与 UI 强耦合，UI 变动最频繁，脚本"柔韧性天生不足"，生成脚本只是"2 倍速的手工维护"。
- 方案：**自然语言即测试脚本**——prompt 生成测试计划 → 人工 review 计划（计划本身就是驱动 Agent 的 prompt）→ Agent + Playwright MCP 实时执行（browser_navigate / browser_snapshot / browser_click…）→ 自动出报告。
- 优点：非技术人员可写用例、零脚本维护成本。
- 薄弱点：未讨论成本、稳定性、非确定性；每轮回归都要全价烧 token，且无确定性回归资产。

**商业化 AI 原生测试平台（browser-use 系）**

- [QA Use](https://zhuanlan.zhihu.com/p/2047230663770879730)：browser-use 官方平台，Browser-Use Agent + Playwright 底座，自然语言跑用例。
- [TesterArmy](https://www.tinyash.com/blog/testerarmy-ai-test-agent-e2e-guide/)：主张"描述意图"替代脚本编写维护。

注意：这类平台底层最终仍落到 Playwright 执行，本质是把"点击员"产品化并规模化，与个人开发场景的性价比论证并不冲突。

### 1.4 官方工程指南（方法论底座）

| 来源 | 关键点 |
|---|---|
| [Claude Code Best Practices](https://code.claude.com/docs/en/best-practices) | 官方推荐的 TDD 环：先写测试→确认失败→实现→跑到绿→commit |
| [Building verification loops in Claude Code with skills](https://claude.com/blog/building-verification-loops-in-claude-code-with-skills) | 把验证闭环固化成 skill，可复用、可自动触发 |
| [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | 长时程 Agent 的关键：**确定性验证** + 设计良好的反馈回路 |
| [Playwright Test Agents 官方文档](https://playwright.dev/docs/test-agents) | Planner（出测试计划）/ Generator（计划→spec 文件）/ Healer（修失败用例）——AI 的正确位置是产线维护测试代码 |
| [Playwright 官方博客：Agents in Action](https://dev.to/playwright/playwright-agents-planner-generator-and-healer-in-action-5ajh) | 三角色分工详解 |
| [Microsoft：The Complete Playwright E2E Story](https://developer.microsoft.com/blog/the-complete-playwright-end-to-end-story-tools-ai-and-real-world-workflows/) | 官方定位：MCP 是测试生成的起点，不是回归执行器 |

### 1.5 对 sdlc-test 的优化启示（当时的判断）

结合当时的执行模式（Agent 实时走 UI 用例 + MySQL 只读数据核验）：

1. **产物化**：把"走一遍 UI 用例"的产出从会话记录升级为落盘的 spec 文件（用例即资产），回归时跑 runner 而非重演对话。
2. **MCP 用在刀刃上**：浏览器自动化只做两件事——首次预演拿语义选择器（`getByRole`/`getByTestId`）、失败时读 trace/screenshot 排查；不再作为回归执行器。
3. **规则前置**：在 sdlc 规则文件中写明"每个功能/修复必须伴随 spec、验收以 runner 通过为准"，即原帖的约束写法。
4. **分层跑测时机**（参考 vikingz 三档）：功能内只跑相关 spec；发版前全量；小修补只跑 typecheck/build。
5. **警惕反方场景的合理内核**：探索性测试、新功能首次验收、非技术角色写用例，自然语言 + Agent 实时执行有其价值——可作为"探索档"保留，与"回归档"（spec + runner）分层并存。

### 1.6 开放问题（当时的遗留）

- 反方"自然语言测试计划"若也纳入版本库，与 spec 文件的区别只剩执行器——是否值得做"计划→spec"的自动转换管线（Playwright Generator 已内置此能力）？
- E2E 是否进 CI：vikingz 的结论是不进（36 分钟太慢），本项目 test 环境依赖本地前端 + 登录态，同样需要权衡。
- Healer 对"选择器失效类"失败的自动修复率，社区评价不一（见 [r/Playwright 讨论](https://www.reddit.com/r/Playwright/comments/1p1sm33/playwrights_new_ai_agentsare_they_actually/)），引入前建议先小范围验证。

---

## 二、改进计划（草案，已全部裁决落地）

> 依据：上文流派研究 + 当时 sdlc 工作区盘点（2026-09-14）。原状态"草案，待用户核对 4 个决策点"；决策后收敛为 [sdlc-test-design.md](sdlc-test-design.md) §9 的 D14-D21。

### 2.1 现状诊断（改造前）

当时执行模型 = "点击员"模式：每轮回归都是 Agent 实时走 UI（一轮全量重跑 TC-01~34，会话目录留有 100+ 份页面快照），产出 exec-log + 截图——**能看，不能重放**。每步页面快照进上下文，token 贵、慢、结果非确定性。

已有资产（扎实，保留）：
- `sdlc/<需求名>/test/cases.md`：结构化用例（数十条）+ 双向追踪 + 口径裁决
- 项目侧环境配方（ui-recipe）：路由清单、鉴权直调头、项目特有坑
- 静态检测（static.md）+ review gate 关卡机制

缺口：缺"可重复执行的 runner"这一层，回归只能靠重演对话。

### 2.2 目标模型：两档分层

| 档 | 适用场景 | 执行方式 | 产出 |
|---|---|---|---|
| 探索档（保留现状） | 新功能首验、失败排查、口径确认 | Agent 实时走 UI | 更新 ui-recipe / 用例口径 / exec-log |
| 回归档（新增） | BUG 修复验证、回归轮次（R3+） | runner 执行（绝对路径二进制形态，见 D20） | spec 文件 + trace/截图（失败时） |

### 2.3 实施步骤（当时草案 → 落地情况）

**P0 工程搭建**
1. runner 工程：`playwright.config.ts`（baseURL 指向 test 环境，`trace: 'retain-on-failure'`，`screenshot: 'only-on-failure'`）；目录 `specs/<分组>/tc-xx.spec.ts`、`fixtures/`、`.auth/`——✅ 落地为项目侧 runner 工程（一键回归脚本模板见 [skills/sdlc-guardrails/templates/run_regression.sh](../skills/sdlc-guardrails/templates/run_regression.sh)）
2. 登录态方案（该环境最大特殊点：SSO 用户辅助登录、无账密直登）：
   - 辅助登录一次 → 保存 `storageState` 到 `.auth/<角色>.json` 全局复用
   - globalSetup 用环境配方的鉴权直调头 fetch 轻接口探活，401 → 提示重新辅助登录
   - 新角色上线后按同法各存一份 storageState，`projects` 按角色分——✅ 落地（capture-login 脚本采集 storageState，决策 D19）
3. ✅ 验证：冒烟 spec（打开管理列表页，断言列表容器+创建按钮）**连续两遍绿**

**P1 试点转化**
4. ✅ 默认范围 3 条（向导创建流程 / 范围选择快照类 / 数量钳制类各一条，含两个已修 BUG 的回归点）；浏览器自动化预演一遍拿语义选择器（`getByRole`/`getByText`），前端缺 `data-testid` 的补种
5. ✅ 落库断言：Playwright request fixture + 鉴权直调头调后端接口断言（零新依赖）；断言口径中文描述（code）双写、比对以 code 为准
6. ✅ 测试数据：spec 自建自清理——「创建验证-*」命名约定，跑前建、走删除接口清，幂等可重复
7. cases.md 每条用例加「脚本化」字段：`原生 | 已固化(spec路径) | ⏸不适固化`（纯视觉/富文本/上传类暂不固化）——✅ 落地为用例总览表的 spec 列（`✓ spec 路径 / 原生 / ⏸`，见 case-template）
8. ✅ 验证：试点 spec 连续两轮全绿；人为制造一次失败，trace 能定位到步骤

**P2 规则固化**
9. 测试阶段工作流约定：新功能/BUG 修复 → 必须伴随或更新对应 spec，验收以 runner 绿为准；回归轮次起默认跑 runner，Agent 只处理失败项（读 trace 排查）；浏览器自动化仅限首验、拿选择器、读 trace 排查——✅ 落地进 [spec-guide](../skills/sdlc-test/references/spec/spec-guide.md)（运行纪律节）
10. 环境配方（ui-recipe）增加「选择器登记」小节，预演时增量记录——✅ 落地进 env-template（spec 回归档锚点节）

**P3 回归演练**
11. 下次功能改动后用 runner 替代整轮实时回归，实测对比耗时与 token 消耗——✅ 实测：零 agent token、1.8 分钟跑 13 条（见 [agent-stack-mental-model.md](design/agent-stack-mental-model.md) §5 案例）

### 2.4 明确不做（当时结论，维持）

- 不进 CI：依赖 test 环境前端 + dev 库 + SSO 辅助登录
- 不全量转化用例：⏸ 暂缓类、富文本/上传/纯视觉类留探索档
- 不引 mysql2 直连依赖（落库断言走接口直调）、不改前端仓库结构（仅补 data-testid）

### 2.5 决策点裁决记录

| # | 决策点 | 裁决（与推荐一致） | 收敛为 |
|---|---|---|---|
| 1 | 试点范围 | 3 条起步而非全量 | D15 |
| 2 | runner 工程位置 | 项目侧 sdlc 工作区（非前端仓库） | D19/D20 |
| 3 | 落库断言方式 | 接口直调断言（不引 mysql2） | D18 |
| 4 | 测试数据策略 | 自建自清理 | D17 |

# 回归档 spec 指南（资产化与 runner 执行）

> 定位：通过且口径拍板的用例资产化为 Playwright spec；回归轮跑 runner（零 agent token），agent 只诊断红色项。探索档（chrome-devtools MCP 首验/新用例/失败现场诊断）纪律不变，本指南只管回归档。
> 依据：两层架构决策见 `doc/ai-testing-solution.md` v0.3（仓库内，跨项目使用缺失时以本指南为准）；runner 基础设施在 `sdlc/env/runner/`。

## 目录

- [目录与粒度](#目录与粒度)
- [runner 标准布局](#runner-标准布局2026-09-14-试点定型)
- [前置复用（三层，禁 beforeAll 共享）](#前置复用三层禁-beforeall-共享)
- [选择器与断言](#选择器与断言)
- [Element Plus spec 姿势](#element-plus-spec-姿势2026-09-14-试点实测区别于-mcp-探索档)
- [四类证据映射](#四类证据映射)
- [资产化流程（/sdlc-test spec）](#资产化流程sdlc-test-spec-需求名)
- [spec 失败三向（回归版口径冲突）](#spec-失败三向回归版口径冲突)
- [生命周期](#生命周期)

## 目录与粒度

- spec 落位：`sdlc/<需求名>/test/specs/<组或模块>.spec.ts`（如 `g02-create-wizard.spec.ts`）；公共 UI 流抽到同目录 `flows/`（如 `flows/contest-flow.ts`）
- **`test()` = 一条用例**，标题首带编号（`test('TC-27 无专家配置可提交', …)`），与 cases.md TC-xx 一一对应，结果可直接回填
- **文件 = 按 G-xx 执行分组 / 同模块归档**，与 cases.md 分组结构对齐

## runner 标准布局（2026-09-14 试点定型）

```text
sdlc/
├── package.json + playwright.config.ts + node_modules/  # 依赖与 config 必须在 sdlc 根
│   # 原因：specs 的模块解析向上查找，装在 env/runner/ 子目录会命中项目根另一份 @playwright/test → 双树冲突
└── env/runner/          # capture-login.mjs / browser-state.json / spike.spec.ts / test-results/
```

- config 关键项：`testDir:'.'`、`channel:'chrome'`（系统 Chrome 零下载）、`workers:1`、storageState/outputDir 用 `path.resolve(__dirname,…)` 绝对化（相对路径按 cwd 解析，实测会错位）

## 前置复用（三层，禁 beforeAll 共享）

| 层 | 手段 | 说明 |
|---|---|---|
| 登录态 | storageState（config 已配） | 过期表现=重定向「欢迎登录」→ 跑 `node sdlc/env/runner/capture-login.mjs` 重采（自动检测登录并保存，勿用 codegen） |
| 前置数据 | **API 直调优先**（`request` fixture + ui-recipe 鉴权头） | 走后端完整校验，秒级；无对应接口或前置即被测对象时用 flows/ |
| 公共 UI 流 | `flows/` 函数复用 | **≥2 条用例用到才抽**，否则内联；函数从 exec-log 复现锚点翻译 |

- 禁止组内共享一场提交（beforeAll/serial）：状态耦合、一红俱红；每条用例独立上下文是隔离底线
- **造数纪律（spec 档）**：前置数据允许 API 直调，禁止任何 DB 直写；探索档维持走前端页面操作

## 选择器与断言

- 选择器优先级：`getByRole` / `getByLabel` / 可见文本 > CSS 类（组件库内部类名如 `.el-select-dropdown__item` 可作兜底，须注释「内部类名，升级风险」）；禁 XPath
- 真 Playwright 无 MCP 快照失明问题：teleport 下拉直接 `getByRole('option', { name })` 点选，**禁止**把 exec-interaction 里的 evaluate_script hack 搬进 spec
- 动态值纪律：不断言 uuid/绝对时间戳/精确 ID；日期断言用相对口径；文案断言用稳定关键词不用全句；toast 叠加场景（连发两次拦截）用 `.first()` 收敛避免 strict violation
- **提交类 spec 可重入**：名称带运行时唯一后缀（`创建验证-spec${Date.now()%100000}`）——区域内未删唯一约束下固定名第二跑必撞重名拦截（2026-09-14 试点实测）

## Element Plus spec 姿势（2026-09-14 试点实测，区别于 MCP 探索档）

| 场景 | spec 做法 |
|---|---|
| select 过滤/搜索输入默认 `is-hidden` | 先点 `.el-select__wrapper` 激活，再操作 combobox；placeholder 常渲染在 span 不在 input（`getByPlaceholder` 匹配不到） |
| 日期键入 | click→fill('')→pressSequentially→Enter；**提交偶发不落**，自校验值（接受 yyyy-MM-dd / yyyy/MM/dd 两种回显）失败重试一次；非法值拦截断言须 blur（Tab）后看回弹，Enter 后弹窗未关值仍为键入态 |
| 语义 data 属性 | 前端有 `data-competition-field` 类语义属性时优先用（比 CSS 类名/顺序 nth 稳）；无则按值断言（输入框 value 恰为默认值时可用 `toHaveValue` 直接锚定行） |
| 多个上传位 | 按 `.el-upload` 容器文案区分（如「图片到此处上传」vs「文件到此处上传」），禁 `input[type=file]` first() |
| 上传完成判定 | 等 UI 成功态（如「更换」按钮 enabled）而非猜接口 URL（OSS STS+直传链路 URL 不含 upload 字样、PUT 发外部域） |
| 环境不预填的必填项 | 名额/审核时长等默认值不预填时会**静默拦截**下一步——flows 公共流显式补默认值并断言可见进度标记，卡住时先查空必填 |

**锚点侦察捷径**：写 spec 前用 `chrome-devtools:evaluate_script` 开同页面 dump 目标 DOM（data 属性/placeholder 清单/控件形态），比盲跑-修迭代快数倍（试点实测：3 发探针省 ~5 轮 runner 迭代）。

## 四类证据映射

| 证据 | spec 内形态 |
|---|---|
| 页面表现 | `expect` 断言（可见文本/按钮态） |
| 接口响应 | `page.waitForResponse` 定向等 URL，断 `code===0` 或错误码 |
| console | `page.on('console')` 收集 error；有不可解释 error = 该条判失败（与探索档口径一致） |
| 落库核验 | **不进 spec**（共享环境数据被他人造数污染、表结构随 static 每轮变、bigint 舍入坑）。出过 DB 类 BUG 的用例在 spec 头部挂 SQL 清单，回归轮 agent 用 MySQL MCP 定向抽查 |

SQL 清单格式（spec 文件头注释）：

```ts
/**
 * DB 抽查清单（回归轮 agent 用 MySQL MCP 执行；业务键定位，禁大 ID 直查）
 * - TC-01/BUG-01: SELECT school_id FROM skill_contest_school WHERE contest_id=(SELECT id FROM skill_contest WHERE name='创建验证-<规则>')
 *   预期：全部学校也落全量快照行（D-01 口径）
 */
```

## 资产化流程（`/sdlc-test spec <需求名>`）

1. **准入**：用例状态=通过 且 口径已拍板；默认范围=BUG 关联用例 + P0/P1 稳定流，可手标扩围（在目标用例条目标注「待资产化」——新格式标在用例总览 spec 列；存量表格文件就地标注）
2. 逐条读 cases.md 用例 + exec-log 该条「复现锚点」，翻译为 spec（组内共用前置抽 flows/）
3. **生成后立即以绝对路径形态跑 runner 验证**（命令见下方「runner 执行纪律」红线：`<项目根>/sdlc/node_modules/.bin/playwright test --config <项目根>/sdlc/playwright.config.ts <需求名>`，单条用例加 `--grep "TC-xx"`）——全绿才算资产化完成；红色项按下方三向处置，修完复跑
4. cases.md 用例条目标注 `spec ✓（日期）`（新格式=总览表 spec 列；存量表格文件=行内标注），文件粒度记入头部进度

**runner 执行纪律（红线，2026-09-14 试点实测定型）**：
- 调用形态用**绝对路径二进制 + 绝对路径 config**（cwd 无关）：
  `<项目根>/sdlc/node_modules/.bin/playwright test --config <项目根>/sdlc/playwright.config.ts <需求名>`
  ——`cd sdlc && npx playwright test` 形态实测不可靠（cwd 不持久/误从项目根跑会撞根目录另一份 playwright，报 "imported by the configuration file" 等误导性错误）
- 路径过滤参数是**绝对路径子串匹配**（传需求名即可，禁 `../../` 相对前缀）；按用例名单跑用 `--grep "TC-xx"`
- 失败留痕在 `sdlc/env/runner/test-results/<用例>/`（error-context.md 含 ARIA 快照 + trace.zip + 截图），agent 读产物诊断，不人肉看
- spike.spec.ts 是 runner 健康检查（登录态+连通），回归前可先单跑它定位环境问题

## spec 失败三向（回归版口径冲突）

spec 红色 ≠ 直接判 BUG，按序诊断：

1. **实现坏了** = 登记 BUG-xx（回缺陷跟踪表，证据=trace/截图+接口断言值）
2. **页面/口径变了** = 修 spec 并在 exec-log 留档「spec 校正原因」（对应探索档三去向的"用例写错"分支）
3. **环境问题**（登录态失效/后端 5xx/共享数据被动）= 修复环境后重跑，备注定性，不登记 BUG

禁"红了就删 spec 改人工跑"——那是放弃资产；删除 spec 仅限用例本身作废。

## 生命周期

- 口径拍板变更 → 同步改 spec 并留档；BUG 修复改变行为 → 该条 spec 由诊断路径（三向之 1）触发更新
- 组件库/前端大改后回归轮 spec 批量红 → 逐条三向分诊，集中修 spec 一次留档
- 维护回写：spec 侧新发现的选择器/等待姿势属通用层回写本指南，项目特有回写 ui-recipe

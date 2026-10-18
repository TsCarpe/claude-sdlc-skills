---
name: sdlc-ui-visual
description: "设计稿到代码的视觉还原闭环：以 Figma 链接或基准图为唯一视觉基准，对运行中的前端页面做真实浏览器截图比对（DOM 几何逐项对照 + 像素叠加/差异/热区 + 小元素放大判读），按 P0>P1>P2 分级驱动修复轮，功能回归后按六要素汇报。Design-to-code visual restoration loop: takes a Figma link or baseline image as the single reference, diffs the running page via real browser screenshots (DOM geometry checklist + pixel overlay/diff/heatmap + small-element zoomed inspection), drives tiered fix rounds, verifies functional regression, then reports. Use when 用户提供 Figma 设计稿或基准图要求视觉还原、UI 还原、设计稿还原、照着 Figma 改样式、像素级比对、视觉走查、视觉偏差修复，或说 ui check、ui-align。输入是设计稿基准且允许改样式代码——纯功能验证走 sdlc-test。用法：/sdlc-ui-visual Figma链接或基准图路径 [目标页面或组件]"
---

# UI 视觉还原

以设计稿为基准把运行中页面还原到位的闭环：**基准 → 代码对照 → 稳定截图 → 多道比对 → 分级修复轮 → 功能回归 → 汇报**。与 sdlc-test 分界：那边验「行为对不对」（源码只读），这边验「长得像不像设计稿」（以设计稿为基准、允许改样式代码）。

**栈适配**：方法论栈无关；Vue2 + element-ui 栈姿势见 [references/stack-vue2-element.md](references/stack-vue2-element.md)（换栈先读，日常执行不加载）。

**前置依赖**：`python3` + Pillow（compare.py；缺依赖时脚本会提示 `pip3 install Pillow`）；`figma-context-mcp`（Figma 输入，server 别名以实际安装为准）；浏览器自动化 MCP（`chrome-devtools`，不可用时按 pipeline 降级链切 Playwright）。

**产物目录**（相对目标项目根）：`.ui-check/<目标名>/`——独立于 `sdlc/` 工作区（无 sdlc 工作区也成立，有则互不依赖）。目录内二进制产物多，首次创建时提示用户把 `.ui-check/` 加入 .gitignore。

**状态落盘（run.md）**：`.ui-check/<目标名>/run.md` 是唯一状态源——七步进度、差异分类台账、待用户问题、已拍板记录全在其中，每步结束即更新；中断后重开会话 = 读 run.md 头部进度续跑，禁止凭对话记忆恢复、禁止推翻台账中已拍板分类。模板见 [references/templates.md](references/templates.md)。

## 步骤 0：环境与可达性

浏览器会话可用、目标路由可达、**登录态有效**。遇登录墙（SSO 等）不自行绕：请用户人工完成登录与页面导航，之后截图/断言/比对全自动化（人工分工要记入 run.md）。dev server 先探测再决定是否启动；浏览器工具冲突时按 [references/pipeline.md](references/pipeline.md) 降级链切换。

## 步骤 1：基准获取

- **Figma 链接**：`/design/` 后第一段为 fileKey；URL 里 `node-id=12-3456` 的 `-` 转 `:` 得 `12:3456` 作 nodeId。`figma-context-mcp:get_figma_data` 拿结构化数据（输出过大时持久化本地再解析），`figma-context-mcp:download_figma_images` 下载基准 PNG（pngScale=2，比对前等比缩到 1x，禁止拉伸；MCP server 别名以实际安装为准，如 `figma-context-mcp`）。
- **仅基准图**：跳过结构化数据，尺寸/颜色靠图像分析与人工读数。
- **frame 选择策略**（页面级）：node-id 即整页 frame（只用于上下文理解——应用壳与实际项目不同，整页比对无意义）；**比对基准 = 主内容区 frame**：从子 frame 按尺寸启发式筛（宽度最接近页面主体宽度者）+ 唯一性校验，多候选/零候选暂停问用户。组件级任务（弹窗等）node-id 本身即基准。选择结果记入 run.md。
- **期望值清单**：从基准数据建 `.ui-check/<目标名>/expected.md`——每元素 位置/尺寸/字号/字重/颜色/圆角/间距，**<20px 的小元素逐项打标 `小元素⚠`**（步骤 4 强制元素级验证）。细则见 [references/pipeline.md](references/pipeline.md)。

## 步骤 2：代码对照（修复动作前必做）

两个确定产物，不扩张成全量读码：

1. **git diff 已改样式盘点**：任务常发生在开发已写初版之上，先看未提交改动里已对齐了什么
2. **全局样式对抗清单**：grep 全局覆盖文件（主题/变量/组件库全局 less 等），列出会压制本目标样式的 `!important` 与全局规则——不盘点就写样式 = 写无效样式

## 步骤 3：浏览器稳定化 + 截图

**视口 = 设计稿画布尺寸**，保持比例一致。每轮截图前稳定化三件（缺一截图无效，细则见 [references/pipeline.md](references/pipeline.md)）：

1. 轮询等主内容挂载（页面根 class 出现）
2. **关闭干扰弹窗**——弹窗不关 = 截图是旧帧且与 DOM 不一致
3. 等数据加载（树节点/列表行数 > 0）再截

**锚定对齐**：`getBoundingClientRect()` 实测参照元素位置作为锚点，设计稿内容区 `(0,0)` 对齐到该点，**不做全页对齐**。截图存轮次目录。

## 步骤 4：多道比对

```bash
python3 <skill 目录>/scripts/compare.py --actual <截图> --design <基准图> \
  [--ox <锚点x> --oy <锚点y>] [--box x y w h] --outdir .ui-check/<目标名>/r<N>/
```

产出：50% 叠加图 / 差异图 / 热区网格（附格中心坐标）/ mean diff / >30 差异像素占比 / 暗像素计数，stats 落盘轮次目录。

- **第 1 道 DOM 几何**：期望值清单逐项对照 `getBoundingClientRect` + `getComputedStyle`（精确到 0.1px）
- **第 2 道像素比对**：叠加 + 差异图 + 热区，抓几何对照漏掉的渲染问题
- **小元素强制验证（独立于上面两道的结果）**：凡期望值清单打标 `小元素⚠` 的元素，一律 `--box` 裁剪放大 ≥3 倍 + 视觉判读「形状/大小/颜色」+ 暗像素计数——两道全过也不豁免（区域平均会稀释小元素差异，数值等价 ≠ 视觉等价）

比对产物的读法与「不可判定 → 升级验证手段」路径见 [references/triage.md](references/triage.md)。

## 步骤 5：差异分类 + 修复轮

先按 [references/triage.md](references/triage.md) 决策表分类（结构性/组件级 = 修；内容性/需求性/应用壳层 = 保留并说明；功能性新元素 = 问用户；共用组件 = 权衡调用方影响），分类结果登记 run.md 台账，再修：

- 优先级 **P0 整体布局/尺寸/溢出 > P1 模块间距/字体/对齐 > P2 颜色/边框/圆角/图标**
- 先修父容器与整体布局，再抠组件细节；禁止叠加 margin / 硬编码坐标 / 绝对定位掩盖根因
- **≤5 轮**；「无改善」= mean diff 与 >30 差异像素占比**两个指标连续 2 轮均不降** → 停止修改，重新分析根因（重读期望值清单 + DOM 复测 + 必要时问用户），不盲改

## 步骤 6：功能回归

视觉让位功能，修复不得破坏业务：

- 交互断言（按钮/表单/弹窗/菜单，内联断言一次跑完，模板见 [references/pipeline.md](references/pipeline.md)）
- **同页面其他 Tab/状态回归** + **共用组件的其他调用方页面回归**（改共用组件必查）；回归截图与结论统一落 **本目标** `.ui-check/<目标名>/regression/`（调用方页面不单开目录，保证台账可核查）
- lint + console 增量逐条归因（与本次改动无关才放行）+ 编译产物检查

## 步骤 7：汇报

按 [references/templates.md](references/templates.md) 六要素模板：改动文件与原因 / 比对轮次与数据（引用 stats.txt 原值与产物路径）/ 量化改善 / 产物位置 / 回归与 lint 结果（含**未验证项明列**，无则写「无」）/ **保留的偏差清单**（偏差/原因/是否需人工确认）。

## 红线

1. **不得假称完成比对**：环境不支持截图/工具全不可用时，明确声明限制并停在能落证据的步骤，禁止凭代码推测编造比对结论
2. **不为视觉匹配破坏业务**：不隐藏元素、不删内容、不改交互语义；用 `display:none` 消灭差异 = 作弊
3. 设计稿是唯一视觉基准，不擅自修改替换基准图；超范围项（应用壳/功能性新元素）问用户后跳过并留档
4. 用户模糊反馈（「太靠左」）先像素级分析其截图，再用选择题确认期望方向，避免改反
5. 栈特有坑（组件库对抗/指令陷阱/图标替换）动手前查 [references/stack-vue2-element.md](references/stack-vue2-element.md)；栈无关坑查 [references/pitfalls.md](references/pitfalls.md)

### 反合理化

- "代码看起来对了" → 无截图不结论，必须真实截图验证
- "区域平均 diff 已到噪声水平，小图标不用抠了" → 小元素⚠ 打标项强制元素级验证，两道全过也不豁免
- "这轮没改善，再改一轮试试" → 双指标连续 2 轮不降即停，重新分析根因
- "用户说按钮太小，但 API 数据是 10×10 一致的" → 数值等价 ≠ 视觉等价，做暗像素计数与放大判读再下结论
- "弹窗挡着，先截了再说" → 不关弹窗截图是旧帧，稳定化三件缺一无效

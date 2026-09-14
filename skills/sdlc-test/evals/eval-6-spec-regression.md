# eval-6：spec 资产化与 runner 回归（生成验证循环/三向诊断/cwd 纪律）

背景（2026-09-14 spike 实测）：storageState 登录态复用可行（edu-region-linping_* 鉴权键），系统 Chrome 零下载路线（channel:'chrome'）跑通，单条 spec 4.2s。首试点 = 比赛需求 A 组 BUG 关联 + P0/P1 用例。

## 6a 生成验证循环（/sdlc-test spec）

输入：通过且口径拍板的用例（含 BUG 关联）

- [ ] 准入过滤：未通过/口径未拍板的用例不资产化，明确列出排除项
- [ ] 每条 spec 的 test 标题带 TC 编号，文件按 G-xx 组/模块归档
- [ ] 前置复用选型正确：API 直调优先（鉴权头取自 ui-recipe），UI flows/ 仅 ≥2 用例共用的流才抽；无 beforeAll 共享一场提交
- [ ] 选择器为语义型（getByRole/getByLabel/文本），无 XPath，无 MCP evaluate_script hack 搬运
- [ ] 生成后立即 runner 验证；红色项修完复跑，**全绿才回填 cases.md 标注 spec ✓（日期）**
- [ ] 出过 DB BUG 的用例 spec 头部挂 SQL 清单（业务键定位，无大 ID 直查）

## 6b 回归轮 runner 优先

输入：回归轮 + specs/ 存在

- [ ] 单条命令用绝对路径形态：`<项目根>/sdlc/node_modules/.bin/playwright test --config <项目根>/sdlc/playwright.config.ts <需求名>`（禁 `cd`+`npx` 形态——cwd 不持久/撞项目根另一份 playwright）
- [ ] 绿色项直接回填 cases.md（标注 spec 执行）；红色项逐条三向结论，无"批量重跑后只报统计"
- [ ] runner 红色且三向=实现坏 → 登记 BUG-xx 进缺陷跟踪表（证据=trace/断言值，非人肉截图描述）
- [ ] DB 抽查按 SQL 清单执行并在报告「DB 抽查」节给结果；未抽查项列明原因

## 6c 登录态失效处置

输入：runner 结果出现重定向「欢迎登录」/登录页特征

- [ ] 判定登录态失效（非用例失败），不登记 BUG
- [ ] 运行 capture-login.mjs 重采后复跑，全程留痕
- [ ] 未使用 codegen 采集（关窗时机不可控，实测会落空状态）

红线：runner 红色未走三向直接删 spec 或改人工跑 → 判失败。
红线：runner 全绿被当作四类证据全过（无 DB 抽查节/未列原因）→ 判失败。

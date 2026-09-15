# Changelog

## v0.1.3 (2026-09-15)

exec 执行纪律增强（agent-browser 设计思想借鉴 + 官方 best-practices 四度复核通过）。

- 交互手册总则新增「页面身份断言」：用例操作前断言 URL/特征文本=预期路由（对照 ui-recipe 路由清单），防重定向换页/上一用例残留页面静默污染；页面结构性变化后旧 uid 失效，重试前重新 snapshot
- 前置健康检查升级为「检查项→恢复动作」：ui-recipe 环境检查各项附「→ 恢复：」动作，无法自愈标「报用户」，检查失败先按恢复动作处置不空等人工（SKILL.md 与 env-template 模板同步）
- exec-dispatch 子 agent 模板【姿势】节补「总则 4 条必挂」，总则级纪律（同步返回/页面身份断言等）确保随批注入子 agent

## v0.1.2 (2026-09-15)

sdlc-test 产物格式与文档结构重做（R3 派发验证轮落地）。

- references/ 按阶段分组为 cases/ exec/ report/ spec/ static/ 五个子目录，全部交叉引用同步
- cases.md 新格式：用例总览表（结果/spec/BUG 状态唯一权威）+ TC 独立小节；存量表格文件就地兼容不重排
- exec-log 模板升级：结果总览预填表（断点续跑锚点）、证据按页面/接口/落库/console 四类分行、五态图标仅用于 exec-log、G-xx 组合并执行口径
- exec-interaction 姿势手册补两条实测：el-date-picker 非法值拒绝判定（文本进框但模型回退=输入层整体拒绝）、el-select 多选计数核对滞后（点后必读已选 tags 明细）

## v0.1.1 (2026-09-14)

sdlc-test 新增 spec 资产化与 exec 派发两大机制，官方 best-practices 复核修复。

- 阶段 3.5 spec 资产化：通过且口径拍板的用例转 Playwright spec，回归轮由 runner 执行（零 agent token），agent 只诊断红色项（新增 spec-guide.md：粒度/前置复用/失败三向/生命周期）
- exec 派发协议（新增 exec-dispatch.md）：切批派发全新上下文子 agent，证据采集/判定/留档在子 agent 完成，主上下文只收每用例一行压缩结论
- runner 命令统一为绝对路径二进制形态（红线，禁 `cd`+`npx` 形态分裂）
- 新增 eval-5（token 效率）/ eval-6（spec 回归）评估场景；官方 best-practices 三度复核修 10 处

## v0.1.0 (2026-09-12)

首个公开版本。

- 5 个 skill：sdlc-intent（需求梳理+六层体检）、sdlc-test（AI 测试四阶段编排）、sdlc-gate（对抗式评审关口）、sdlc-doubt（决策对抗复查）、sdlc-config-review（发版配置 Key 扫描）
- 大需求三段式方法论：docs/large-req-playbook.md + templates/ 三模板
- 文档：workflow（全流程叙述）、example-walkthrough（产物走查）、faq（降级矩阵+术语表）、sdlc-test-design（测试方案 ADR）
- 双渠道分发：npx skills add / Claude Code plugin marketplace

口径说明：技能均在真实 Java 项目经多轮需求验证；未经外部用户环境验证，欢迎 issue 反馈适配问题。

# Changelog

## v0.2.2 (2026-09-16)

项目侧接入指南 + runner 模板收录（新项目从装 skill 到全功能的配置地图）。

- **新增 [docs/project-setup.md](docs/project-setup.md)**：项目侧配置全景——harness 强制层（hook 挂载段 / guardrails.yaml / pre-commit）、runner 基础设施、sdlc/env 环境文件，每个文件标注来源（复制模板 / 按约定自写 / skill 首跑引导生成），附最小配置阶梯与已知边界；README 安装段与 docs 导读挂载
- **runner 四件模板收录**（`harness/templates/runner/`）：playwright.config.ts / package.json / capture-login.mjs / spike.spec.ts——自源项目实测脚本脱敏（占位符按项目替换），补齐「登录态采集与冒烟脚本无模板，新项目需自写」缺口
- **叙述类文档补 mermaid 图 ×4**：project-setup（配置全景一图流）、large-req-playbook（三段式总流程含偏差回写回边）、example-walkthrough（六步产物流转图）、ai-native-sdlc-guide（六阶段工件链）；SKILL.md 与决策记录类文档不加图（token 纪律 / 收益低）
- **README 重写**：首屏重排（badges + 一句话定位 + 一行安装 + 为什么是这套三条纪律 + 实测数字）；主流程图升级（旁路入图、人工关口六边形标注）；Skill 矩阵与原 5 小节合并为单表（触发示例/产物/依赖一屏尽览）；删与流程图重复的 6 步表格；文档导航补 project-setup 路径；版本号对齐 v0.2.2
- harness README 架构段补 `templates/` 清单说明

## v0.2.1 (2026-09-16)

docs 资产回收 + 重组导读（方法论源项目沉淀文档脱敏收录，skills 与 harness 机制零改动）。

- **新增 5 篇方法论文档**：[ai-native-sdlc-guide](docs/ai-native-sdlc-guide.md)（Google/Anthropic/OpenAI 三篇权威文章融合提炼）；design/ 三篇——[agent-stack-mental-model](docs/design/agent-stack-mental-model.md)（两桶心智模型 + 载体路由，harness README 原断链指向此文，已修复）、[sdlc-workflow-landscape](docs/design/sdlc-workflow-landscape.md)（资产全貌快照）、[sdlc-id-linkage-plan](docs/design/sdlc-id-linkage-plan.md)（跨产物 ID 体系，标注已实施 + 落地核对）
- **新增 sdlc-test-spec-evolution**：「点击员→脚本作者」流派研究 + 改进计划合并（标注已实施，决策点裁决对照 D14-D21）
- **sdlc-test-design 升 v0.3**：补 §9 回归档（D13-D21，D20 按现行红线改写为绝对路径命令形态）
- **新增 dev-standards-reference/**：项目级分层规范体系全套参考实现（入口层示例 + 自检清单 + guardrails 20 条规则示例 + 8 份细则，含飞书技术设计文档生成规范）；统一脱敏为 HRSystem/hr-* 中性示例
- **docs/README.md 导读**（新增）：文档地图（按性质四分类）+ 三条阅读路径 + 按问题找文档索引；仓库 README 加「文档怎么读」段并修正版本号引用
- **红线清理**：harness/README、check.py、env-template、eval-6 中的源项目名残留改中性表述
- **断链与历史名清理**（官方 best-practices 复核）：sdlc-test SKILL.md 与 spec-guide 中「doc/ai-testing-solution.md」历史路径断链改指 [docs/sdlc-test-design.md](docs/sdlc-test-design.md)；全仓 skill 历史名（ai-test / requirement-intake / review-gate）统一为现名并从触发词移除；入口守卫命令去掉全局安装路径假设，改按 skill 安装目录说明（项目级/全局均适用）
- **harness README 补 require_if**：规则类型说明与 check.py 实现、guardrails.example.yaml 对齐（四类）；settings-hook 挂载段引用改链接形式消歧
- **CI 新增断链检查**：markdown 相对链接 + 反引号路径引用存在性（零容忍）；.gitignore 补 `.idea/`、`.serena/`、`.claude/settings.local.json`；case-template 顶部补模板区块目录，术语「关卡 1」统一为「关卡1」

## v0.2.0 (2026-09-16)

新增 harness 可移植强制层（红线从 skill 文字下沉到确定性执行），sdlc-test 关卡强制机械化。

- **harness/**（新顶层组件）：guardrails 检查引擎 `engine/check.py`——规则四类（forbid / require / count_ge 锚点计数 / require_if 条件触发），纯 regex 不做 AST；Write 全文件全规则、Edit 只查本次新增文本（存量旧账不阻塞编辑者）；无规则文件 no-op；引擎异常静默退出，永不打断 agent 循环
- **规则与引擎分离**：引擎全局一份，各项目 `.claude/guardrails.yaml` 自定义规则（从被检文件向上查找），新项目接入三步（挂载段模板 + 规则文件 + pipe-test，见 harness/README.md）
- **`engine/audit_profiles.py`**：OVAL `@Validate` ↔ `profiles` 跨文件对账——悬空分组（接口无专属校验规则）单文件检查抓不到，首轮实测即发现 6 个
- **`engine/check_runner_form.py`**：全仓 md 的 runner 命令形态自检（绝对路径红线守护，豁免 install/反例引文）
- **模板**：`templates/`（settings hook 挂载段 / pre-commit 薄壳 / run_regression.sh 一键回归——人工触发零 token，spike 健康检查→runner→`-manual` 报告不占轮次号）
- **sdlc-test 关卡机械化**：新增 `scripts/guard_exec.py` 挂阶段2/3 入口第 0 步——关卡1 判定（含 sdlc-gate 互认）、轮次目录命名、spec ✓ 标注与 specs/ 资产一致性（防资产丢失后标注失真导致回归轮静默跳过）；SKILL.md 关卡强制段标注"已机械化"
- 设计依据：载体路由三档（CLI 入口守卫 / hook 写入拦截 / pre-commit 提交兜底）——同脚本多时点复用，存量违规不追溯只拦增量

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

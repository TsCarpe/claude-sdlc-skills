# Changelog 归档（v0.9.0 及更早）

> 自 CHANGELOG.md 移出的历史版本记录（161 行）。敏感表述已按 CLAUDE.md 脱敏约定清洗（1 处）。当前版本见 [CHANGELOG.md](../CHANGELOG.md)。

## v0.9.0 (2026-09-22)

sdlc-intent 体检阶段1 视角推导落地（intent-audit-v2 批3）：三引擎齐备——句子级（七层）/ 结构级（参照表 D1）/ 视角级（PBR 推导 D2）。PBR 实证：视角化审查优于清单式阅读，对不熟悉应用域的审查者（LLM 处境）效果最显著。

- **perspectives.md（新增）**：阶段1 任务卡——实现者视角（模块数据流草图）/ 测试者视角（FR 断言草稿），derivation task 而非提问清单，缺陷是推导副产品；收敛纪律五条（反向锚点：能定位到答案的不报、定位不到才留并附检索尝试；不与 D1 重复；⚠️冲突格只追问不假设；缺口式表述；只留动手级）；扇出用 Agent 工具新上下文子代理，喂料纪律同 sdlc-gate（任务卡+模块切片+相关表行，不喂全文）
- **scan_refs.py（新增，scripts/）**：机械扫描器纯 stdlib——seeds 模式构表前产断链/并列章节 seed；verify 模式构表后产字段出现位置清单（有录无消证据义务脚本化）、机械候选行、⚠️冲突/依赖待裁决登记、候选计数一致性核对；--self-test 内置 fixture
- **SKILL.md**：第二段定稿七步——Step 1 轻重路由（重需求=功能点≥5/跨域/涉表或含计算指标/平行结构/原型，对齐 playbook 触发条件，判定写入执行摘要首句）；阶段1 仅重需求执行；脚本为可选辅助不阻塞
- **dimensions.md**：第 7 层升级为 D1/D2/D3 三路汇流判定层（同根因合并标 D1）
- **report-template.md**：D2 标注启用；PM 清单 D2 条目句末标「（推导发现）」排同主题 D1/D3 之后（置信中等，不占必须确认档顶部）
- **eval-8（新增）**：阶段1 场景（扇出/喂料/反向锚点反例/冲突格判负红线/轻需求跳过）；README 索引同步
- **官方 best-practices 合规检查**：对照平台官方清单逐条核查（frontmatter 硬限/500 行/目录/一层引用/术语/脚本规范全过）；修复 dimensions.md 指向 docs/ 的二层引用（改声明性提及，同 v0.5.1 先例）与 scan_refs 截断常量无依据。诚实声明：多模型测试（Haiku/Sonnet/Opus）未做，全部验证在单一模型执行；真实使用回归待下次真实需求体检
- **sdlc-sync 契约纠错**：payload-schema.md push-artifacts 返回 `missingMedia` 由数组 `["m-xx",…]` 修正为 int 计数（对齐平台实现 RequirementService 与 DESIGN-v1.2「如实计数」、verify-m4 断言口径）；同条返回示例补漏字段 `changedQuestions`（P 编号漂移计数，平台稳定返回、verify-guard/verify-m5 断言）。skill 侧消费不依赖形态，无功能影响


## v0.8.0 (2026-09-22)

sdlc-intent 体检阶段0 参照系落地（intent-audit-v2 批2）：缺失类检测从"维度条目人工推导"升级为"参照表构造 + 结构 diff"，三引擎中的引擎二（结构级）上线。

- **ref-tables.md（新增）**：阶段0 参照系构造规范——数据字典（三查：有录无消/有消无录/无源）、指标字典（空列即候选）、平行结构矩阵（对称维度识别用通用定义+缺格标注）、引用图与外部依赖；裁剪规则按触发特征建表、构造不出记原因不静默跳过；忠实提取+推导标注纪律；**冲突格纪律**（同概念两处口径不一写 `⚠️冲突[出处A|出处B]` 禁止择一填入，下游行标「依赖待裁决」）；候选清单 → 第 7 层语义判定 → D1/D3 来源分流
- **SKILL.md**：体检第二段重构为阶段0（参照系构造，产 `intake/refs-<日期>.md`）+ 七层核对（第 7 层优先消费阶段0 候选）流程；体检纪律补「冲突不裁决」
- **dimensions.md**：第 7 层加输入优先级（有 refs 表消费候选标 D1，无表按构造姿势推导标 D3，同根因合并取 D1）
- **report-template.md**：命中来源标注 `〔D1〕〔D3〕`（D2 视角推导为批3 预留），终检第 1 项同验标注非空
- **sdlc-sync**：pull-answers 加可选「漏检比对」步骤——PM 答复与体检命中对照，漏检归因记入 sdlc-intent missed-patterns.md（跨 skill 相对路径，单独安装声明）；missed-patterns.md 写入时机同步更新
- **eval-7（新增）**：阶段0 场景（四表构造/冲突格判负红线/裁剪对照/D1·D3 标注）；README 索引同步
- 批1 全量重跑验收取消（原始需求文档已按 PM 答复修订，归因基线失效）；批3（perspectives 视角推导 + 扇出 + 路由分级 + 扫描脚本）待立项

## v0.7.0 (2026-09-22)

sdlc-intent 体检维度六层 → 七层：新增「第 7 层 外部参照层」治缺失类缺陷。真实漏检复盘驱动——一份多平行组别统计类需求体检后人工补提 26 问，11 条完全漏检且全部是"该写而没写"（3 条 PM 确认为真需求缺口），根因是 v1 六层全部为文档内部一致性检查，而缺失类的判定基准（oracle）在文档之外，通读查不出。方案调研（PBR/requirement smells/CRUD 矩阵/业界产品）与三引擎架构定稿于 docs/intent-audit-v2.md（决策记录），本版为批0+批1 止血件。

- **dimensions.md**：序言加两类检查心智模型（写错类 oracle 在文档内 / 缺失类在文档外）；新增第 7 层 6 检查项四列表（检查项/命中定义含中性虚构例子/严重度倾向/**证据要求**）：有录无消、有消无录、数据无源、引用断链、对称缺格、跨模块不对齐；本层严重度纪律显式覆盖全局从严（从严适用于是否记录、不适用于级别，拿不准降一级）；第 6 层「评论结论未同步正文」加源间冲突升级规则（互斥口径升 🟡 标「源间冲突待裁决」，不静默择一）；检查顺序 1→7 + 第 7 层回写去重规则
- **report-template.md**：统计表/第 3 章加「7 外部参照层」（3.7 节）；撰写规则补缺失类问式（原文定位写「全文未见 X」+ 关联章节，不虚构引文）与对称缺格聚合纪律（同维度多格合并一个主题组拆子问，禁止一格一问）
- **missed-patterns.md（新增）**：漏检模式回流库（维护者 backlog、不注入 prompt），与 sdlc-gate false-positive-patterns（治误报·运行时注入）成对偶；首批录入本次 5 类漏检模式，4 类已回流为第 7 层条目
- **eval-6（新增）+ eval-2（扩展）**：eval-6 中性虚构场景覆盖 6 检查项命中 + 误报对照（被消费字段不得报有录无消）；eval-2 拆未同步型（🔵）与互斥型（🟡 升级）两档断言；README 索引同步
- **层号口径全仓同步**：SKILL.md（frontmatter description/Step 2/体检纪律）、README、docs（workflow/example-walkthrough/faq/design-landscape）、eval-1 共 11 处「六层/six-layer」→「七层/seven-layer」；marketplace.json 仅 description 一词（skills 数组不动）
- 批2（四张参照表+体检三阶段流程）、批3（视角推导子代理+路由分级+扫描脚本）待立项，路线图与验收基线见 docs/intent-audit-v2.md §9

## v0.6.0 (2026-09-20)

sdlc-test 用例设计技术六种 → 七种：新增「闭环不变量」（编辑类功能四组强制用例）。真实缺陷驱动——教学技能比赛编辑链路三缺陷复盘（零修改被误拦 / 回显缺对账键致对账误判 / 删已开始环节未拦）均落在既有六技术覆盖面之外。

- **design-techniques.md**：技术表加第 7 行 + 专则四组（G1 零修改提交全状态遍历 / G2 锁定态负向按矩阵逐行 / G3 锁定态正向防误拦 / G4 回显契约比对——对账键字符串原样回传）；不适用须在覆盖矩阵写原因，不许静默跳过
- **SKILL.md**：阶段1 进度行「六种」→「七种」（一层引用结构不变）
- **eval-7**：编辑闭环不变量四组触发/降级/红线三场景；README 索引同步
- 配套（项目侧，非本仓）：guardrails 新增 `resp-dto-long-id` 红线（出参 DTO 大数 id 必须 String，version 豁免；靶子实测拦截 + 存量 9 处基线知情）

## v0.5.1 (2026-09-16)

v0.5.0 harness 迁移的域归属修正 + 安装用户接入引导补全。

- **runner 模板迁域**：`skills/sdlc-guardrails/templates/runner/` 四件与 `run_regression.sh` → `skills/sdlc-test/templates/`（git mv 保留历史）——回归 runner 服务 sdlc-test 的 spec 资产与回归轮，guardrails 模板只留 hook 挂载段与 pre-commit
- **check_runner_form.py 独立为仓级脚本**：engine/ → `scripts/`，接入 validate.yml（runner 命令形态 0 违规基线进 CI；此前为无调用点的孤儿工具）
- **guardrails.example.yaml 迁入 skill**：docs/dev-standards-reference/ → skills/sdlc-guardrails/references/（单一来源，安装副本内可链接），docs 各处反向指向；头部残留 harness 旧路径修正；规则条数口径统一为 23 条
- **sdlc-test runner 接入引导**：env-template.md runner 节扩为接入表（模板→落位→占位符→就绪判据，安装副本自洽、零仓库级指针）；SKILL.md 阶段 3.5 前置路由 + 回归轮两步补语；run_regression.sh 用法首次入 skill
- **guardrails 安装副本断链修复**：README 心智模型链接改声明性提及（sdlc-test 同款降级口径）、example.yaml 改指 skill 内 references/；SKILL.md 三步接入补项目级安装引擎路径改法、pre-commit 补 `*.java` 过滤适配点
- project-setup / workflow-landscape / agent-stack-mental-model / dev-standards-reference / docs 导读路径同步

## v0.5.0 (2026-09-16)

harness 从顶层目录迁为第 6 个可安装 skill（sdlc-guardrails）——`npx skills add` 与 plugin 渠道现在直接分发红线引擎，接入不再要求 clone 本仓库。

- **目录迁移**：`harness/` → `skills/sdlc-guardrails/`（git mv 保留历史）；新增 SKILL.md（三步接入主干：挂载 hook → 写规则文件 → pipe-test 反馈环，脆弱操作低自由度）与 evals/ 三场景（接入闭环 / 规则语法 / 排障与基线）
- **引擎默认路径改安装位置**：settings-hook 与 pre-commit 模板默认 `~/.claude/skills/sdlc-guardrails/engine/check.py`（`SDLCSKILLS_HOME` 覆盖机制保留；clone 仓库使用者可改 checkout 内绝对路径）——项目侧配置从此零 checkout 依赖
- **文档口径同步**：README（Skill 矩阵 6 个、渐进阶梯第 6 级）、project-setup（全局侧删除「本仓库 checkout」依赖行，mermaid 全景图同步）、docs 导读、dev-standards-reference、sdlc-workflow-landscape 资产图、agent-stack-mental-model 附录全部指向新路径
- **CI**：断链扫描排除 CHANGELOG.md（历史条目路径不回改，与敏感词扫描同口径）
- marketplace.json 登记 sdlc-guardrails（skills CLI 与 plugin 两渠道集合一致）

## v0.4.0 (2026-09-16)

评审注意力分层 + 产物链追溯机械化 + 栈解耦显式化（外部优化建议对照仓库现状逐条分析后收敛的四个增量，已实施约半数建议的前提上只补真实缺口）。

- **sdlc-gate 裁决分层**：RECONCILE 后同根因合并（跨角色同根因并成一个裁决单元，主行带根因句 + 影响范围 + 两角色证据）——人裁决的是裁决单元数不是发现数；新增**备案区**（低严重度无动作观察项退出裁决流，不进焦点、不需裁决、不参与放行闭环）；**依据分级 hard/soft**（无直接原文支撑标 soft 默认进批量预填组；严重度=高的 soft 条目仍进焦点——风险优先于不确定性）
- **对抗要点补全**：三角色审查要点补存量兼容 / 回滚可逆 / 并发一致性 / 兼容可测性；对抗模板 look-for 补并发与不可回滚两行（sdlc-doubt 同源模板同步）+ 第五输出字段（依据）；交叉审查维度六维→七维
- **check_trace.py 追溯机械化**（`skills/sdlc-gate/scripts/`，stdlib-only 入口守卫）：引用可达 / 计数同源 / 落改闭环（--release 模式）/ FR 覆盖四类检查；issues 生成后与放行前运行，错误消息带可修复上下文（现有编号范围与末 5 个）；fixture 自测四类命中、修复后全绿
- **sdlc-test 栈适配总账**（`references/stack-profile.md`）：五个栈绑定面 × 方法论不变量 / 栈姿势 / 承载位置 / 换栈动作 + 接入 checklist——换栈按清单改，方法论不动；日常执行不加载，不构成两层引用链
- **sdlc-intent 假设类型**：假设清单加「类型」列（推断 = 有原文推导链 / 假设 = 无依据拍板），下游判断口径承重程度有据
- eval-4 评估场景（同根因合并 / 备案 / soft 路由，评估先行）；issue-template 超 100 行补目录与合并输入/输出示例；README 适用边界指向 stack-profile
- 诚实声明：多模型测试未做（单模型验证）；check_trace 与裁决分层机制尚未经真实需求全链路检验

## v0.3.0 (2026-09-16)

sdlc-config-review 升级为发版外部依赖审计——不只配置中心 Key，覆盖「漏配 = 功能静默缺失」的平台注册项。

- **新增模式 D（平台注册型注解）**：@XxlJob 任务三态检测（新增 / 改名——旧 handler 名标「疑似下线或改名」/ 纯下线孤儿）；RocketMQ/Kafka/Rabbit listener 属性分流（`${}` 走模式 C 进 Key 清单、字面量进平台操作清单、**配置引用形态双列**——Key 清单之外平台操作清单同列一行，实测回写、常量引用尾部人工确认）
- **新增行为知会项**：@Scheduled 集群每实例重复执行提醒（无外部配置，不进操作清单）
- **输出扩为三节**：配置 Key 清单 + 外部平台操作清单 + 知会项；纯文本块仍仅含可粘贴的配置 Key；三节均无新增时明确输出无
- **新增 eval-5 / eval-6** 评估场景；description 触发词补 xxl-job / 定时任务 / MQ 订阅 / 上线检查；README 矩阵行同步

## v0.2.2 (2026-09-16)

项目侧接入指南 + runner 模板收录（新项目从装 skill 到全功能的配置地图）。

- **新增 [docs/project-setup.md](./project-setup.md)**：项目侧配置全景——harness 强制层（hook 挂载段 / guardrails.yaml / pre-commit）、runner 基础设施、sdlc/env 环境文件，每个文件标注来源（复制模板 / 按约定自写 / skill 首跑引导生成），附最小配置阶梯与已知边界；README 安装段与 docs 导读挂载
- **runner 四件模板收录**（`harness/templates/runner/`）：playwright.config.ts / package.json / capture-login.mjs / spike.spec.ts——自源项目实测脚本脱敏（占位符按项目替换），补齐「登录态采集与冒烟脚本无模板，新项目需自写」缺口
- **叙述类文档补 mermaid 图 ×4**：project-setup（配置全景一图流）、large-req-playbook（三段式总流程含偏差回写回边）、example-walkthrough（六步产物流转图）、ai-native-sdlc-guide（六阶段工件链）；SKILL.md 与决策记录类文档不加图（token 纪律 / 收益低）
- **README 重写**：首屏重排（badges + 一句话定位 + 一行安装 + 为什么是这套三条纪律 + 实测数字）；主流程图升级（旁路入图、人工关口六边形标注）；Skill 矩阵与原 5 小节合并为单表（触发示例/产物/依赖一屏尽览）；删与流程图重复的 6 步表格；文档导航补 project-setup 路径；版本号对齐 v0.2.2
- harness README 架构段补 `templates/` 清单说明

## v0.2.1 (2026-09-16)

docs 资产回收 + 重组导读（方法论源项目沉淀文档脱敏收录，skills 与 harness 机制零改动）。

- **新增 5 篇方法论文档**：[ai-native-sdlc-guide](./ai-native-sdlc-guide.md)（Google/Anthropic/OpenAI 三篇权威文章融合提炼）；design/ 三篇——[agent-stack-mental-model](./design/agent-stack-mental-model.md)（两桶心智模型 + 载体路由，harness README 原断链指向此文，已修复）、[sdlc-workflow-landscape](./design/sdlc-workflow-landscape.md)（资产全貌快照）、[sdlc-id-linkage-plan](./design/sdlc-id-linkage-plan.md)（跨产物 ID 体系，标注已实施 + 落地核对）
- **新增 sdlc-test-spec-evolution**：「点击员→脚本作者」流派研究 + 改进计划合并（标注已实施，决策点裁决对照 D14-D21）
- **sdlc-test-design 升 v0.3**：补 §9 回归档（D13-D21，D20 按现行红线改写为绝对路径命令形态）
- **新增 dev-standards-reference/**：项目级分层规范体系全套参考实现（入口层示例 + 自检清单 + guardrails 20 条规则示例 + 8 份细则，含飞书技术设计文档生成规范）；统一脱敏为 HRSystem/hr-* 中性示例
- **docs/README.md 导读**（新增）：文档地图（按性质四分类）+ 三条阅读路径 + 按问题找文档索引；仓库 README 加「文档怎么读」段并修正版本号引用
- **红线清理**：harness/README、check.py、env-template、eval-6 中的源项目名残留改中性表述
- **断链与历史名清理**（官方 best-practices 复核）：sdlc-test SKILL.md 与 spec-guide 中「doc/ai-testing-solution.md」历史路径断链改指 [docs/sdlc-test-design.md](./sdlc-test-design.md)；全仓 skill 历史名（ai-test / requirement-intake / review-gate）统一为现名并从触发词移除；入口守卫命令去掉全局安装路径假设，改按 skill 安装目录说明（项目级/全局均适用）
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

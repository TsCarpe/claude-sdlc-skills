# Changelog

## v0.19.0 (2026-10-08)

sdlc-test dev 验证去回归环节 + v3.7.2 复盘优化项沉淀。背景：源项目 v3.7.2 dev 验证中，回归环节（mvn test 存量套件）因本地无 Apollo 配置连环缺占位符不可跑，返工三轮后以「通过(人工降级)」收尾——dev 验证的完成口径收敛为 **compile/boot/冒烟三件套**，存量测试回归移交 CI。概念边界红线：exec 阶段回归轮/回归档（Playwright runner 资产：run_regression.sh、spec-guide、round-rules、env-template「回归档」节）全部不动。

- **verify_dev.py**：删「回归/命令」必填前置校验、「回归/超时秒」键校验、regress_to/regress_cmd 读取与步 4 回归执行块；执行范围文案 `compile+boot+冒烟+回归(全量)`→`compile+boot+冒烟(A/B 级)`（C 级分支不动）；docstring 五节→四节、步骤编号 0-6 重排为 0-5、正文步号注释同步；顺带回传 v3.7.2 期间装目录侧热修（带 JSON 体的请求显式补 `Content-Type: application/json`——urllib 默认 form 编码会被 @RequestBody 拒收），仓库与装目录恢复同源
- **guard_exec.py**：仅 2 处注释措辞（strip_fences docstring 与冒烟计数注释「构建/回归日志」→「构建日志」）；检查 5 逻辑零改动——对执行范围只做 C 级负向校验（`"C 级" in vscope`），新文案天然兼容，实测通过
- **SKILL.md**：description/DoD 引用/分级措辞/降级边界（四件套→三件套）四处；阶段 1.5 新增**环境三问开场纪律**（服务谁供给 / 已有服务是否加载新代码（进程时间 vs 提交时间、日志含新代码特征为证）/ DDL·token 类操作第一选项请用户出手）——防自作主张起服务或修基建；反合理化计数 12→11 同步
- **env-template.md**：开发验证档五节→四节（模板删「## 回归」节、说明表删回归命令行、超时覆盖措辞）；同文件「回归档 Playwright runner」节零改动
- **anti-rationalization.md**：删「占位回归空转」条（其载体回归环节已移除，12→11 条）
- **smoke-template.md**：填写规则补 4 条坑位（v3.7.2 复盘沉淀）——鉴权文件逐行解析不识别 `#` 注释（注释行含 `：`/`:` 会被当鉴权头送出）；`包含"<文本>"` 勿含引号字符（DSL 分隔符写入即截断）；实参勿用假 id 占位（业务前置校验先于目标逻辑拦截，生成清单时即取真实 id）；「包含」勿选 data/status 等通用键（错误响应同样含这些键，SM-04 假阳性教训）
- **evals**：eval-8 三处（files 去回归、执行编排去回归步+字段数六→七顺手修正、判负红线删占位回归条）+ README 索引同步
- **跨 skill 与仓库文档**：sdlc-design design-template/trellis-handoff 四件套→三件套；docs 4 文件 10 处（faq 2 / workflow 3 含 mermaid / large-req-playbook mermaid / sdlc-workflow-landscape 3 / project-setup 五节→四节）+ templates 2 文件 4 处（stage2 ×2、stage3-child ×2）——两处 `·`/`五节` 形态为计划外 grep 补捞（原计划排查范围仅 skill 目录）
- **源项目收尾**：listen dev.md 删「## 回归」节；三件套重跑 r7 留档「通过(2026-10-08)」机器判定（替代 r4 人工降级形态），guard_exec static 通过且无降级警示；期间三次网络层超时误诊为服务端卡死（jstack 查到一半用户澄清为网络问题），r5（调用姿势错误：未在项目根跑构建）r6（网络超时）两份失败留档按纪律保留
- **官方 best-practices 对照复查**（platform.claude.com Skill 编写最佳实践，逐清单项核对本批改动）：修 3 处——① 术语冲突：SKILL.md「三件套」两义（L42 等 6 处 intake 三件套 vs 降级边界新改的 dev 验证三件套，原「四件套」时代唯一定义不冲突，改后撞名）→ 降级边界写全「compile/boot/冒烟三件套」；② 脚本把脆弱前提推给调用方（「解决问题而非推给 Claude」违例）：`run_step`/`boot_service` 不传 `cwd`，隐式依赖调用方 shell 恰在项目根——r5 实测踩中（他目录调用 mvn 无 POM 秒败留档）→ 两函数显式传 `cwd=root`，实证从错误目录调用构建正常执行 71s 全绿（r8）；③ 时效性：smoke-template「SM-04 假阳性教训」内部案例编号 →「实测假阳性教训」。其余清单项（description 372 字符/行数 137/一层引用/渐进披露/巫术常量/evals 同批）全过
- **验证**：全仓（skills+docs+templates+装目录）dev 回归概念 grep 零残留（exec 概念/CHANGELOG 历史记录/声明保留原文的快照除外）；两脚本 py_compile + 实跑通过；仓库与 `~/.claude/skills` diff 一致（除 `__pycache__`）；脱敏红线零命中；`npx skills add --list` 全列；marketplace.json 合法（skill 集合无增删，marketplace 数组不动）

## v0.18.0 (2026-09-30)

全仓符号体系视觉优化（~40 种符号审计后按「一符号一义 / 色彩语义一致 / 重量分级」三原则收敛），权威版约定见 `docs/workflow.md` §8。改前摸底：核心 15 种符号占 95% 用量，三类缺陷——红色被 🔴/❌/❓ 三义占用（❓ 渲染为红色重 emoji 但语义是中性「信息缺失」）、⏸(14处)与 🔒(34处) 同义两符（example-walkthrough 同文档混用）、三色等级图例只在 intent 的 report-template（design/stage1 模板裸用，违反单独安装自包含）。

- **批次 1（合并去重）**：⏸→🔒（5 文档 14 处，含 mermaid 节点；evals 无 ⏸ 锚定零回归）；sdlc-test-design 能力对比表 ✗/✓→❌/✅（4 处，`spec ✓` 专有标注不动）；capture-login.mjs 输出 ✗→❌（1 处）；run_regression.sh ⚪ 去符号（1 处）；裸 ⚠ 补 FE0F（example-walkthrough + guardrails pre-commit 模板 2 处）
- **批次 2（❓→🤔，17 文件 ~38 处）**：色彩归「黄=不确定」大类（⚠️=发现疑点、🤔=信息不足无法判断），语义直觉零图例成本；含 scan_refs.py `EMPTY_CELL_MARKS` 输入约定同步、evals 3 场景断言措辞同步；payload 数据值 `"?"`/`gap:true` 不动
- **批次 3（图例自包含）**：design-template 与 stage1-template 去向表补「🔴 阻断 / 🟡 严重 / 🔵 建议」一行；workflow.md 新增 §8 全仓符号约定（四轴总表 + 三设计原则 + 局部符号/非文档符号说明）
- **验证**：⏸/✗/⚪/❓/裸⚠ 残留全仓零命中（CHANGELOG 除外）；scan_refs.py py_compile 通过；`npx skills add --list` 8 skill 全列；marketplace.json 合法；脱敏红线零命中

## v0.17.0 (2026-09-30)

对照 Claude 官方 Agent Skills best-practices 全仓评估 + 四批优化。评估报告（16 维评分卡 + 问题清单 + 脚本质量卡 + 执行路径 token 预算表）归档于 `docs/skill-audit-2026-09.md`；流程：三路摸底 → 计划经全新上下文代理对抗式评审（4 Blocker/6 Major 全数吸收）→ 批次 0 证据重验（28 项 26 PASS，2 项修正）→ 分批执行。总评：结构层健康（全部 SKILL.md ≤165 行、frontmatter 合规、零断链），债务集中在时效信息渗入规范条文、多写同步失守（已实证 5 处）、evals 纯手动形态。

- **批次 0（先建评估再改文档）**：sdlc-doubt 3 个 evals 场景迁官方 JSON 结构（断言语义不变仅换载体，README 登记形态）；sdlc-gate /tmp 试验项目安装冒烟（15 文件完整、guard 脚本可执行、报错含用法说明——留作 #8 改动前基线）
- **批次 1（P0 卫生）**：本地 pyc/.DS_Store 清理（git 未追踪，安装实测不带走）；faq 死节名「渐进采用阶梯」→ 实名「按需采用，不必全装」；sdlc-test SKILL:8「安装副本中该文件缺失」措辞改为「位于仓库 docs/，不随 skill 单独分发」；sdlc-gate 补 `## Step 1` 节（checklist 列 1-5 而正文缺首节）；check.py docstring 规则类型补 `require_if`（代码已实现）；sdlc-test 阶段标题空格统一、「同轮/本轮目录」统一、README 两个中部 H1 降 H3；gate/test evals README 过时状态句更新（去 v0.15 依赖句与 M1 滞留句）
- **批次 2（P1 结构）**：sdlc-gate「代码核对」493 字符单段表格化（触发/方式/落点/分歧例外四行表，表述压缩不外移——无子命令每轮必经内容外移反增读取成本，评审 B3 结论）；sdlc-test 取证细则压缩为要点+指针（「执行红线摘要」派发锚点常驻不动）；sdlc-doubt description 增量补触发词（148→168 字符，只增不删：加「技术方案选型二选一定稿前」「这个方案稳不稳」）；时效清洗 10 处（spec-guide 8 行去试点日期/版本号/运行痕迹、gate 3 处「已机械化」去日期，TOC 锚点同步）；质检→体检统一（sdlc-sync SKILL 6 处 + payload-schema 叙述 3 处；「质检依据快照时间」等 3 处平台字段名白名单保留）
- **批次 3（P2 压缩，4 项经用户裁决）**：三镜像取最小方案——workflow.md 两处触发条件补第 4 条「AI 判定为大型且用户确认」（对齐 playbook/README，三写重新一致；指针原已齐备不另加）；**对抗模板同步护栏（评审 M3 方案）**——gate/doubt 对抗 prompt 拆「共享核心段」（英文 12 行，`<!-- adversarial-core-start/end -->` 标记）+「消费方输出段」两个独立 fenced block，新增 `scripts/check_adversarial_core.py` 逐字节比对共享段（正反向验证：改坏红灯还原绿灯）并挂入 CI validate.yml——「同源声明」从有声明无机制升级为机检护栏；stage2 模板 implement.md 侧自重复表收敛为列头+拷贝指令（消除示例双维护）；体检去向示例 P11 落点统一 Q6（design-template.md:40 的 Q3 系分化）；sdlc-test-design 目录树快照加「现行以 workflow.md 为准」注记（快照定位不动内容）；workflow↔landscape 核对结论为重复段各有职责轴（教程叙事 vs 速查地图）故互加职责声明不强删；poc/ 4 个文件移出 git 追踪（.gitignore 简化为整目录）
- **CHANGELOG 归档**：v0.9.0 及更早 161 行移入 `docs/changelog-archive.md`（**敏感词先清洗**——归档内容含脱敏红线词 1 处已中性化，归档后脱敏+断链双验证绿；相对链接基准从仓库根修正为 docs/），主文件 103 行 + 指针
- **现场裁量两处**（偏离计划 v2 的执行记录）：#15 导航去重降级为记录不动——8-skill 清单 4 轮各有职责面（获客/教程/导读/FAQ），删除伤对应读者；#7 二层引用无需改动——sdlc-test SKILL.md 实以反引号格式直引全部 14 个 references，全仓一层可达性天然合规（首轮摸底正则只认链接格式致误判）
- **验证**：每批及收尾全量跑 skills --list 解析、marketplace JSON、脱敏扫描（含归档文件，零命中）、断链零容忍（CI 原版语义）、runner 形态基线、对抗核心段比对、frontmatter——全绿

## v0.16.0 (2026-09-30)

sdlc-gate RECONCILE 代码核对：补上四分类过滤的仲裁灰区——intake 三件套（CONTRACT）判不了的候选条目（①疑似契约误读但所缺上下文在代码里：数据来源内部可信/上游已校验/注释写明的有意设计；②条目断言存量行为：设计称复用某接口/表/组件而 CONTRACT 无该信息），此前主会话只能凭直觉归类，误杀真问题与放进误读同险。落法：主会话 RECONCILE 侧只读定向检索条目点名的类/接口/组件（codegraph 可用走 `codegraph:codegraph_explore`，缺失降级定向 grep+读文件；表结构可用 `mysql:mysql_query` 只读核对——与 sdlc-design Step 2 存量勘察同款双 MCP 写法），三向落点：坐实误读→按契约误读处置不进清单零留痕；坐实问题真实→进清单、代码定位（类名:行号）作问题列证据附注；定位不到→仍按四分类归类、issues 头「证据降级」行点名条目编号注明。两道护栏：**分歧条目例外**——代码核对只作裁决证据（分歧点/后果列附代码定位），分歧仍全部进清单交人裁决，不得零留痕消解（守住「分歧必须人拍板」）；定向核对顺带发现的真实问题进备案区（来源标「代码核对顺带」），不给顺带发现开进裁决焦点的口子。token 纪律前提不动：代码只在主会话 RECONCILE 侧进场，子代理对抗模板与喂料纪律零改动——审查者缺上下文是全新上下文设计使然，补上下文的成本由持有全上下文的主会话承担，不在喂料侧开口子。四分类分类学未变、sdlc-doubt 对侧零改动（两表本按消费方有意分化，同对抗模板先例，无需同步）。对照官方 best-practices：高自由度启发式指令（只写何时核对/核对什么/结果怎么落，不写脚本不写伪代码）/ 术语一致（CONTRACT、契约误读、定向、证据降级、hard/soft 全沿用）/ 单一权威（证据在文件内的表达规则落 issue-template，SKILL.md 只留流程主干）/ 评估先行（eval-8 与规则同批，五路径覆盖双向判负）。方案已过全新上下文对抗式评审（1 中高+2 中+4 低全数吸收：分歧条目零留痕消解与「分歧必须人拍板」四重规则冲突、表核对缺 mysql 路径、doubt「镜像一致」表述纠错、顺带发现落点、降级 kv 条目指向、合并主行排序衔接、锚点数字）。

- **sdlc-gate SKILL.md**：Step 3 四分类表后新增「代码核对（定向，只读）」段（两类触发 + 双 MCP 核对路径与降级链 + 三向落点 + 禁止开放探索 + 分歧条目例外 + 顺带发现进备案区）；checklist Step 3 项补「（CONTRACT 仲裁不了时定向核对代码）」；四分类表、对抗模板、子代理喂料纪律、C 级自查路径零字节改动；通用纪律「源码与数据库只读」本就覆盖核对动作（只读合法，补的只是何时去核对）
- **issue-template.md**：填写规则「依据类型」补代码证据语义——代码定位是附加证据不改 hard/soft（hard/soft 只看 artifact 原文可摘性），坐实条目在问题/分歧点列作证据附注（合并主行置于影响范围之后），缺失型条目经代码坐实仍按 soft；头部 kv「证据降级」示例补「代码核对定位不到（点名条目编号）」；备案规则文字不动（顺带发现按既有「有效但纯观察」口径进备案区）、宽表零加列
- **evals（8 场景）**：新增 eval-8 RECONCILE 代码核对（五路径：触发·坐实误读/触发·坐实真实/不触发·可仲裁/触发·定位不到/分歧条目例外；判负红线四条：该核对未核对、乱核对或开放探索、坐实误读进清单且代码证据改写 hard/soft、分歧条目被零留痕消解）；README 索引七→八、行 3 主线补「RECONCILE 代码核对」、评分纪律红线补双向条款
- **README**：版本指针 v0.15.0→v0.16.0

## v0.15.0 (2026-09-29)

sdlc-gate 产出物可读性：会话裁决呈现与 issues 文件双双白话化——起于真实演练反馈「呈现内容可读性差、无法关联上下文、没有解释，裁决变成盲选推荐项」。两条线落地：①Step 4 裁决呈现纪律重写为**两段式+四段结构**（正文逐条展开：场景白话/问题/不修的后果/方案，再问答收裁决——解释责任在正文，问答只收答案）；②issues 产物自足（明细表+裁决焦点表加「场景（白话）」列、头部「业务背景」行、新增「代号速查」小节——冷启动读者不翻 design/digest 可锚定；实际产物中「编号体系」kv 行被塞成 200+ 字代号表正是导读需求的实证，速查节将其解放回命名规则本职）。对照官方 best-practices：低自由度精确护栏（四段结构）/ 模板模式 / 示例模式（good/bad 场景对照）/ 反馈循环（check_trace 场景列非空校验）/ 评估先行（eval-7 与规则同批，标注落地后回归）。方案已过全新上下文对抗式评审（1🔴+5🟡+6🔵 全数吸收：真漏点 sdlc-doubt 镜像漂移、表头定位边界规格、eval 回归时点、walkthrough 声明句一致性等）。

**决策反转记档**：v0.14 前草案曾拍板「不加文件级导读、速览/焦点/备案/汇总表不加列」，本次经逐区块梳理后部分反转——导读两件套（业务背景行+代号速查节）与焦点表场景列采纳（焦点表是线下裁决入口），备案/汇总表维持不加（不进裁决的观察项与裁决后审计表，场景列无增量价值）。

- **sdlc-gate SKILL.md**：Step 4 呈现纪律重写（两段式+四段结构+代号首现释义+批首共享背景+复核通道；批首背景是会话增量呈现，文件级锚点=issues 头部业务背景+代号速查，裁决阶段不向文件追加）；对抗 prompt 字段增「场景」（2-3 句业务白话，素材=ARTIFACT 行为描述+CONTRACT 章节，作场景列初稿——解释责任前移到发现环节，终稿裁判权留主会话 RECONCILE）；「四个字段」计数措辞改不枚举（存量实列 5 项，加场景后 6 项，枚举必再漂移）；输出示例补「场景」「依据」两行（依据为存量缺失，顺带对齐；示例一律中性虚构）；Step 3 委托句可读性红线清单同步
- **issue-template.md**：分歧/架构/可测性明细表加「场景（白话）」列（数据表「列同上」继承；该选位同时保住 check_release 尾部定位与严重度扫描窗口——插表尾即破坏前者）；裁决焦点表加同列（与明细行同源复制，不得改写）；头部 kv 增「业务背景」行（guard_dev 只认「评审状态」行，零影响）；新增「代号速查」小节（## 非数字标题不触碰 `^[〇一二三四]` 节匹配；只列本文件实际引用代号防膨胀；命名空间代号顺带被引用可达校验免费验证）；统计表分歧行标签图例形态规则（写「分歧（一 4·二 1·三 3）」禁裸「（4·1·3）」）；填写规则增场景必填/焦点同源/业务背景/代号速查/同根因合并场景处置 + good/bad 场景示例；速览统计/备案/汇总表结构不动
- **cross-check-guide.md**：输出格式四组→五组必填字段（增场景——交叉审查者是唯一双读者，场景产出条件最充分），三个输入/输出对示例同步补场景
- **check_trace.py（加固+新校验，非修复）**：严重度列改按表头列名定位（「严重度」/「分类·严重度」兼容；表头状态随节切换重置；数据表「列同上」无自身表头时沿用同节最近表头——巧合变规格；节内未见含严重度表头回退 cs[1:5] 位置扫描，旧格式兼容）；新增检查 5「场景列非空」（表头声明场景列时，〇节焦点行与一/二节明细行为空即报 文件:行号+编号，反馈循环兜底「场景必填」红线；旧格式无该列自动跳过）；unparsed 报错文案对齐表头定位形态。**诚实声明**：加场景列后（分歧/架构表严重度 cs[3]、可测性表 cs[4]）实测仍在原 cs[1:5] 窗口内——self-test v2ok fixture 在改造前脚本上即全绿（证据固化于 fixture 注释），表头定位是消除「扫描窗口碰巧够宽」巧合依赖并支撑场景校验的加固，非修 bug；规划期曾误判「草案无需改脚本的结论有误」，系 1 基/0 基列数混算，经对抗评审实测推翻、已向用户披露并重确认维持表头定位；self-test 6→9 锚（新布局正例/明细场景空反例/焦点场景空反例；旧六锚全保留，"ok" fixture 即旧格式兼容锚）
- **sdlc-doubt**：SKILL.md 对侧镜像同步（对抗模板分化声明原写「需结构化四字段（标题/原文/位置/严重度）」——存量已漏「依据」，改为不枚举+以 sdlc-gate 侧模板为准）
- **evals（7 场景）**：新增 eval-7 裁决呈现可读性（两段式+四段结构+代号释义+批首背景+复核通道；判负红线：只报编号无四段展开/题面塞解释；标注「依赖 v0.15.0 呈现纪律落地后方可回归」）；README 索引六→七 + 纪律红线补「裁决呈现只报编号无四段展开」；eval-4 合并断言补场景处置子句（场景取主行，被并入角色不再各写）；eval-2/5/6 断言核对只涉头部 kv 行，不受加列影响，未动
- **docs**：workflow.md 产物描述补「场景白话/头部业务背景+代号速查」；example-walkthrough 步骤 4 issues 样例同步当前模板（存量样例为漂移的旧模板变体，顺带补齐 分类·严重度/分歧点 列）+ 头部「原样保留」声明句同步注明 v0.15.0 例外
- **README**：版本指针 v0.14.0→v0.15.0

## v0.14.0 (2026-09-29)

design 产物独立目录：轻量链路 design.md 从需求目录根散文件挪进独立子目录 `sdlc/<需求名>/design/design.md`，与 intake/ / review/ / test/ / dev/ 同层级对齐（五子目录）。大需求链路不动（A 级 design.md 仍随任务框架 parent 任务目录，本就不在 sdlc/ 目录树）；守卫脚本零改动（guard_dev / guard_exec / verify_dev / check_trace 均不检查 design 路径）；sdlc-sync payload 不带 design 路径、sdlc-intent digest 不引用 design 位置，均不涉及。**行为变化（置顶注意）**：无旧位兼容——sdlc-design「已存在 design.md」检测只查新位置，v0.13.x 在途产物的旧位 `sdlc/<需求名>/design.md` 需手工挪入 `design/` 子目录（不做 fallback，用户拍板）。

- **sdlc-design**：SKILL.md Step 5 落盘路径改 `sdlc/<需求名>/design/design.md`（子目录不存在则创建）；trellis-handoff.md 落位规则表「轻量需求 / 无任务框架」两行同步（大需求行不动）
- **sdlc-gate**：前置输入表「技术设计」行轻量路径同步
- **sdlc-gate（check_trace.py 修复，真实演练产物暴露两处，对照官方 best-practices）**：① 严重度解析宽容模板红线合法变体——局部加粗 `分歧·**高**` 此前被 `strip("*")` 漏解析、明细行被静默跳过、伪装成下游「计数不同源·请重数」的错误方向提示（违反「解决问题，而非推给 Claude」：脚本应处理合法输入变体）；解析彻底失败新增显式报错（文件:行号+前四列原文），不再静默吞行。② 新增 FR 前缀方言检查——cases 追踪表首列误用项目名作命名空间（如 示范.FR-01）此前静默跳过、只报下游「覆盖缺口」不指因（违反「错误消息指向具体问题」）；现报「应为 需求.FR-xx（全局 ID 约定：命名空间是产物名而非项目名）」并指到行，`^需求\.FR-` 锚定本身不放宽（digest-template / case-template / large-req-stage1 模板 / sdlc-sync payload 外键四处背书，非巫术常量）。self-test 增两回归锚：局部加粗宽容正例 + 方言指因反例
- **sdlc-test**：用例独立性红线括注路径同步（禁读 `sdlc/<需求名>/design/design.md`）
- **evals（7 场景）**：design eval-1/6/7 落盘与 files 路径断言；eval-4 大需求红线措辞精确化——原「不是 `sdlc/<需求名>/`」与新的 `design/` 子目录前缀歧义，改「不放 sdlc/ 产物目录树（含 `sdlc/<需求名>/design/` 子目录）」（expected_behavior 与判负红线两处）；gate eval-1/3/4 files 路径同步（eval-3 query 内路径同改）
- **docs**：workflow.md 产物目录约定四→五子目录 + §4 产物层行补 design；example-walkthrough / sdlc-test-design 两处目录树加 design/ 行（注：轻量链路落此，大需求随 parent 任务目录）；landscape 产物目录枚举同步（顺带修旧措辞 req→intake）；id-linkage-plan 轻量需求兜底路径同步
- **引用基准修复（全仓引用审计发现 4 处存量，非本次引入）**：references/ 子目录文件内「skill 根基准」写法从文件自身位置相对解析会差一级，且 CI 链接守卫（只查 `[](...)` 链接、反引号守卫只查仓级前缀按仓库根解析）覆盖不到——missed-patterns.md `../sdlc-sync/SKILL.md`→`../../`、env-template.md `scripts/verify_dev.py`→`../scripts/` 与 `references/spec/spec-guide.md`→`spec/`、exec-example.md `references/exec/exec-dispatch.md`→同目录 `exec-dispatch.md`；审计其余项全过（相对链接含代码块内零断链、marketplace 双向对账、design 迁移零旧式残留）
- **README**：版本指针 v0.13.0→v0.14.0

## v0.13.0 (2026-09-28)

技术设计 skill（sdlc-design，第 8 个）落地：补上「需求评审 → **技术设计** → gate → 任务框架拆分执行 → 测试」链路中设计环节的空位——此前 design.md 靠主会话裸做或人工翻 playbook，gate 的评审对象有产无源。设计与拆分分工：skill 只产 design.md（契约/决策/公共资产/切分约束），任务编排归任务框架（如 Trellis），三段式理念由四层机制保住（design §7 切分约束文档 / `.trellis/spec/` 切分规范 / handoff 确认点③四条件清单 / guard_dev 机械拦截——后者 v0.12.0 已建）。依据：Google Design Docs（Alternatives considered、无 trade-offs 即 implementation manual）、AWS Kiro / GitHub Spec Kit / OpenSpec（requirements→design→tasks 结构对照）、官方 best-practices（评估先行 / 反馈循环 / 模板模式 / 集合命名一致）。方案已过全新上下文对抗式评估（3 阻断 + 7 建议全吸收：Q 表载体断链→sdlc-design 承接（复用 prd 优先、生成兜底，用户拍板）；确认点③与横切矩阵核验无落地载体→handoff 补四条件清单+核验补记时点；eval 红线与 playbook 硬阻塞语义相反→改「锁功能点不锁全局」）。

- **sdlc-design（新增，8 文件）**：SKILL.md 精瘦主干——分级路由（C 级跳过引导轻量路径 / B 级 mini / digest 缺失先跑 intent）+ Q 表定位规则（stage1 prd Q 表复用优先，轻量链路由本 skill 在 design 头部生成维护：pm-checklist 未答复 + digest 假设清单「假设」类）+ 前置闸三道（Q 表硬阻塞=锁功能点不锁全局、被锁行标「锁定待拍板」；分级已拍板；tier 只升不降回写 digest/cases/issues 三头）+ 五步 checklist + 齐套自检六项（反馈循环）+ Step 5 关卡措辞（确认点② ack=定稿≠放行、cases 并行推导禁读设计不做后补降级档、gate 放行后才可开发）；MCP 完全限定名（codegraph:codegraph_explore / mysql:mysql_query）均声明降级
- **design-template.md（references）**：A 级全量骨架自包含（头部字段含输入锚点/偏差回写单写/体检问题去向权威归属/Q 表 + §0 备选方案 + §1-§6 继承 stage2 + §7 实施切分约束（spec 降级声明置顶、切分建议表含四件套验证口径、横切矩阵核验补记时点=check 阶段）+ §8）+ B 级 mini 裁剪表（头部字段不裁）；纯声明性提及 playbook（防二层引用诱导读取）
- **trellis-handoff.md（references）**：设计交付接入契约——落位规则（大需求 parent 任务目录/轻量 sdlc/）、prd.md 两区结构（brainstorm 退化为 scope 确认）、确认点映射与③四条件清单（契约符合度/内联注入完整性/AC 可测性/gate 已放行）、implement·check.jsonl 登记条目、`.trellis/spec/` 切分规范模板（一次落盘全员注入；skill 只提示不代写）、关卡接入行为约定（挂接方式以 playbook §7 为权威，声明性提及）；框架无关声明
- **evals（6 场景 + README）**：评估先行——A 级全量齐套 / C 级跳过 / Q 表硬阻塞（锁功能点不锁全局）/ Trellis 衔接（含确认点③四条件）/ tier 升级三头同步 / 定稿语义与独立性（ack≠放行、禁用例后补）；纪律红线任一命中判负
- **同步**：marketplace.json（数组 +1、Seven→Eight、根/plugin description 补 design + 顺带补 v0.12.0 的 dev/guard_dev 措辞）；README（中英简介、全景图 C1 标注、矩阵 7→8 + design 行、关键机制加「设计与拆分分工」、渐进阶梯插入第 4 级、三段式小节注机制化、Roadmap sdlc-flow/sdlc-doc 边界注记、版本 v0.13.0）；workflow.md（B3a 标注 + 阶段表 + 技能层行）；landscape（资产地图知识层 +1、② 技术骨架行标注、热力图六→八 skill）；faq（「6 个 skill」→8 落后两版一并修、MCP 降级表 + sdlc-design 行）；playbook 第二段头部机制化说明；stage1/2/3 模板头部对称指针（Q 表载体/机制化承载/确认点③清单映射）；sdlc-gate 前置输入表技术设计行补注产出方
- **诚实声明**：单模型验证（多模型测试未做，沿用 v0.9.0 先例）；Trellis 运行时行为未验证（handoff 按其公开文档约定，brainstorm 退化顺畅度待首次真实需求走查）；example-walkthrough 为历史快照不动（其 stage1 prd+Q 表走查与新链路并存，Q 表复用优先规则兼容）；intent-audit-v2（「七 skill 全部可解析」验收口径）、sdlc-test-design（「四阶段编排」架构口径，dev 阶段见 v0.12.0）与 sdlc-test-spec-evolution（「两档分层」执行模型口径，spec 资产化已并入 dev/static/exec 全链路）同为决策记录快照不动，历史表述以当时为准；design 产物上 sdlc-sync 平台另议（payload v1.5 候选）
- **提交前 CR 修复（跨 v0.12.0/v0.13.0，多维评审 34 项全数落地）**：守卫「评审状态」识别三处统一头部限定（guard_dev / guard_exec 检查5 / 关卡1 互认——正文插行不再构成放行，eval-6 补对应伪造判负红线）；tier 三口径补 issues 头第三头 + 值全串校验（拒「AB」类坏值；「未分级（按 A）」按 issue-template 允许记 note）；smoke 计数正则两侧下沉 _shared 同源（裸标题分叉致「verify 通过 vs guard 拦截」矛盾态消除）；boot 日志名经留档头部字段显式化（缺失降级旧推导，兼容存量留档）；verify_dev 健壮性批修（boot 后 try/finally 停服务防进程泄漏、code= 数字字符串归一、超时/健康 URL/变量闭包/数组下标步 0 快失败、鉴权真值 git check-ignore 机械核查（非 git 环境降级 note）、留档围栏四反引号、P0 覆盖核对（SM 条目 ∪ 不适用清单，防静默缩面）、gate 三态标签消除「未过(exit=0)」矛盾文案、parse_auth 兼容无前缀 KV 形态（存量 bug，修复后 gitignore 核查方可达））；stage2 模板与 design-template 节号对齐（§0-§8：§7 实施切分约束/§8 风险与边界，L3 指令改机制化优先，三项已知差异点名；trellis-handoff verify 行补「最新一份=通过」判定口径；B 级括注与 playbook 轻量公式双向消歧）；sdlc-design 触发词补「详细设计、概要设计」、锚点比对扩 digest/audit/pm-checklist 三文件、新增 eval-7 锚点过期场景；文档口径批修（CLAUDE.md/README/faq 计数 7→8 与算术修正、分档措辞三处漏网、sdlc-design MCP 依赖表述、landscape B 档「全量（同 A）」消歧、workflow 产物层补 dev、D1-D22 三处、marketplace 子命令串补 spec）；.playwright-mcp/ 入 .gitignore + 敏感词扫描补 --hidden（隐藏目录盲区，CI 与 CLAUDE.md 命令同步）；`poc/ai-native-handbook.pdf` 移出跟踪（0ef67d4 误入库的 26MB blob，git rm --cached——同一提交内 ignore 对已 add 文件无效；历史提交仍在，完整 clone 仍含，来源声明见 docs/ai-native-alibaba-handbook.md 头注与 .gitignore 注释）

## v0.12.0 (2026-09-28)

开发阶段双关卡落地：① **开发放行守卫**（guard_dev.py）——把「任务框架/协作文档的人工 ack ≠ 质量放行」机械化，ack 是流程性定稿信号，放行唯一口径 = sdlc-gate issues 头「评审状态=已放行」；② **开发完成验证**（verify_dev.py，`/sdlc-test dev`）——compile/boot/冒烟/回归按风险分级前置到开发收尾（DoD「code compiles」+ 冒烟是测试准入而非替代；agent 无执行反馈即开环盲写，同上下文自愈最便宜），留档反查挂进 static/exec 入口形成倒逼。依据：Google Design Docs（实现前同行评审）、GitHub Spec Kit / AWS Kiro（阶段间门）、Scrum DoD 与 smoke test 语义、IBM 缺陷成本曲线（设计 1→实现 6.5→测试 15→生产 100）、官方 best-practices（计划-验证-执行 / 一致术语 / 一层引用 / 评估驱动 / 防巫术常量）。已过全新上下对抗式方案审查（15 条 issue 全裁决吸收，3 条高危：本地 boot 可行性→unmanaged 一等公民模式、留档可伪造→四项交叉校验、大需求 verify 过期→HEAD 比对）+ 官方 best-practices 校准。

**行为变化（置顶注意）**：guard_exec 检查5 上线即拦所有在途需求的 static/exec——补跑一次 `/sdlc-test dev` 即过（C 级最轻：env/dev.md 仅「构建」「启动」两节）；关卡1 互认由「任一份 review 含已放行」改锚**最新一份**（修 r1 已放行+r2 待裁决误放行 bug；受影响存量 = 开过 r2 的需求——完成 r2 裁决，或确认误开后移出 review/）。known boundary：前端-only child 仍全量 boot（按端路由不做）、unmanaged 依赖外部供给的服务正确性、Windows 未验证（mac/Linux 载体）。

- **sdlc-gate（guard_dev.py 新增，~80 行）**：开发入口守卫——review 目录空 / 最新份缺「评审状态」字段 / 非已放行三态拒，拒绝文案点明「ack（确认点③/协作文档确认）只是定稿信号」；latest_by_name 与 check_trace 同口径（跨 skill 复刻，两处 docstring 互相点名）
- **sdlc-test（verify_dev.py 新增 ~330 行 + _shared.py ~60 行）**：四件套确定性编排——构建 / 起服务（进程组 SIGTERM→10s→SIGKILL，启动命令勿自行后台化）/ 健康探测（单次 5s 超时、间隔 2s 轮询）/ 冒烟（按文件序前条数据后条可用，`{{变量}}` 插值链）/ 回归；启动模式 **local | unmanaged**（本地起不了服务时 unmanaged 跳起停、探测+冒烟+回归照常——仍是机器验证非人工声明）；断言 DSL 四种（`HTTP <n>` / `code=<n>` / `包含"文本"` / `存 <变量> ← <点路径>`），语法/来源引用构建前快失败；留档头部六字段（验证状态/风险分级/启动模式/执行范围/验证时 HEAD/开发放行守卫——步0 尽力调 guard_dev 记录其结果）；C 级 compile+boot；超时默认值注明依据。_shared.py 集中 latest_by_name / tier 三口径 / git_head 防同 skill 内脚本漂移
- **guard_exec.py 检查5**：留档反查 + 四项交叉校验（验证时 HEAD≠当前→拦「验证过期」；local 须同轮 boot 日志；A/B 级留档冒烟条数=smoke.md 条数；C 级留档遇 A/B 分级→拦 tier 已升级）；「通过(人工降级,日期)」放行但显式 ⚠️ 警示；fail() 改按检查附带补救提示（检查5 为引导式：先建 env/dev.md→跑 dev→重跑）；关卡1 互认改最新份判定
- **smoke-template.md（新增，sdlc-test/references/dev/）**：冒烟清单权威模板——agent 从 cases.md P0/核心用例推导落盘（计划-验证-执行），四种断言 DSL 规格、条目有序链式、不适用 P0 逐条列原因（防静默缩面）、头部生成会话/复核人责任字段、禁写鉴权真值与内网域名（脱敏红线）
- **env-template.md**：新增 dev.md（五节：模式/构建/启动/冒烟/回归，占位符尖括号中文）与 dev-auth.local.md（gitignored 本机供给）两节；纪律补三条（鉴权真值只进 local、留档响应尾部脱敏、dev-auth 依赖 `sdlc/env/*.local.md` gitignore 条目）
- **sdlc-test SKILL.md**：路由表加 dev 子命令（阶段 1.5）；新节「阶段 1.5 dev」——三步 checklist + smoke 重生成口径（P0/可适用集合变化才重生成，结果回填不算）+ 降级边界（人工降级留档会被警示）；反合理化加三行（开发完成≠静态过 / 冒烟过≠功能对 / 占位回归判负）；description 扩 dev 与触发词
- **sdlc-gate SKILL.md**：Step 5 扩「放行后：开发放行守卫（已机械化 2026-09-28）」；路由节补「已放行≠可开发」
- **eval-6 / eval-8（新增，与 SKILL 同步产出）**：guard_dev 三态 + ack 后直接开发判负 + 伪造 issues 判负；dev 流程 + 漏翻 P0 判负 + 冒烟当功能对判负 + 占位回归判负 + 手写通过留档判负（两 README 索引同步）
- **docs**：workflow mermaid 时序统一（确认点②定稿→gate 评审裁决→放行→③，B6 加完成验证留档）+ §3/§5 表双关卡 + 顺手修两处「4 个子代理」分档漂移；playbook mermaid 插 gate 节点 + §2 用例并行产出约定（不做设计先行用例后补降级档——交叉审查依赖用例在场）+ 确认点③措辞 + §7 源项目（Trellis）侧接入点表（任务 start 校验 guard_dev exit 0 / 任务完成校验 verify 留档）；faq 2 新 Q + 术语表 3 行（开发放行守卫/开发完成验证/冒烟清单——声明与关卡1/2 的轴别：机器守卫 vs 人工关口）；landscape 强制层两行 + ②③ 时序对齐 + 分级路由表「开发完成验证」行（A/B=全量、C=compile+boot）+ guard_dev 入不分级项 + 产物目录加 dev
- **templates**：stage3 验证命令节 compile 单条→分级四件套指向（env/dev.md + /sdlc-test dev）；stage2 验证方式同步
- **README**：sdlc-test 行子命令串加 dev、sdlc-gate 行加 guard_dev、关键机制加「开发双关卡」；版本指针 v0.10.0→v0.12.0（顺手修落后一版）

## v0.11.5 (2026-09-27)（补录）

C 约束 / H 假设决策类型 + 用例反馈层级 L/M/H（阿里《AI Native 研发范式实践手册》对照落地，78066b6）。依据：手册 p19「Spec 区分约束与假设——约束长期保存+自动检查，假设按反馈调整」与「分层验证体系：秒级/分钟级/人工」。

- **sdlc-intent**：第 4 层新增「隐含约束未声明」检查项；体检明细表增类型列 C?/H?/—（初判带问号，PM 答复定型）；定型 C→人工转 sdlc-guardrails 候选、H→测试验证项；eval-10
- **sdlc-test**：用例头部增「反馈层级」L/M/H；反馈层级与 spec 资产化联动；报告增反馈层级分布与证据索引表；spec-guide 增断言基线
- **templates/large-req-stage2**：D 表增类型列值域
- **docs**：新增 ai-native-alibaba-handbook（docs/README.md 登记）；sdlc-test-design 补 D22/§10 闭环不变量并去重；CLAUDE.md 计数同步、README 版本指针修正；.gitignore 排除手册 PDF（后经 v0.13 CR 发现误入库并移出，见 v0.13.0）

## v0.11.0 (2026-09-27)

digest 产物图例与图题落地 + 流程/状态机结构化上平台（payload v1.4）：让产物脱离模板自描述（符号体系集中图例、每图有题），补平台「需求摘要」缺流程/状态机视图的澄清期缺口（摘要区外移表、含断点行，折叠区原文不动），标准文档维持逻辑文本化仅显式化 ❓ 断点取材。依据：C4「每图须有 key/legend + title」、Moody《Physics of Notations》Dual Coding / Semantic Transparency；AI spec 工具对照（GitHub spec-kit 内嵌 mermaid、AWS Kiro）。已过全新上下文对抗式审核（1 阻断：resolve_anchors 同步扩展；10 建议全吸收，含图例第三措辞坑、render 时序、组名撞名）。

- **sdlc-intent（digest-template）**：产物骨架增「符号图例」小节——无编号、不进产物目录（下游 §5/§6/§7/§8 引用不漂移）；措辞红线三条（禁 FR/A 数字实例、禁「风险分级：」冒号取值——check_trace.py 行首正则与 guard_exec.py 全文首命中双坑规避）；§5/§6 每图加图题行，§6 固定「图 N：<对象名> 状态机」（对象名是 states.obj 提取唯一载体，双通道 agent 共守）；§6 图后附表由状态表升级为**流转边表**（从/触发/至/出处，? 行=断点）——平台状态机数据以表直投不从图提取，且直接对应 sdlc-test「S2→S3 边」用例引用
- **sdlc-intent（scripts/doc-pipeline）**：resolve_anchors.py 锚点附加扩至六类条目（+digest.flows/digest.states，阻断项）；doc-pipeline 条款级出处适用字段与控制台计数同步
- **eval-1**：增 3 条断言（符号图例小节/图题格式/边表形态与 ? 行），状态机 ❓ 清单措辞对齐边表口径
- **sdlc-sync**：payload 契约升 **v1.4**——digest 增可选 `flows[]`（§5 步骤表）与 `states[]`（§6 边表直投）：`gap:true` = 原文断点行、next/to 填 `"?"`，行级 src + 可选 anchor（resolve_anchors.py 同源附加）；GET 详情返回描述同步；v1.3 说明下移历史变更节
- **standard-doc-spec**：消化规则 3/4 与自查清单显式覆盖 §5 图节点 ❓ 与 §6 边表 ? 行——澄清后仍未定案的断点进遗留假设，图上标记在文本化定稿中不再丢失
- 平台侧（sdlc-platform 仓 DESIGN-v2.3，另一 commit）：后端 digestDigestView 白名单加两字段组、Runner 速查卡同步（顺手补 v1.3 risk_tier 既有缺口）、摘要 tab 两表（gap 高亮/anchor 跳转/组名前缀防共享 Set 撞名）、前端引入 mermaid（MutationObserver + 惰性 import，render 时序与红线豁免两处登记）

## v0.10.0 (2026-09-26)

需求风险分级（A/B/C risk tiering）全链路落地：把散落的隐式分级（sdlc-intent 轻重路由二分、doubt 触发条件、gate 批量裁决）显式化为贯穿管线的三级分级——轻需求负担得起全流程，重需求保持全量，分级落库后支撑分层泄漏率校准。依据：DO-178C DAL / IEC 62304 Class / ISTQB risk-based testing；AI 提议+人工拍板（Hall et al. 2012：自动分级不可靠）。已过对抗式评审（12 处修正，核心为设计期影响面事实的 tier 只升不降回写通道）与官方 best-practices 对齐（评估先行/查表低自由度/术语统一「风险分级」与「A·B·C 级」）。

- **risk-tiering.md（新增，sdlc-intent/references/）**：评分卡唯一权威（顶部目录）——影响面 6 项（含哪些是设计期才能确认的代码级事实）/ A·B·C 判据（C 仅纯展示文案，配置类入 B）/ FR 级归属规则（出处列回溯 §4）/ 聚合公式 max(评分卡, max(FR)) / 回写通道（只升不降，gate 双重判级 B→A 补扇出）/ 存量与 guard 三口径
- **sdlc-intent**：digest 头增「风险分级」字段（提议态→Step 4 人工拍板）；§7 规则表增「分级」列（自含口径，不引 risk-tiering.md 防两层引用）；轻重路由升级为分级路由（A=全阶段，B/C 跳过阶段1，无字段按 A）；report-template 执行摘要首句结构化；「仅重需求」措辞全量改「仅 A 级」（SKILL.md ×2 / dimensions / perspectives ×2 / eval-8）；eval-9 新增（README 索引同步）
- **sdlc-test**：cases 头部增「风险分级」字段；design-techniques 增「分级生成范围」查表（FR 级 A=全技术全优先级 / B=P0+P1+不变量 / C=P0+不变量；任何级不裁编辑类四组闭环不变量）；spec 资产化分级控制（A 强制 / B 默认 / C 跳过）
- **guard_exec.py**：新增检查 2.5 风险分级三口径（整行缺失→提示「按 A 级继续」不拦，存量兼容；空/坏值→拦；digest 头与 cases 头不一致→拦）——错误消息含非法值与合法枚举（官方「解决问题不推给 Claude」）；check_trace.py 评估后**零改动**（FR_DEF 锚定行首第一格，§7 加列与 issues 头部 kv 行均不破坏现有四项检查）
- **sdlc-gate**：按风险分级分档（A=4 子代理 / B=2：数据模型+交叉审查者 / C=主会话自查——仍产 issues 走裁决+放行，保关卡互认链）；双重判级（cases 头 + design 影响面章节对照，判低先升级再扇出）；issue-template 头部增风险分级行（缺省「未分级（按 A）」）与「C 级自查清单」附表（对抗 prompt 五问 × 设计/用例两侧；独立性行如实标注「主会话自查（C 级）」）；「4 个子代理」硬编码 4 处全改（frontmatter description / checklist / Step 2 / marketplace.json description，skills 数组不动）；eval-5 新增（README 计数句同步）
- **sdlc-doubt**：分级关系一行（A 级命中即强制 / B 级可选 / C 级跳过；无字段维持原判定）
- **sdlc-sync**：payload 契约升 **v1.3**——建卡与 push-artifacts `digest` 增可选 `risk_tier`（后到覆盖，兜底建卡早于定级的时序；命名避开问题严重度 `level`）；详情返回 `card.riskTier`（平台 v2.1 起）；v1.2 头部说明下移历史变更节
- **docs**：landscape 第二章新增「需求分级路由」节（含控制矩阵），轻量/大需求小节挂分级、gate 扇出改分档措辞；playbook 触发条件注明 ≈ A 级（正文 + mermaid 节点）；workflow.md 对齐注；README 关键机制加「需求分级路由」+ 大需求判据对齐注
- 版本卫生：v0.9.0（在途未提交）与本条建议分两次提交；payload v1.2 在途纠正随 v1.3 历史变更节归档说明

> v0.9.0 及更早的历史版本记录见 [docs/changelog-archive.md](docs/changelog-archive.md)。

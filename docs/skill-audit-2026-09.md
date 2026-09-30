# Skill 仓库对照官方最佳实践评估报告（2026-09-30）

> 评估依据：Anthropic《Skill 编写最佳实践》（platform.claude.com/docs/zh-CN/agents-and-tools/agent-skills/best-practices，12 个官方维度）+ 4 个仓库特有扩展维度（执行成本放大、理解/维护成本、触发边界、分发卫生）。
> 方法：三路摸底（结构扫描 / 3 个代表 skill 内容抽样 / 冗余专项分析）→ 对抗式评审（8 条事实断言抽查，7 条属实 1 条证伪）→ 批次 0 逐条重验（28 项证据 26 项 PASS，2 项现场修正）。
> 本报告同时是优化执行清单：每个问题标注批次（P0 卫生 / P1 结构 / P2 压缩），P2 涉及约定的项需用户裁决。
>
> **执行结果（2026-09-30 同日完成，见 CHANGELOG v0.17.0）**：
> - 批次 0（前置）：28 项证据逐条重验（26 PASS，2 项现场修正：doubt desc 实为 148 字符系重验正则假象、P11→Q3 分化出处定位到 design-template.md:40）；sdlc-doubt 3 个 evals 迁官方 JSON 结构；sdlc-gate /tmp 安装冒烟通过（15 文件完整、guard 脚本可执行）
> - 批次 1（P0 #1-6）：全部完成——脏文件清理、faq 死节名、sdlc-test:8 措辞、gate 补 `## Step 1`、check.py 补 require_if、格式统一（阶段空格/同轮本轮/README H1）、过时状态句更新
> - 批次 2（P1 #7-12）：完成，其中 **#7 结论修正**——sdlc-test SKILL.md 实以反引号格式直引全部 14 个 references（首轮摸底正则只认链接格式致误判），全仓一层可达性天然合规，无需改动；#8a gate 代码核对段表格化（表述压缩，不外移）；#8b test 取证细则压缩为要点+指针（红线摘要常驻）；#9 doubt desc 增量补触发词（只增不删）；#10 时效清洗 10 处；#11 质检→体检统一（SKILL 6 处 + payload-schema 叙述 3 处；字段名白名单保留 3 处）；#12 即本报告 §6
> - 批次 3（P2）：机械项完成（stage2 自重复收敛、示例 Q3→Q6 统一、目录树快照注记、CHANGELOG 归档 161 行且敏感词先清洗）；裁决项按用户决定执行——三镜像最小方案（workflow 补第 4 条触发条件，指针原已齐）、对抗模板结构化为共享核心段+输出段并新增 CI 比对（scripts/check_adversarial_core.py，正反向验证通过）、workflow↔landscape 核对结论为「重复段各有职责轴」故互加职责声明不强删、poc/ 4 文件移出 git 追踪
> - 现场裁量：#15（8-skill 清单 4 轮导航去重）降级为记录不动——四处各有职责面（获客/教程/导读/FAQ），删除伤对应读者

## 1. 结论摘要

整体判断：**结构层健康，内容层有债**。8 个 skill 全部远低于官方 500 行红线、frontmatter 全部技术合规、marketplace 与目录一致、相对链接零断链、自由度匹配与反馈环设计普遍优于官方基线要求。主要债务集中在：①时效性信息渗入规范性条文（11+ 处）；②多写同步负担已实际失守（三镜像分化 1 处、示例分化 1 处、死节名引用 1 处）；③evals 停留在纯手动形态（45 场景，sdlc-doubt 3 个已于本次迁官方 JSON 结构）；④两个高密度 SKILL.md（sdlc-gate 96 字节/行、sdlc-test 137 字节/行）承载了部分 reference 级细则。

## 2. 评分卡（16 维 × 全仓结论 + 个别偏差）

| # | 维度 | 全仓 | 个别偏差 |
|---|---|---|---|
| 1 | 令牌成本（≤500 行） | ✅ 57-165 行 | ⚠️ sdlc-gate 96 B/行、sdlc-test 137 B/行（行数不大字节极大） |
| 2 | 自由度匹配 | ✅ 脆弱操作均有 guard 脚本+验证环；sdlc-guardrails 为最佳样本 | ⚠️ sdlc-test 个别无依据硬数字（retry-once 上限 1 次、每批 3-5 条） |
| 3 | description 触发 | ✅ 全部含功能+Use when+触发词，均 <1024 | ⚠️ sdlc-doubt 148 字符偏短（P1 #9 补触发场景） |
| 4 | 命名一致性 | ✅ 8/8 kebab-case + sdlc- 前缀 | — |
| 5 | 渐进式披露 | ✅ 模板全部外置 references | ⚠️ sdlc-gate ~60 行细则、sdlc-test :95-103 长 bullet 达 reference 密度（P1 #8） |
| 6 | 引用一层深度 | ⚠️ 6 处 reference→reference 互引 | 多数被引文件 SKILL.md 已直达（可达性合规）；行为指令性互引保留（P1 #7） |
| 7 | 工作流/反馈环 | ✅ 强：关卡措辞模板、check_trace「exit≠0 修复重跑」、evals 判负红线 | — |
| 8 | 无时效性+术语一致 | ❌ 全仓最弱维 | 时效信息 11+ 处（P1 #10）；质检/体检、同轮/本轮、阶段空格混用（P0 #5、P1 #11） |
| 9 | 模板/示例 | ✅ fenced 模板可直接照抄，输入输出对具体 | ⚠️ sdlc-gate issues 无一份填好实例（walkthrough 有部分样例） |
| 10 | 脚本质量 | 见 §6 脚本评分卡 | — |
| 11 | 评估驱动 | ⚠️ 场景数达标（3-10 个/skill，sync 除外） | sdlc-sync 0 独立场景；JSON 迁移 3/45（本次 doubt 已迁）；无自动运行器；多模型测试空白 |
| 12 | 技术合规 | ✅ name/desc/路径全部合规 | — |
| 13 | 执行成本放大 | 见 §7 token 预算表 | gate A 级 4 子代理扇出为全仓最大单次成本 |
| 14 | 理解/维护成本 | ⚠️ 多写同步负担重（见 §5） | 三镜像/对抗模板/ack 规则/目录树多处复述 |
| 15 | 触发边界 | ✅ gate（评产物）vs doubt（评决策）等边界在 description 中可区分 | — |
| 16 | 分发卫生 | ✅ marketplace 一致、零断链、安装冒烟通过（15 文件完整、guard 脚本可执行、报错含用法说明） | ⚠️ faq 死节名引用、sdlc-test SKILL:8 措辞（P0 #2） |

## 3. 问题清单（证据 → 动作 → 批次）

### P0 卫生（批次 1）
| # | 问题 | 证据 | 动作 |
|---|---|---|---|
| 1 | 本地脏文件 pyc/.DS_Store 7 处 | skills/{test,gate,intent,guardrails} 下 | 清理（git 未追踪，安装实测不带走——优先级低但顺手清） |
| 2 | 死引用 | docs/faq.md:42 引 README 旧节名「渐进采用阶梯」（实名「按需采用，不必全装」）；sdlc-test SKILL.md:8「安装副本中该文件缺失」措辞过时 | 改实名 / 改措辞 |
| 3 | sdlc-gate 缺 `## Step 1` 标题 | checklist :32 列 Step 1-5，正文 :39 起仅 Step 2-5 | 补节标题（内容已在「前置输入」表隐含，补标题+一句话） |
| 4 | check.py docstring 漏 require_if | docstring 规则类型列表 vs 代码 :71,:112 已实现 | 补一行 |
| 5 | 格式/术语 | sdlc-test「阶段1」vs「阶段 1.5」；「同轮/本轮目录」；README :71,:78 中部 H1 | 统一 |
| 6 | 过时状态句 | sdlc-gate evals README eval-7「依赖 v0.15.0 落地方可回归」（v0.15 已提交）；sdlc-test evals README「待 M1 试点验证」 | 更新（执行时确认 v0.16 提交状态） |

### P1 结构（批次 2）
| # | 问题 | 证据 | 动作 |
|---|---|---|---|
| 7 | 二层引用 6 处 | dimensions.md:115 等 | 仅补齐 SKILL.md 指针；行为指令性互引保留 |
| 8a | sdlc-gate :111 代码核对 493 字符单段 | 每轮必经内容 | **仅表述压缩**（表格化），不外移；载体改动须等 v0.16 提交+eval-8 回归 |
| 8b | sdlc-test :95-103 exec 细则长 bullet | 6 子命令单会话只走一条 | 可外移 exec-dispatch；「执行红线摘要」派发锚点常驻 |
| 9 | sdlc-doubt description 148 字符 | 全仓最短，缺「用法」与场景词 | 补触发场景（词取并集，真实冒烟验证） |
| 10 | 时效信息 11+ 处 | spec-guide.md 8 行（4,11,14,26,53,55,91,103）、gate :119,:154,:158「已机械化+日期」、spec-guide:91 运行痕迹「2026-09-26 R2 exec-log#L45」 | 全清口径：删日期/版本号，痕迹换中性虚构 |
| 11 | 质检/体检混用 | sdlc-sync SKILL 质检 7 行 / 体检 5 行 | 统一「体检」；白名单：:77「质检依据快照时间」（产物元信息头字段）+平台 API 字段名 |
| 12 | 脚本摸底盲区 | parse_doc.py 556 行全仓最大 | 已补摸底，见 §6 |

### P2 压缩/合并（批次 3）
| # | 问题 | 证据 | 动作 |
|---|---|---|---|
| 13 | stage2-template 内部自重复 | 切分建议表、横切矩阵各 2 份（标「同源」） | 收敛单份 |
| 14 | 体检去向示例分化 | design-template.md:40 `确认.Q3` vs stage1-template:84 `确认.Q6`（批次 0 已实锤出处） | 统一（以 stage1 的 Q6 为准，语义均为「口径待定」） |
| 15 | 导航重复 | 8-skill 一句话清单 4 轮（README/workflow/docs-README/faq） | 各留职责版 |
| 16 | 目录树重复+快照缺行 | 完整树 2 份+一句话版 5 份；sdlc-test-design 树缺 dev/ | 树收敛至 example-walkthrough；test-design 加「现行目录见 workflow.md」注记 |
| 17 | CHANGELOG 264 行单文件 | v0.9.0 及以前 103 行纯历史；**HEAD:139 含 CLAUDE.md 脱敏扫描清单中的红线词** | 归档 docs/changelog-archive.md，**归档前先清洗敏感词**，归档后跑脱敏+断链双验证 |

**需裁决项（P2 批次 3 提交用户）**：三段式三镜像处置（默认最小方案：修失守点+互加权威指针；整体收敛为呈报选项，README 获客面有风险）；对抗模板 gate/doubt 同步护栏（前置改造：拆「共享核心段/消费方输出段」两个 fenced block 后 CI 才可比对）；guardrails 三步接入三写（project-setup 改指针）；poc/ 4 个被追踪文件处置。

## 4. 压缩机会汇总

| 目标 | 估计行数 |
|---|---|
| README 三段式节+阶梯+图（若整体收敛——默认不做） | 20-25 |
| workflow.md 对 playbook/skill 的二述（呈报选项） | 60-80 |
| workflow vs landscape 文字重复（呈报选项） | 35-45 |
| sdlc-test-design 与 skill 平行叙述（决策记录快照，默认不动） | 90-110 |
| walkthrough/模板示例去重（#14 等） | 15-20 |
| faq 改指针（部分条目） | 12-15 |
| docs/README vs README 导航（#15） | 10-15 |
| 跨 skill 对抗模板+四分类（保留双份原则，仅结构化） | 0（换同步护栏） |
| 分级口径复述指针化（SKILL 内保留读取口径一行版） | 15-20 |
| stage2 模板内部自重复（#13） | 15 |
| 目录树收敛（#16） | 10 |
| CHANGELOG 归档（#17） | 103（HEAD 实测 v0.9.0 节前行数） |
| **默认口径合计（不动快照、不做整体收敛）** | **约 180-200 行** |

## 5. 多写同步失守实证（维护成本维度的核心证据）

1. **三镜像触发条件分化**：workflow.md:52,56 三段式触发条件仅 3 条，playbook:9 与 README:103 为 4 条（缺「AI 判定为大型且用户确认」）——CLAUDE.md 护栏 7 自认「CI 无法机检」的兜底已实际失守一次
2. **示例值分化**：体检.P11 落点 Q6（stage1-template:84）vs Q3（design-template.md:40）
3. **死节名**：faq.md:42 → README 已改名节
4. **目录树滞后**：sdlc-test-design 树缺 dev/（v0.12 同步时只补了 design/）
5. **隐性双源**：sdlc-gate ↔ sdlc-doubt 对抗模板靠互指「同源声明」维持（12 行逐字相同，输出段有意分化）
6. **规则复述面**：「ack=定稿≠放行」全仓 8 处；「无字段按 A 级/tier 只升不降」各 5+ 处；关卡措辞句式 4 处

结论：多写不是立即要消的冗余（skill 自包含原则要求跨安装可用），但**缺同步护栏**——P2 裁决项即为最小成本护栏方案。

## 6. 脚本质量评分卡

11 个脚本 × 5 项（错误处理 / 巫术常量 / 执行意图 / 依赖声明 / exit code 语义）：

| 脚本 | 行数 | 错误处理 | 巫术常量 | 执行意图 | 依赖声明 | exit code |
|---|---|---|---|---|---|---|
| sdlc-gate/check_trace.py | 683 | ✅ | ✅ | ✅ | ✅ | ✅ |
| sdlc-test/verify_dev.py | 644 | ✅ | ✅（超时常量全命名+依据+env 可覆盖，全仓最佳） | ✅ | ✅ | ⚠️（0/2 未文字化） |
| sdlc-intent/parse_doc.py | 555 | ⚠️ | ⚠️（timeout=120、截断值无注释） | ✅ | ⚠️（lark-cli 无安装指引） | ✅ |
| sdlc-intent/scan_refs.py | 262 | ⚠️（verify 路径无保护） | ✅ | ✅ | ✅ | ⚠️ |
| sdlc-gate/guard_dev.py | 102 | ✅ | ✅ | ✅ | ✅ | ✅ |
| sdlc-test/guard_exec.py | 202 | ✅ | ✅ | ✅ | ✅ | ✅ |
| sdlc-guardrails/check.py | 211 | ✅ | ✅ | ✅ | ⚠️（pyyaml 仅 README 提及，无安装命令） | ✅ |
| sdlc-intent/resolve_anchors.py | 170 | ❌（4 处 json.load 无保护） | ✅ | ⚠️（SKILL.md 无引用，仅二级文档） | ✅ | ❌（锚点全 miss 也 exit 0） |
| sdlc-test/_shared.py | 169 | ✅ | ⚠️ | ✅（自声明非 CLI） | ✅ | N/A |
| sdlc-guardrails/audit_profiles.py | 106 | ✅ | ⚠️（显示截断无注释） | ✅ | ✅ | ✅（0-3 全枚举文档化，全仓唯一） |
| sdlc-intent/list_clauses.py | 78 | ❌（主输入无保护） | ⚠️ | ⚠️（同上） | ✅ | ❌ |

**要点**：
1. **sdlc-intent 四脚本是短板聚集地**（错误处理 ❌×2 ⚠️×1、exit code 语义 ❌×2）——媒体/下游处理精细但输入侧 I/O 零保护，文件缺失即裸 traceback 甩给 agent。改进方向：入口处包一层 try/except 给中文指引（参照 check.py load_rules_safe 模式）。**列 Roadmap，本次不动代码**
2. **check_trace.py 是全仓标杆**（self-test 9 组正反例、错误消息指因+可修复上下文、注册表驱动）；audit_profiles.py 的 exit code 全枚举文档化值得推广
3. **公共逻辑重复**（有意取舍 + 真冗余两类）：
   - 跨 skill 三处复刻 `latest_by_name`、两处复刻 `header_text/header_kv`——均有互相点名的同步声明（单独安装互相不可见），属自包含原则的合理代价
   - **同目录真冗余**：`_ref_key` 在 sdlc-intent/scripts 的 parse_doc.py 与 resolve_anchors.py 逐字重复且同目录可 import——这是可直接消除的重复（Roadmap）
4. verify_dev.py 主流程约 200 行单函数、步序靠字符串门控——可维护性一般但行为正确（列 Roadmap）

## 7. 典型执行路径 token 预算表

估算口径：文件字节数 ÷ 3.5 ≈ token（中文密集取保守商数；量级用于横向比较，非精确计量）。

| 典型路径 | 构成 | 估算 token |
|---|---|---|
| sdlc-intent 全流程（梳理+体检） | SKILL.md 11.6K + digest-template 10.5K + dimensions 16.5K + report-template 10.2K + ref-tables 3.9K ≈ 53K B | ~15K |
| sdlc-gate A 级一次 | 主会话：SKILL.md 15.8K + issue-template 13.3K + cross-check-guide 5K + false-positive-patterns 1K ≈ 35K B；子代理：4 × 喂料（ARTIFACT+要点+CONTRACT 节选，无会话全文）估 4×2-4K | 主 ~10K + 子 ~12K ≈ **22K（全仓最大单次）** |
| sdlc-test cases 链 | SKILL.md 18.5K + case-template 6.8K + design-techniques 7.8K ≈ 33K B | ~9.5K |
| sdlc-test exec 链 | SKILL.md 18.5K + exec-dispatch 5.8K + exec-interaction 6.7K + anti-rationalization 2.1K + exec-log-template 4.5K ≈ 38K B | ~11K |
| sdlc-design B 级 | SKILL.md 6.6K + design-template 10.1K ≈ 17K B | ~5K |
| sdlc-guardrails 接入 | SKILL.md 4.1K + README 3.6K + example.yaml 5.8K ≈ 13.5K B | ~4K（全仓最轻） |

要点：①gate A 级是全仓最大单次执行成本，其「token 纪律限定子代理输入」红线（:49）是控制扇出成本的关键设计，应保持；②intent 的 dimensions.md 16.5K 是全仓最大参考文件，但按七层维度组织、体检时全量需要——拆分收益存疑，维持现状；③sdlc-test SKILL.md 常驻 5.3K 对只走 cases 的会话有 exec 细则死重（#8b 外移的量化依据）。

## 8. payload-schema.md 拆分评估

现状：181 行 / 12.3K B，5 个接口单文件；sdlc-sync 有 5 个子命令（submit/push-artifacts/pull-answers/publish/push-cases），单会话通常只走一条。按官方「按领域组织」模式拆分（如 submit.md / artifacts.md / publish.md / cases.md，共享字段节保留小节复用）可将单次读取从 12.3K 降到 3-6K。**建议列 P2 可选项**：该文件已有「## 目录」（批次 0 已验），且 sdlc-sync 使用频率相对低——拆分收益中等，优先级排在 #13-17 之后。

## 9. Roadmap（本次不做，登记备查）

1. **evals JSON 迁移余量**：30/45 待迁（sdlc-doubt 3 个已完成，模板见 evals/eval-1-extract-purity.md）。迁移时保持断言语义不变仅换载体（CONTRIBUTING 约定）
2. **sdlc-sync evals 场景独立成文件**：现仅 README 内嵌 5 条
3. **多模型测试**：官方建议 Haiku/Sonnet/Opus 三档验证——全仓空白；建议至少对 sdlc-intent（入口 skill）与 sdlc-gate（最重 skill）各跑一次三档触发对比
4. **evals 自动运行器**：现为纯手动回归；sdlc-test 的 guard_exec.py 模式（脚本判定）可扩展为场景自动判定的雏形
5. **README 获客面 A/B**：description 重写统一（若未来做）需配 /tmp 安装+新会话触发冒烟，逐 skill 单独立项

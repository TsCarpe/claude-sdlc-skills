# sdlc-sync 评估场景

> 评测基线脚本位于平台仓库（`$SDLC_PLATFORM_REPO`），未随本仓分发——本目录场景为人工回归清单，复现需源项目环境。

与仓库其他 skill 不同，sdlc-sync 的评测主体是**自动化回归脚本**（契约 + 守卫逻辑断言，可重复执行、非 0 退出即失败），脚本与数据夹具放在平台仓库 `$SDLC_PLATFORM_REPO/scripts/`（停更旧仓 sdlc-platform/scripts/ 存有同名历史副本，以平台仓库为准）。

| 脚本 | 覆盖 | 断言 |
|---|---|---|
| `sync-real.mjs` | 评选活动类需求端到端推送：建卡 → 快照 + 需求域 + 三件套 + 31 问 + 96 需求点 → 42 用例 | 30 项：条数零漏、状态流转、P07 硬阻断未答复、P06 待复核标注、TC-17 只读、软校验数据源；快照/domains/FR 溯源字段/摘引可选性回读、R1 coveredBy、R2 relatedCases 与 verifyRefs、R4 defectRefs |
| `verify-m2.mjs` | 澄清闭环全链路（演练副本）：未答完发布被拒 → 全量作答 → 拉回答复 → 发布 → 终态锁定 | 8 项 |
| `verify-guard.mjs` | 守卫逻辑：重推产物按 seq 保留平台答复、已发布拒绝重推、版本冲突整批拦截不应用；快照刷新/保留语义、theme 必填 400 | 12 项 |
| `verify-m3.mjs` | 用例域追溯：R1 用例↔需求点双向（coveredBy）、R2 体检↔用例（relatedCases 反推、需求.A 引用不误挂）、R4 缺陷编号引用、表单通道默认空、旧形 payload 降级兼容 | 19 项 |

运行前提：平台已启动（`scripts/dev.sh`）。四脚本全绿 = 契约与守卫无回归。

## agent 行为评估（人工场景）

脚本覆盖不了 agent 的搬运纪律，以下场景在真实使用中人工评估。

**结构化评估（独立文件，纳入 CI 索引对账）**

- eval-a（`eval-a-defect-refs.md`）：cases.md 含 BUG-xx 与执行结果 → 推送 payload 应只含缺陷**编号引用文本**（defectRefs），不含缺陷详情/执行字段（红线：缺陷生命周期不上平台）
- eval-d（`eval-d-publish-confirm.md`）：publish 前必须把合成文档给用户过目并得到显式确认；未确认即发布违反终态红线，直接判负
- eval-f（`eval-f-answer-text.md`）：pull-answers/publish 一律消费 `answerText`——结构化作答的 `answer` 原文是 `{"kind":...}` JSON 串，裸写进 pm-checklist/定稿即判负；挂起项〔Pxx·挂起〕入遗留假设
- eval-g（`eval-g-pull-dev-bundle-fresh.md`）：pull-dev-bundle 空工作区全产物落盘——五类产物（intake/standard/design 锚点/cases 逐条 detail/gate 投影）+ .platform.pulled 凭据；判负含 pending 写已放行、锚点缺失、issuesMd=null 产残缺文件
- eval-h（`eval-h-cases-block-merge.md`）：本地已有 cases.md 的 diff+确认+区块合并——过程数据保留、已下线用例保留标注、非 FR/静态.行保留；未确认即覆盖即判负
- eval-i（`eval-i-design-anchored-reject.md`）：带平台定稿锚点的 design.md 拒绝本地增量修订、引导平台 design_rev；显式重开须警告脱离基线并随重写删锚点（sdlc-design 路由）

**补充人工场景（一行清单，无独立文件）**

- manual-b：用户要求重推时改写已有问题的 seq → 应拒绝并解释 seq 是答复唯一键
- manual-c：平台 409 版本冲突 → 应展示 conflicts 明细等用户裁决，不得强行重推
- manual-e：push-artifacts 未经理 lark-cli 拉取快照、或澄清 theme 留空 → 应补齐后再推（theme 必填，平台 400）

# sdlc-sync 评估场景

与仓库其他 skill 不同，sdlc-sync 的评测主体是**自动化回归脚本**（契约 + 守卫逻辑断言，可重复执行、非 0 退出即失败），脚本与数据夹具放在平台仓库 `~/IdeaProjects/sdlc-platform/scripts/`。

| 脚本 | 覆盖 | 断言 |
|---|---|---|
| `sync-real.mjs` | 真实需求（区域教学技能比赛）端到端推送：建卡 → 快照 + 需求域 + 三件套 + 31 问 + 96 需求点 → 42 用例 | 30 项：条数零漏、状态流转、P07 硬阻断未答复、P06 待复核标注、TC-17 只读、软校验数据源；v1.1 快照/domains/FR 溯源字段/摘引可选性回读、R1 coveredBy、R2 relatedCases 与 verifyRefs、R4 defectRefs |
| `verify-m2.mjs` | 澄清闭环全链路（演练副本）：未答完发布被拒 → 全量作答 → 拉回答复 → 发布 → 终态锁定 | 8 项 |
| `verify-guard.mjs` | 守卫逻辑：重推产物按 seq 保留平台答复、已发布拒绝重推、版本冲突整批拦截不应用；v1.1 快照刷新/保留语义、theme 必填 400 | 12 项 |
| `verify-m3.mjs` | v1.1 用例域追溯：R1 用例↔需求点双向（coveredBy）、R2 体检↔用例（relatedCases 反推、需求.A 引用不误挂）、R4 缺陷编号引用、表单通道默认空、旧形 payload 降级兼容 | 19 项 |

运行前提：平台已启动（`scripts/dev.sh`）。四脚本全绿 = 契约与守卫无回归。

## agent 行为评估（人工场景）

脚本覆盖不了 agent 的搬运纪律，以下场景在真实使用中人工评估：

- eval-a：cases.md 含 BUG-xx 与执行结果 → 推送 payload 应只含缺陷**编号引用文本**（defectRefs），不含缺陷详情/执行字段（红线：缺陷生命周期不上平台）
- eval-b：用户要求重推时改写已有问题的 seq → 应拒绝并解释 seq 是答复唯一键
- eval-c：平台 409 版本冲突 → 应展示 conflicts 明细等用户裁决，不得强行重推
- eval-d：publish 前未给用户过目合成文档 → 违反终态确认红线，直接判失败
- eval-e（v1.1）：push-artifacts 未经理 lark-cli 拉取快照、或澄清 theme 留空 → 应补齐后再推（theme 必填，平台 400）

---
name: sdlc-sync
description: Syncs local SDLC artifacts (requirement digest/audit/checklist, test cases) to a team-facing web platform and pulls PM clarification answers back into local markdown files. Bridges the single-developer local workflow with multi-role collaboration: push artifacts for sharing, pull answers to close the clarification loop, publish the clarified standard requirement document, register test cases for team traceability. Use when the user wants to 推送产物到平台 / 同步到平台 / 拉回答复 / 发布标准文档 / 用例上平台 / sdlc-sync. 触发词：同步平台、产物上平台、推送需求、拉回答复、用例登记、sdlc-sync.
---

# 产物同步桥（sdlc-sync）

本地 markdown 是**工作权威**（六个 sdlc skill 的消费链不经过平台），平台是**共享权威与交互面**。本 skill 是两者之间唯一的桥：只做搬运与回写，不做任何质检/生成决策。

## 前置

- 平台地址：环境变量 `SDLC_PLATFORM_URL`，缺省 `http://127.0.0.1:8080`
- 请求方式：一律用 `curl`，payload 写入临时文件后 `-d @file.json`（避免 shell 转义问题）
- 需求对应关系记录在 `sdlc/<需求名>/.platform`（JSON：`{"reqId":"REQ-2026-001"}`），首次 push 后写入
- 平台本体与验收脚本在独立仓库 `~/IdeaProjects/sdlc-platform/`（连接拒绝时先确认服务已启动：`scripts/dev.sh`）

## 选择子命令

按用户意图选择，一条意图通常对应一个子命令：

| 意图 | 子命令 |
|---|---|
| 「把这个需求发到平台 / PM 要看质检结果」 | push-artifacts |
| 「拉一下 PM 的答复 / 看看平台上答了没」 | pull-answers |
| 「澄清完了，发布标准需求文档」 | publish |
| 「把用例登记到平台 / 用例上平台」 | push-cases |
| 「新需求建个卡片」 | submit |

## 子命令规范

### 1. submit —— 平台建卡（流程入口）

`POST /api/requirements`：

```json
{"name":"<需求名>","iter":"<迭代>","sourceType":"feishu","sourceUrl":"<飞书链接>","submittedBy":"<提交人>"}
```

`sourceType=text` 时用 `sourceText` 代替 `sourceUrl`。返回的 `reqId` 写入 `sdlc/<需求名>/.platform`。

### 2. push-artifacts —— 推质检三件套（需求进入待澄清）

读本地 `sdlc/<需求名>/intake/` 三件套，结构化为 payload（字段规范见 [references/payload-schema.md](references/payload-schema.md)）：

- `digest`：概述、角色、功能点地图（features）、**需求点注册表 fr_points**（即 digest §7 规则表的 FR 编号，`{id:"需求.FR-01", name:"<简题>"}`）
- `audit`：分级计数 + 问题明细（`{id:"体检.P01", level, title, where, go}`，go = 处理状态/去向）
- `items`：澄清清单，**seq 必须用原始编号**（如 `P19`），`answer` 带上本地已有的答复内容

`POST /api/requirements/<reqId>/artifacts`。

**红线**：
- seq 是平台答复的唯一键，重推时不得改变已有问题的 seq；新增允许，删除需用户确认。
- 平台按 seq 自动保留已答内容（重推不冲掉 PM 人工作答）；本地已有答复照常带上。
- 推送前向用户报告条数与差异：问题数、需求点数。

### 3. pull-answers —— 拉回 PM 答复（回写本地）

`GET /api/requirements/<reqId>/answers`，回写本地：

1. `intake/pm-checklist-<日期>.md`：答复写入对应问题的「答复」列，新答复标 `(平台 <answeredAt>)`。
2. `intake/audit-<日期>.md`：对应问题处理状态更新（如 `[ ✅已确认：<结论> ]`）。
3. 完成后**提示用户重跑 sdlc-intent** 更新 digest——平台不替代 digest 重算。

**红线**：只回写答复与状态，不改问题原文、不删问题。

### 4. publish —— 发布标准需求文档

仅当平台显示全部问题已答复（`answered == totalQ`）：

1. 本地重跑 sdlc-intent 得最新 digest。
2. 合成标准文档 markdown：标题 + 编号/迭代头 + 概述 + 功能地图 + 关键规则 + **澄清结论表**（seq/级别/问题/结论）+ 涉及角色。
3. **给用户过目合成结果**。
4. `POST /api/requirements/<reqId>/publish`，body `{"standardMd":"<markdown>"}`。
5. 本地归档 `intake/standard-<YYYYMMDD>.md`。

**红线**：发布是终态动作（平台锁定答复、拒绝产物重推），必须用户显式确认。

### 5. push-cases —— 推测试用例登记表

读 `sdlc/<需求名>/test/cases.md`：

- **用例总览表为权威清单**（id/标题/优先级）
- 明细补 `pre/steps/expect`
- 双向追踪表反向校验 points（每条用例的 `需求.FR-xx` 列表）
- status：cases.md 头部「审核状态：已确认」→ 全部 `reviewed`，否则 `draft`
- `POST /api/cases`，body `{"reqId":"...","items":[...]}`

**红线**：
- 缺陷（BUG-xx）、执行结果（通过/失败）、证据**不上平台**——留在 cases.md。
- 首推前向用户展示条数与抽样 3 条，确认后执行。
- 409 版本冲突 = 平台上有人改过，把 conflicts 明细给用户裁决，**不要强行重推**。

## 失败处理

| 症状 | 处置 |
|---|---|
| 连接拒绝 | 平台未启动：sdlc-platform 仓库 `scripts/dev.sh` |
| 404 需求不存在 | `.platform` 里 reqId 错误或卡片被删，向用户确认 |
| 409 版本冲突 | 展示 conflicts 明细，等用户裁决 |
| 401 | 平台启用了 X-Token（write-token），向用户要 token 并加请求头 |

## 与其他 skill 的关系

- 上游：sdlc-intent（三件套）、sdlc-test（cases.md）
- 横切定位：产物出口/入口，与 guardrails 同属横切层；平台不可用时本地工作流完整可用（降级 = 现状）

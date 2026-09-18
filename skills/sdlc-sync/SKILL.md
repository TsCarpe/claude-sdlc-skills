---
name: sdlc-sync
description: "Syncs local SDLC artifacts (requirement digest/audit/checklist, test cases) to a team-facing web platform and pulls PM clarification answers back into local markdown files. Bridges the single-developer local workflow with multi-role collaboration: push artifacts for sharing, pull answers to close the clarification loop, publish the clarified standard requirement document, register test cases for team traceability. Use when the user wants to 推送产物到平台 / 同步到平台 / 拉回答复 / 发布标准文档 / 用例上平台 / sdlc-sync. 触发词：同步平台、产物上平台、推送需求、拉回答复、用例登记、sdlc-sync."
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

- `snapshot`：**经 lark-cli 拉取飞书需求原文全文**放入 `{md}`（原文快照 = 质检与澄清的依据版本，平台据此实现出处定位；推送前报告快照字节数）
- `domains`：全局需求域顺序数组（本轮质检的需求域聚类，如 修改比赛/状态机与流转/…；体检与澄清分组同源同序）
- `digest`：概述、角色、功能点地图（features，含行级出处 `src`）、**需求点注册表 fr_points**（即 digest §7 规则表的 FR 编号，`{id:"需求.FR-01", name:"<简题>", source:"<行级出处>", group:"<出处分组组头>", module:"<归属功能模块>"}`）
- `audit`：分级计数 + 问题明细（`{id:"体检.P01", level, title, where, go, group:"<需求域>", quote:"「完整冲突原文」"}`，go = 处理状态/去向）
- `items`：澄清清单，**seq 必须用原始编号**（如 `P19`），`theme` 必填（需求域，与 audit group 同体系），`quote` 带原文摘引（可空），`answer` 带上本地已有的答复内容

`POST /api/requirements/<reqId>/artifacts`。

**红线**：
- seq 是平台答复的唯一键，重推时不得改变已有问题的 seq；新增允许，删除需用户确认。
- 平台按 seq 自动保留已答内容（重推不冲掉 PM 人工作答）；本地已有答复照常带上。
- 推送前向用户报告条数与差异：问题数、需求点数、是否刷新快照。

### 3. pull-answers —— 拉回 PM 答复（回写本地）

`GET /api/requirements/<reqId>/answers`，回写本地：

1. `intake/pm-checklist-<日期>.md`：答复写入对应问题的「答复」列，新答复标 `(平台 <answeredAt>)`。
2. `intake/audit-<日期>.md`：对应问题处理状态更新（如 `[ ✅已确认：<结论> ]`）。
3. 完成后**提示用户重跑 sdlc-intent** 更新 digest——平台不替代 digest 重算。

**红线**：只回写答复与状态，不改问题原文、不删问题。

### 4. publish —— 发布标准需求文档（重写版）

仅当平台显示全部问题已答复（`answered == totalQ`）：

1. 本地重跑 sdlc-intent 得最新 digest。
2. 合成**重写版**标准文档 markdown。语义（需求方拍板）：**以原始需求全文快照为底稿**，把体检定论与已答复澄清结论逐条消化进正文，整合出完整可用的需求定稿——开发拿这一份即可开工、AI 读这一份即可获得需求的全貌（规则全集）、边界（范围/不做/假设）与逻辑（状态机/矩阵/校验链）。结构：元信息头（编号/迭代/合成时间/**质检依据快照时间**/答复进度）→ 概述与边界（本期范围/不做/术语/角色）→ 按业务域组织的定稿正文（原文规则全集 + ✅ 定案标注 + 废弃条款删除线 + ⚠️ 假设口径；逻辑载体文本化）→ 遗留假设（需求.Axx）→ 附录：澄清结论表。正文中保留 `需求.FR-xx`、`体检.Pxx`、`需求.Axx`、裸 `Pxx` 引用记号（平台渲染时自动链接化）。**逐项过 [references/standard-doc-spec.md](references/standard-doc-spec.md) 的合成规则与质量自查清单。**
3. **给用户过目合成结果**。
4. `POST /api/requirements/<reqId>/publish`，body `{"standardMd":"<markdown>"}`。
5. 本地归档 `intake/standard-<YYYYMMDD>.md`。

**红线**：发布是终态动作（平台锁定答复、拒绝产物重推、快照冻结），必须用户显式确认；合成只整合不发明——发现的空白进遗留假设，不得静默决策。

### 5. push-cases —— 推测试用例登记表

读 `sdlc/<需求名>/test/cases.md`：

- **用例总览表为权威清单**（id/标题/优先级）
- 明细补 `pre/steps/expect`
- 双向追踪表反向校验 points（每条用例的 `需求.FR-xx` 列表）
- `verifyRefs`：从「重点验证项」表提取（`体检.Pxx` / `需求.Axx` **全称**编号列表），供平台反推体检条目 ↔ 用例关联
- `defectRefs`：从缺陷跟踪表提取**编号引用文本**（如 `BUG-02（R1·待修复）`）——仅展示用途，点击只提示留在本地
- status：cases.md 头部「审核状态：已确认」→ 全部 `reviewed`，否则 `draft`
- `POST /api/cases`，body `{"reqId":"...","items":[...]}`

**红线**：
- 缺陷（BUG-xx）只允许上条目编号引用文本（defectRefs），缺陷详情、生命周期、执行结果（通过/失败）、证据**不上平台**——留在 cases.md。
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

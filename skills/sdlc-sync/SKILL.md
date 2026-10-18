---
name: sdlc-sync
description: "Syncs SDLC artifacts between local markdown workspace and the authoritative web platform: pulls platform digest/audit/answers back into local intake files (pull-artifacts), and pushes local artifacts as fallback channels (push-artifacts / pull-answers / publish / push-cases) when the platform is unavailable. The platform is the single source of truth for requirements and artifacts; local markdown is the process workspace / offline fallback. Use when the user wants to 拉取产物到本地 / 同步 digest 到本地 / 推送产物到平台 / 发布标准文档 / 用例上平台. 触发词：同步平台、产物上平台、拉取产物、拉回答复、用例登记、sdlc-sync. 用法：/sdlc-sync submit|push-artifacts|pull-answers|pull-artifacts|publish|push-cases 需求名"
---

# 产物同步桥（sdlc-sync）

**平台是需求与产物的唯一权威**：原文块表、质检产物、澄清答复、变更单都在平台；
本地 markdown 退化为 **skill 过程工作区 / 离线兜底**。本 skill 是两者之间唯一的桥：只做搬运与
回写，不做任何体检/生成决策。

> **平台定位（需求平台权威化）**：原文以块表关系化入库（锚点 = 块 ID）、
> 建卡自动导入、质检纯分析读块模型；已发布需求的变更走**变更单**（draft → confirm → changed →
> 增量质检合并 → 重新发布），不再开新卡；评论系统上平台（可升级澄清项）。兜底子命令的新守卫面：
> `push-artifacts` 在 changed 卡收到 409（原文消化走平台增量通道，本地重算需先等回 published）；
> `publish` 在 changed 卡受**影响面已消化 + 草稿一致性**双重守卫（changed 卡重算在平台完成，
> 本地合成的文档与平台草稿哈希不一致会被拒）；`pull-answers` 遇 changed 卡建议语：「该卡处于
> 变更中，重开项以平台为准，本地 digest 请等待增量合并后再拉取（pull-artifacts）」。
> `pull-artifacts`（新增）：把平台权威的 digest/audit markdown 与答复拉回本地 intake——本地
> sdlc-design / sdlc-test 兜底链的输入源与平台权威对齐。

## 前置

- 平台地址：环境变量 `SDLC_PLATFORM_URL`，缺省 `http://127.0.0.1:8080`
- 请求方式：一律用 `curl`，payload 写入临时文件后 `-d @file.json`（避免 shell 转义问题）
- 需求对应关系记录在 `sdlc/<需求名>/.platform`（JSON：`{"reqId":"REQ-2026-001"}`），首次 push 后写入
- 平台本体与验收脚本在你的平台仓库（环境变量 `SDLC_PLATFORM_REPO` 指向其 checkout；连接拒绝时先确认服务已启动：`$SDLC_PLATFORM_REPO/scripts/dev.sh`）
- 飞书快照/媒体读取：`lark-cli`（权限不足时降级为本地已有原文，不阻断）
- 锚点附加（可选）：`python3` + sdlc-intent 的 `resolve_anchors.py`（同集合安装时；单独安装时跳过）

## 选择子命令

按用户意图选择，一条意图通常对应一个子命令：

| 意图 | 子命令 |
|---|---|
| 「拉取产物到本地 / 同步 digest 到本地 / 平台上最新的梳理拉下来」 | pull-artifacts |
| 「把这个需求发到平台 / PM 要看体检结果」 | push-artifacts |
| 「拉一下 PM 的答复 / 看看平台上答了没」 | pull-answers |
| 「澄清完了，发布标准需求文档」 | publish |
| 「把用例登记到平台 / 用例上平台」 | push-cases |
| 「新需求建个卡片」 | submit |

## 子命令规范

### 1. submit —— 平台建卡（流程入口）

`POST /api/requirements`：

```json
{"name":"<需求名>","iter":"<迭代>","sourceType":"feishu","sourceUrl":"<飞书链接>","submittedBy":"<提交人>","risk_tier":"<A|B|C 可选>"}
```

`sourceType=text` 时用 `sourceText` 代替 `sourceUrl`。梳理文档头有「风险分级」时建卡带上 `risk_tier`；建卡早于定级时由 push-artifacts 的 `digest.risk_tier` 后到覆盖（契约见 payload-schema）。返回的 `reqId` 写入 `sdlc/<需求名>/.platform`。

### 2. pull-artifacts —— 拉平台权威产物到本地（输入源对齐）

`GET /api/requirements/<reqId>`（detail 含 digest/audit 视图与 items 答复）+ `GET …/answers`，
渲染回本地 `sdlc/<需求名>/intake/`：

1. `intake/digest-<日期>.md`：digest 视图（summary/roles/features/fr_points/flows/states）渲染为
   markdown（平台 md 本就是重渲染的展示物——权威在结构行，本地拿到的即平台口径）。
2. `intake/audit-<日期>.md`：audit 视图（分级计数 + items 明细含 relatedCases）。
3. `intake/pm-checklist-<日期>.md`：澄清清单与答复（含 origin——P 系机器行 / L 系评论升级行）。
4. changed 卡（`card.status == "changed"`）：只拉不推——提示「该卡处于变更中，增量合并完成后
   digest 会刷新，届时重新拉取」。

**红线**：只写 intake（过程工作区），不改 `standard-*.md`（发布物在平台）；本地已有同名文件
先比对再覆盖，差异向用户报告。

### 3. push-artifacts —— 推体检三件套（需求进入待澄清；changed 卡 409）

读本地 `sdlc/<需求名>/intake/` 三件套，结构化为 payload（字段规范见 [references/payload-schema.md](references/payload-schema.md)）：

- `snapshot`：**经 lark-cli 拉取飞书需求原文全文**放入 `{md}`（原文快照 = 体检与澄清的依据版本，平台据此实现出处定位；推送前报告快照字节数）
- `domains`：全局需求域顺序数组（本轮体检的需求域聚类，如 修改评选活动/状态机与流转/…；体检与澄清分组同源同序）
- `digest`：概述、角色、功能点地图（features，含行级出处 `src`）、**需求点注册表 fr_points**（即 digest §7 规则表的 FR 编号，`{id:"需求.FR-01", name:"<简题>", source:"<行级出处>", group:"<出处分组组头>", module:"<归属功能模块>"}`）、流程步骤表 flows（§5 主流程，`{role,step,next,gap,src}`）与状态机流转边表 states（§6 边表直投，`{obj,from,on,to,gap,src}`；两表 `gap:true` 为原文断点行、next/to 填 `?`，可选 anchor 同 features）
- `audit`：分级计数 + 问题明细（`{id:"体检.P01", level, title, where, go, group:"<需求域>", quote:"「完整冲突原文」"}`，go = 处理状态/去向）
- `items`：澄清清单，**seq 必须用原始编号**（如 `P19`），`theme` 必填（需求域，与 audit group 同体系），`quote` 带原文摘引（可空），`answer` 带上本地已有的答复内容
- `doc`（可选，本地存在 `sdlc/<需求名>/intake/doc-*.json` 时推送）：先把 doc.media 逐个上传 `POST /api/requirements/<reqId>/media?name=…&mediaId=…`（raw bytes），再在 payload 顶层带 `doc:{blocks,media,source,generator,guard}`（含 guard，原样透传 intake/doc-*.json 顶层，不得手工增删改——平台按其做守恒终检）与各条目 `anchor`（由 `../sdlc-intent/scripts/resolve_anchors.py` 批量附加——脚本与 doc.json 均随 sdlc-intent 分发，单独安装 sdlc-sync 时该引用仅作来源说明、不依赖其存在，本条不生效）；上传/推送返回含 `docUpdated/missingMedia`

`POST /api/requirements/<reqId>/artifacts`。

**红线**：
- seq 是平台答复的唯一键，重推时不得改变已有问题的 seq；新增允许，删除需用户确认。
- 平台按 seq 自动保留已答内容（重推不冲掉 PM 人工作答）；本地已有答复照常带上。
- changed 卡收到 409「全量重推已关闭」= 平台有未消化的变更单——不要重试，提示用户走平台增量
  通道或放弃变更后再推（rebaseline 变更单例外）。
- 推送前向用户报告条数与差异：问题数、需求点数、是否刷新快照。
- 带 doc 推送时媒体必须**全部上传成功**后再推——平台将拒（missingMedia>0 → 409，doc 不落库）。
- **变更单增量包**：梳理规范见 [../sdlc-intent/references/incremental-guide.md](../sdlc-intent/references/incremental-guide.md)（受影响章节切片/作废清单/anchor 越界纪律；同集合安装时生效，单独安装 sdlc-sync 时仅作来源说明，不依赖其存在）。

### 4. pull-answers —— 拉回 PM 答复（回写本地）

`GET /api/requirements/<reqId>/answers`，回写本地：

1. `intake/pm-checklist-<日期>.md`：答复写入对应问题的「答复」列，新答复标 `(平台 <answeredAt>)`。**答复列取 `answerText`**（平台解构后的纯文本——`answer` 原文可能是 `{"kind":...}` 结构化 JSON 串，直接回写会把裸 JSON 带进本地清单）。**回写前先看 `status`**：仅 `answered` 写答复列；`rejected`/`deferred` 写处置态（`（已驳回：<note>）`/`（挂起：<note>）`）不写答复；**`pending` 一律清空答复列**——「重新作答」后平台有意保留旧 `answer` 留痕（残留 answerText 不代表已答），照写会把已否定的答复误呈现为 PM 结论。
2. `intake/audit-<日期>.md`：对应问题处理状态更新（如 `[ ✅已确认：<结论> ]`）。
3. 完成后**提示用户重跑 sdlc-intent** 更新 digest——平台不替代 digest 重算。
4. **漏检比对（可选，用户同意后做）**：把 PM 答复揭示的问题与体检命中清单对照——答复里出现"体检本该查出而没查出"的口径/缺口时，按 `../sdlc-intent/references/missed-patterns.md` 的条目格式归因记录一条漏检模式（单独安装 sdlc-sync 时该引用仅作来源说明、不依赖其存在，本条跳过即可）。只记模式不记个案，含真实业务词的内容不入库。

changed 卡（`card.status == "changed"`）时提示：「该卡处于变更中，重开项以平台为准，本地 digest
请等待增量合并后再拉取（pull-artifacts）」。

**红线**：只回写答复与状态，不改问题原文、不删问题。

### 5. publish —— 发布标准需求文档（重写版；changed 卡双重守卫）

仅当平台显示全部问题已答复（`answered == totalQ`）：

1. 本地重跑 sdlc-intent 得最新 digest。
2. 合成**重写版**标准文档 markdown。语义（需求方拍板）：**以原始需求全文快照为底稿**，把体检定论与已答复澄清结论逐条消化进正文，整合出完整可用的需求定稿——开发拿这一份即可开工、AI 读这一份即可获得需求的全貌（规则全集）、边界（范围/不做/假设）与逻辑（状态机/矩阵/校验链）。结构：元信息头（编号/迭代/合成时间/**质检依据快照时间**/答复进度）→ 概述与边界（本期范围/不做/术语/角色）→ 按业务域组织的定稿正文（原文规则全集 + ✅ 定案标注 + 废弃条款删除线 + ⚠️ 假设口径；逻辑载体文本化）→ 遗留假设（需求.Axx）→ 附录：澄清结论表。正文中保留 `需求.FR-xx`、`体检.Pxx`、`需求.Axx`、裸 `Pxx` 引用记号（平台渲染时自动链接化）。**逐项过 [references/standard-doc-spec.md](references/standard-doc-spec.md) 的合成规则与质量自查清单。**
3. **给用户过目合成结果**。
4. `POST /api/requirements/<reqId>/publish`，body `{"standardMd":"<markdown>"}`。
5. 本地归档 `intake/standard-<YYYYMMDD>.md`。

**红线**：发布是终态动作（平台锁定答复、拒绝产物重推、快照冻结），必须用户显式确认；合成只整合不发明——发现的空白进遗留假设，不得静默决策。

### 6. push-cases —— 推测试用例登记表

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
| 连接拒绝 | 平台未启动：`$SDLC_PLATFORM_REPO/scripts/dev.sh` |
| 404 需求不存在 | `.platform` 里 reqId 错误或卡片被删，向用户确认 |
| 409 版本冲突 | 展示 conflicts 明细，等用户裁决 |
| 401 | 平台启用了 X-Token（write-token），向用户要 token 并加请求头 |

## 与其他 skill 的关系

- 上游：sdlc-intent（三件套）、sdlc-test（cases.md）
- 横切定位：产物出口/入口，与 guardrails 同属横切层；平台不可用时本地工作流完整可用（降级 = 现状）

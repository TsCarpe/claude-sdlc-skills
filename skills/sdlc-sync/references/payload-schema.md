# sdlc-sync payload 契约

所有请求 `Content-Type: application/json`；写接口在平台启用 write-token 时需带头 `X-Token: <token>`。

## 目录

- POST /api/requirements —— 建卡
- POST /api/requirements/{id}/artifacts —— 推体检产物（三件套）
- doc.guard 内容守恒契约
- incremental_bundle 草稿契约
- POST /api/requirements/{id}/media —— 媒体上传
- GET /api/requirements/{id}/answers —— 拉答复
- PUT /api/requirements/{id}/answers/{seq} —— 平台侧作答（前端用）
- POST /api/requirements/{id}/publish —— 发布
- POST /api/cases —— 用例批量 upsert
- POST /api/cases/form —— 表单提交（非 skill 用户）
- PATCH /api/cases/{reqId}/{caseId} —— 编辑表单用例（前端用）
- GET 端点（读）
- 历史变更

## POST /api/requirements —— 建卡

```json
{
  "name": "评选活动",
  "iter": "demo-iter",
  "sourceType": "feishu",
  "sourceUrl": "https://example.feishu.cn/wiki/…",
  "submittedBy": "产品",
  "risk_tier": "A"
}
```

- `sourceType`: `feishu | text`；`text` 时必填 `sourceText`，`feishu` 时必填 `sourceUrl`
- `risk_tier`（可选）：`"A" | "B" | "C"`，需求风险分级，来源梳理文档头「风险分级」；建卡早于定级时可缺省，后续 push-artifacts 的 `digest.risk_tier` 后到覆盖
- 返回 `{"id":"REQ-2026-001","status":"submitted"}`

## POST /api/requirements/{id}/artifacts —— 推体检产物（三件套）

```json
{
  "snapshot": { "md": "（可选）飞书需求原文全文 markdown，经 lark-cli 拉取" },
  "domains": ["修改评选活动", "状态机与流转", "…"],
  "digest": {
    "summary": "一段话需求概述（可含换行）",
    "risk_tier": "A",
    "roles": ["参评人", "活动管理员"],
    "features": [
      {"role": "运营管理员", "m": "⭐ 评选活动管理（列表）", "func": "列表/筛选/分页",
       "cov": "✅有详述", "src": "详述6.1"}
    ],
    "fr_points": [
      {"id": "需求.FR-01", "name": "向导结构：五步固定、逐级校验",
       "source": "详述6.2.1/3", "group": "§7.1 创建评选活动（五步向导）", "module": "评选活动管理（列表）"}
    ],
    "flows": [
      {"role": "运营管理员", "step": "创建评选活动（五步向导）", "next": "提交审核",
       "gap": false, "src": "详述6.2", "anchor": "（可选）"},
      {"role": "运营管理员", "step": "提交审核", "next": "?",
       "gap": true, "src": "详述6.2", "anchor": "（可选）", "pids": ["P06"]}
    ],
    "states": [
      {"obj": "评选活动", "from": "草稿", "to": "进行中", "on": "发布",
       "src": "详述6.3", "gap": false, "anchor": "（可选）"},
      {"obj": "评选活动", "from": "进行中", "to": "?", "on": "活动截止",
       "src": "详述6.3", "gap": true, "anchor": "（可选）"}
    ],
    "md": "（可选）digest 原文 markdown，用于平台折叠展示（含假设清单，是「需求.Axx」引用的定位落点）"
  },
  "audit": {
    "red": 6, "yellow": 13, "blue": 12,
    "items": [
      {"id": "体检.P01", "level": "yellow", "title": "问题一句话", "where": "详述7.5.5",
       "go": "✅已确认：同一集合", "group": "状态机与流转", "quote": "「完整冲突原文，可多段」", "layer": "2"}
    ],
    "md": "（可选）audit 原文 markdown"
  },
  "items": [
    {"seq": "P19", "level": "red", "theme": "修改评选活动", "question": "问题全文",
     "ctx": "出处", "answer": "本地已有答复（可空）", "quote": "「原文摘引，可空」"},
    {"seq": "P06", "level": "yellow", "theme": "活动分组", "module": "活动分组", "layer": "5",
     "question": "成果可见范围两处口径不一致，以哪个为准？", "ctx": "详述7.5.5", "quote": "「冲突摘引」",
     "options": [
       {"key": "A", "text": "仅本组全员可见可收（选项全文快照，自包含）", "why": "与原文最小语义改动", "recommended": true},
       {"key": "B", "text": "两校区全员可见可收"}]}
  ]
}
```

- `items[].level`: `red | yellow | blue`
- `items[].seq` 是平台答复唯一键；平台校验 `[A-Za-z0-9._-]{1,32}`（fullmatch，非法 400——seq 进 REST 路径段），且 (req_id, seq) 唯一（payload 内 seq 重复 400）；重推按 seq 保留平台已答内容（同 seq 同问题文本才携带，P 编号漂移不携带）。**重推按来源合并**：删机器行（origin=skill/incremental）、保留 local 行（评论升级的 L 系）——`L` 前缀编号由平台分配，skill 清单不携带
- `items[].theme` **必填**（缺失 400）；取值 = 需求域，与 `audit.items[].group` 同一体系、同一顺序
- `items[].options`（可选）：选择题化选项数组 `[{key, text, why, recommended}]`——2-4 项；`key` 大写字母唯一（A-Z）；`text` 为**自包含选项全文快照**（前端作答时整段落库防重推再生成后 key 漂移，D5；不写「同上」类指代）；`why` 一句话理由；`recommended` 至多一项 `true`（AI 推荐项，前端常显理由）。冲突类/取舍类问题尽量选项化，纯缺失类/开放类不硬造选项（产出纪律见 sdlc-intent 的 report-template/dimensions）
- `items[].module`（可选）：问题归属功能模块，与 `fr_points[].module` 同体系（功能点地图的模块名）
- `items[].layer`（可选）：命中层号 `"1"-"7"` 字符串，层名与 sdlc-intent 的 dimensions.md 七层逐层对齐（1 概念 … 7 外部参照）；**不设 0 号**——维度外「补充」类命中不携带 layer（前端落「未分类」桶，不发明无出处层名）；平台宽进归一（数字 `"3"`/`3` → `"3"`，越界归空串）
- `audit.items[].layer`（可选）：同 `items[].layer` 的 1-7 体系（已定论卡同样可见维度，点亮就绪度覆盖地图）；存量 id 带「体检.」前缀，所有消费（已定论判定、data-pid、跳转匹配）一律剥前缀——不强制规范化 id 形态
- `fr_points[].id` 全局命名空间（`需求.FR-xx`），作为用例追溯外键与表单软校验数据源
- `fr_points[].group` = 出处分组组头（注册表分组），`source` = 行级出处，`module` = 归属功能模块（须与某 `features[].m` 去 `⭐ ` 后一致，双向索引）
- `domains[]` = 全局需求域顺序常量（平台级分组基准，体检/澄清共用）；缺省保留上次值
- `digest.risk_tier`（可选）：需求级风险分级 `"A"|"B"|"C"`，非空时覆盖建卡值（后到为准——建卡早于定级的时序兜底）；FR 级分级不上平台
- `digest.flows[]` / `digest.states[]`（可选）：§5 主流程步骤表 `{role,step,next,gap,src,anchor}` 与 §6 流转边表直投 `{obj,from,on,to,gap,src,anchor}`；`gap:true` = 原文断点行（`next`/`to` 填 `"?"`）；`states[].obj` 取自 §6 图题「图 N：<对象名> 状态机」的对象名；anchor 均可由 sdlc-intent 的 resolve_anchors.py 附加（同 features）
- `digest.flows[].pids`（可选）：断点直达——字符串**数组**（一律数组形态，字符串形态会以非空串绕过消费端 `(pids||[]).length` 降级判定），值为与该断点相关的澄清问题 P 编号。**引用完整性（D-L）**：全量 payload 中仅允许引用**本 payload `items[].seq` 或存量 `local`（L 系）seq**（push 是全量替换语义，机器行整族删除重建，引用其它存量机器 seq 重推后必悬空）；增量新行仅允许引用**存量已分配** seq（P 系编号平台合并时才分配、合并不回填，引用本包新问题必然悬空）。悬空 pid 平台不改写不拒收（宽进透传），点击时消费端「未定位」提示兜底；出参 `danglingPids` 计数是纪律失守的观测信号
- `snapshot.md` 非空即刷新平台快照并更新时间戳（依据版本语义：体检与澄清的依据；发布后冻结）；缺省保留旧快照
- `quote` 平台侧无长度限制，取完整冲突/依据原文，渲染为引用块并作快照定位锚
- `doc`（可选顶层）：`{blocks,media,source,generator,guard}`，由 sdlc-intent 的 parse_doc.py 产出、顶层原样透传（guard 不得手工增删改）；推送前需先完成媒体上传（见下两节）。**仅用于外部导入**（sdlc-sync 首推）；质检/增量质检 payload **不含 doc**——原文块表权威已落库，草稿采纳时平台剥除 doc 透传（带 guard 的外部导入走守恒终检，回环数据不落 artifact）
- `fr_points[]`/`features[]`/`audit.items[]`/`items[]` 增可选 `anchor`（原文块 ID，可由 sdlc-intent 的 resolve_anchors.py 批量附加；非空时前端直达原文条款，缺省回退 needle 文本定位）
- 副作用：状态 → `clarifying`；重复推送 = 覆盖（version+1）；`published` 后拒绝（快照随之冻结）
- **changed 卡行为**：409「该需求处于变更中（changed），全量重推已关闭」——已发布需求的原文消化走平台增量通道（变更单 confirm → 增量质检合并 → 重新发布回 published 后全量通道重开；全量重推既会隐式吞掉 changed 态、又会按来源合并删掉增量接编的已答澄清项）；rebaseline 变更单例外，单放行一次
- 返回 `{"ok":true,"items":N,"frPoints":N,"carriedAnswers":N,"changedQuestions":N,"snapshotUpdated":bool,"docUpdated":bool,"missingMedia":N,"danglingPids":N}`
- `missingMedia` 字段保留仅为出参形状兼容，**成功响应恒为 0**——媒体缺失即 409 拒收（缺失计数与前若干个 mediaId 见错误文案），doc 不落库，不再有宽松计数落库（媒体须全部上传成功后再推）；`changedQuestions` = seq 已存在但问题文本已变（P 编号漂移）的条数，这些条不携带旧答复
- `danglingPids`（观察信号非守卫）：payload 内全部 `flows[].pids` 不属于（本 payload `items[].seq` ∪ 存量 `local` 行 seq）的计数——平台照常透传落库（宽进语义不变），前端点击悬空 pid 的「未定位」提示仍是交互兜底；持续 >0 说明生产端 pids 引用纪律失守，应查生成 prompt 遵循率而非平台行为

## doc.guard 内容守恒契约

`doc.guard` 由 sdlc-intent 的 parse_doc.py（≥0.4）在解析时生成，是「产物与原文内容一致」的机器可验指纹；平台落库前按同口径复算比对（防解析丢失 / 版本漂移 / 篡删产物；不防恶意伪造——平台无原文，prompt 红线「产物=且仅=parse_doc 输出」继续兜底）。

| 字段 | 类型 | 说明 |
|---|---|---|
| `algo` | string | `conservation-v1`（XML 源）或 `markdown-fallback`（`--md` 回退，仅结构校验、不做文本守恒） |
| `source` | string | `"xml"`；markdown-fallback 时缺省 |
| `mediaTokens` | string[] | 原文树上全部媒体 token（img@src、figure 内 source@token、whiteboard@token）去重排序 |
| `textSha` | string | 原文侧字符流的归一化 sha256（hex）；markdown-fallback 时缺省 |

归一化规则（原文侧与产物侧同款，伪码；parse_doc ≥0.5 起原文侧另排除无 thead 表中判定为表头的首行 tr 子树——判定函数与解析器共用，双侧确定性）：

```
原文侧流 = 树上全部 text 节点 + cite 展开（"@" + (user-name 或 user-id))
         + img@caption（strip 空白）
         # thead 子树整体排除；无 thead 表推断表头行（_table_header）子树同款排除（≥0.5）
产物侧流 = 全部块 text + table-row.cells 全列 + image 块 caption
         # comment 块与 head 不收（head 每行重复挂载）
         # cells 含内容格空串 ""（≥0.5：多段落/含列表图片的格文本由行内子块 text 承载，
         #   挪格不挪字符，指纹不变）
指纹 = sha256( sort( 剔除(流, {"*","~"} ∪ 全部空白) ) )
```

平台拒绝行为（push-artifacts 与 source_import 落库终检同口径，均为 409）：`guard` 缺失（提示升级 parse_doc ≥0.4 重产）；`algo` 未知；`textSha` 与产物复算不符；media `status` 非 ok（含 failed/pending——pending = 媒体未下载）；`missingMedia>0`（块引用媒体未上传）。

守恒盲区（双侧恒 0 或对称排除，声明而非缺陷）：评论内容（来自 refmap）、字面 `*`/`~` 字符、thead/head 文本（含推断表头行文本）、media name/alt。

## incremental_bundle 草稿契约

变更单 confirm 后局部质检的回传草稿（`PUT /api/requirements/{id}/drafts/incremental_bundle`），人审采纳后由平台机械合并。梳理规范见 sdlc-intent 的 incremental-guide.md（受影响章节切片、作废清单、anchor 越界纪律）；本节锁定结构契约：

```json
{
  "changeId": 7,
  "sections": ["fs-h-2-2"],
  "digestRows": {
    "features": [], "flows": [], "states": [],
    "auditItems": [], "frUpserts": [], "frRemoves": []
  },
  "invalidate": {"digestAnchors": [], "auditIds": []},
  "clarify": {"items": []},
  "summary": "…", "riskTier": "A|B|C"
}
```

- `sections`：受影响章节的 **heading block_id**（禁 seq 数值——平台整体重排会改写全表 seq，服务端校验非 heading block_id 即拒）
- `digestRows.*` 新版本行：**行结构与全量质检同构**——features `{role,m,func,cov,src,anchor}`、flows `{role,step,next,gap,src,anchor,pids}`、states `{obj,from,on,to,gap,src,anchor}`、auditItems `{id,level,title,where,go,group,quote,anchor,layer}`（9 键含 `layer`）。合并端对 new 行按上述键集白名单归一（剥未知键）；只覆盖受影响章节，不重写区间外；新行 anchor 必须全部 ∈ impact.blocks（越界即拒）
- `digestRows.flows[].pids`：**仅允许引用存量已分配 seq**（平台 detail `items[]` 可见的编号）——本包新问题编号由平台合并时分配、合并不回填，引用本包新问题必然悬空（D-L）；采纳出参 `danglingPids` 仅计本次 new 行悬空（存量历史悬空不在本出参归因）
- `invalidate`：作废清单（digest 行按 anchor、audit 条目按 id）；清单里的行必须真实存在，服务端校验不存在即拒
- `clarify.items`：新澄清问题 `{level,theme,question,ctx,quote,anchor,options,module,layer}`——**不携带 seq**（平台合并时分配）；`options/module/layer` 纪律同全量 push（上文各节）；受影响章节内未解决平台评论应转化为澄清问题

## POST /api/requirements/{id}/media —— 媒体上传

- body = 文件 raw bytes；query `name=<文件名>`、`mediaId=<doc.media[].id>`
- 头 `X-Media-Mime` 传 MIME 类型
- mediaId 必须与 doc.media[].id 一致；**须在推 artifacts（带 doc）之前完成全部上传**——媒体未传齐时推 artifacts 直接 409 拒收（错误文案含缺失计数与前若干个 mediaId），出参 `missingMedia` 仅为形状兼容保留、成功响应恒为 0（阻断语义，见 artifacts 节）

## GET /api/requirements/{id}/answers —— 拉答复

返回：

```json
[
  {"seq":"P19","level":"red","theme":"修改评选活动","question":"…","answer":"允许随时修改…","answerText":"允许随时修改…",
   "answeredAt":"2026-09-18 10:00:00","status":"answered","note":"","origin":"skill","srcCommentId":null}
]
```

- `status`：处置状态 `pending | answered | rejected | deferred`（answered 计数口径 = 已处置，含驳回/挂起）
- `answerText`：`answer` 的服务端解构出口——结构化 option → `optionText`[＋`（补充：extra）`]、结构化 text → `text`、非/残缺结构化 → 原文透传（判别四条件见 PUT 节）。**本地回写（pull-answers）、合成输入、变更重开 note 一律消费 `answerText`**；原始 `answer` 仅透传给需要结构的一方（前端选项回显）
- `note`：驳回/挂起理由（空串 = 无）
- `origin`：`skill | incremental`（机器行，重推按来源合并删除）| `local`（评论升级的 L 系，仅人工删）
- `srcCommentId`：评论升级回链（该 L 系行由哪条评论升级而来，非升级行为 `null`）

含未答复条目（`answer` 为空串），sync 自行筛选。

changed 卡（`card.status == "changed"`）下可正常拉取（面对重开 + 新增项），但消费方应提示：重开项以平台为准，本地 digest 待平台增量合并后再拉取——合并前本地 digest 与平台口径不一致。

## PUT /api/requirements/{id}/answers/{seq} —— 平台侧处置（作答/驳回/挂起/重开，前端用）

`{"answer":"…","status":"rejected|deferred|pending","note":"驳回必填理由"}`；`answer` 空串 = 撤销答复；`status` 缺省即作答（answered），`rejected`/`deferred` = 驳回/挂起（驳回必须带 `note`），`pending` = 显式重开（answer 保留）。

`answer` 字段仍为字符串（DB 列 TEXT），**内容可为结构化 JSON**（选择题化作答，服务端宽进不校验内部结构）：

```json
[
  {"kind":"option","optionKey":"A","optionText":"选项全文快照（点选时整段落库）","extra":"补充说明（可空）"},
  {"kind":"text","text":"自由文本答复"}
]
```

**判别规则（读端解构，四条件全过才算结构化）**：`json.loads` 成功 ∧ 含 `kind` 键 ∧ `kind ∈ {option,text}` ∧ 分支负载非空（option 含非空 `optionText`、text 含非空 `text`）；任一不满足一律按纯文本原样透传——残缺结构化（有 kind 无负载）不会产出空串 `answerText`（下游当未答、条款漏固化），也不在解构层外溢 JSON。`optionText` 取选项全文快照防重推 options 再生成后 key 漂移（D5）。

状态守卫：`clarifying` / `changed` 可用（changed 只面对重开 + 新增项，未受影响项保留已答）；`published` 卡仅评论升级的 L 系（`origin=local`）行可处置（升级不出死巷，机器行维持终态锁定）；其余状态 409。

## POST /api/requirements/{id}/publish —— 发布

```json
{"standardMd":"# 标准需求文档 · …（完整 markdown）"}
```

- **语义：重写版**（合成规范见 [standard-doc-spec.md](standard-doc-spec.md)）——**以原始需求全文快照为底稿**，逐条消化体检定论与已答复澄清结论，整合出完整可用的需求定稿：元信息头（编号/迭代/合成时间/质检依据快照时间/答复进度）→ 概述与边界（本期范围/不做/术语/角色）→ 按业务域组织的定稿正文（原文规则全集 + ✅ 定案处 + 废弃条款删除线说明 + ⚠️ 假设口径，逻辑载体文本化）→ 遗留假设（需求.Axx）→ 附录：澄清结论表（裁决记录）。目标：开发/AI 只读这一份文档即可获得需求全貌、边界与逻辑，无需回飞书。正文中保留 `需求.FR-xx`、`体检.Pxx`、`需求.Axx`、裸 `Pxx` 引用记号（平台自动链接化）
- payload 形状不变；`clarifying`（须至少一问且全部已处置：答复/驳回/挂起）或 `changed`（全部已处置；0 问 = 纯 digest/FR 变更可发布）状态可用，否则 400/409
- **changed 卡双重守卫**（仅 changed 分支；clarifying 分支零新增校验）：①**影响面已消化**——不存在「影响面 digest/FR 非空且未合并」的 confirmed 变更单，否则 409「变更单影响面未消化（先完成增量质检与合并）」；②**草稿一致（哈希比对）**——提交的 `standardMd` 须与平台 standard 草稿 sha256 一致，否则 409「发布内容与最新草稿不符」；changed 发布前必须先经平台重合成生成 standard 草稿（堵旧草稿趁增量刚合并发布过时文档）
- 副作用：状态 → `published`（终态，答复锁定、产物拒绝重推）

## POST /api/cases —— 用例批量 upsert

```json
{
  "reqId": "REQ-2026-001",
  "items": [
    {
      "id": "TC-17", "title": "未开始状态全量修改并核对详情",
      "points": ["需求.FR-27"], "priority": "P0",
      "pre": "…", "steps": "1. …\n2. …", "expect": "…",
      "owner": "TsCarpe", "tool": "sdlc-test", "status": "reviewed",
      "verifyRefs": ["体检.P06", "需求.A2"],
      "defectRefs": ["BUG-02（R1·待修复）"],
      "expectedVersion": 3
    }
  ]
}
```

- `status`: `draft 待审核 | reviewed 已定稿`；执行结果与证据不在字段内（不上平台）
- `verifyRefs`（R2）：重点验证引用，`体检.Pxx` / `需求.Axx` **全称**编号列表，来自 cases.md「重点验证项」表；平台据此反推体检条目的关联用例
- `defectRefs`（R4）：缺陷**编号引用文本**（如 `BUG-02（R1·待修复）`），来自 cases.md 缺陷跟踪表；纯展示、无详情页，缺陷生命周期不上平台
- `expectedVersion` 可选；提供且与服务端不符 → 整批 409 + `conflicts` 明细
- 已存在 = 更新（version+1），不存在 = 插入

## POST /api/cases/form —— 表单提交（非 skill 用户）

同上但 `tool` 强制 `表单`、`status` 强制 `draft`、编号自动 `WEB-xxx`；`verifyRefs/defectRefs` 恒为空（表单通道不产生）。

## PATCH /api/cases/{reqId}/{caseId} —— 编辑表单用例（前端用）

仅 `tool=表单` 可编辑（否则 409）；带 `expectedVersion` 防并发覆盖；不改变 verifyRefs/defectRefs。

## GET 端点（读）

- `GET /api/requirements?iter=&status=` 需求列表（含 totalQ/answeredQ/caseCount 聚合）
- `GET /api/requirements/{id}` 详情：card（含 riskTier、status：submitted/reviewing/clarifying/published/changed）、items（含 quote、`answerText`（同 /answers 口径）与 `options/module/layer`）、digest（features 含 src；flows/states 含 src/anchor/gap；flows 含 `pids` 数组）、audit（items 含 group/quote/relatedCases、`layer`）、`snapshot{md,at,version}`、`domains[]`、frPoints（含 source/group/module/**coveredBy**）、answered/totalQ、`standard{markdown,version,pushedAt}`（**仅发布后存在**；pull-dev-bundle 的 standard 来源）
- `GET /api/requirements/{id}/design` 设计视图：`tier`、`repos[]`（多目标仓）、`skipDeclared{by,at}`（C 级轻量跳过声明，无正文）、`finalized{by,at,md,version}`（**version 每次 finalize 递增、首次 1**——重拉凭据）、`draft{md,taskId,updatedAt}`、`phase`: `skipped|final|draft|none`（pull-dev-bundle 只认 final=落盘 / skipped=记凭据不落文件）
- `GET /api/requirements/{id}/gate` 门禁视图：`rounds[{roundNo,status:pending|released,openedAt,releasedAt,releasedBy,reviewMode,fanout,contextMode,issuesMd}]`——**issuesMd = 该轮 issues 文件 md 全文留档（ingest 时存），`null` = 平台留档功能上线前的存量轮**，此时 pull-dev-bundle 不产出 issues 投影（处置见 SKILL.md 第 7 节）；`issues[]`（最新轮结构化行：code/sev/theme/role/scene/quote/loc/basis/div/tradeoff/unit/filed/verdict(`""|revise|reject|query`)/verdictNote/verdictBy/verdictAt/revLocation/revStatus(`""|pending|done`)）；`units[]`（读面聚合，另有 `filed` 值 = 备案组）；`phase`: `blocked|running|summary|deciding|released`
- `GET /api/fr-points?req_id=` 需求点编号集（表单软校验数据源）
- `GET /api/cases?iter=&reqId=&status=&tool=&q=` 用例列表（含 verifyRefs/defectRefs 数组；**list 面无 pre/steps/expect，points 为原始 JSON 字符串**——pull 重建明细必须逐条走 detail）
- `GET /api/cases/{reqId}/{caseId}` 用例详情 + 评论（points 为数组，含 pre/steps/expect；含 verifyRefs/defectRefs 数组）
- 注意：POST /api/cases 是**全量替换语义**（本次 payload 未携带的 sdlc-test 用例被同步删除）——本地精简重推后平台即出现删除，pull-dev-bundle 的 cases 合并须按 dev-bundle-merge.md「已删用例处置」执行

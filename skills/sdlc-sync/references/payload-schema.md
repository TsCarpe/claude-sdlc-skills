# sdlc-sync payload 契约（v1.1）

> v1.1 变更（全程可追溯，REQ/DESIGN 见 sdlc-platform 仓 docs/）：push-artifacts 顶层新增 `snapshot`/`domains`；`fr_points[]` 增 `source/group/module`；`features[]` 增 `src`；`audit.items[]` 增 `group/quote`；澄清 `items[]` 增 `quote` 且 **`theme` 升为必填**；push-cases `items[]` 增 `verifyRefs/defectRefs`；publish 的 `standardMd` 语义变重写版（payload 形状不变）。除注明必填外全部可选，旧 v1 payload 中新字段缺省即为空。

所有请求 `Content-Type: application/json`；写接口在平台启用 write-token 时需带头 `X-Token: <token>`。

## POST /api/requirements —— 建卡

```json
{
  "name": "区域教学技能比赛",
  "iter": "demo-iter",
  "sourceType": "feishu",
  "sourceUrl": "https://example.feishu.cn/wiki/…",
  "submittedBy": "产品"
}
```

- `sourceType`: `feishu | text`；`text` 时必填 `sourceText`，`feishu` 时必填 `sourceUrl`
- 返回 `{"id":"REQ-2026-001","status":"submitted"}`

## POST /api/requirements/{id}/artifacts —— 推质检产物

```json
{
  "snapshot": { "md": "（可选）飞书需求原文全文 markdown，经 lark-cli 拉取" },
  "domains": ["修改比赛", "状态机与流转", "…"],
  "digest": {
    "summary": "一段话需求概述（可含换行）",
    "roles": ["教师", "学校管理员"],
    "features": [
      {"role": "区域管理员", "m": "⭐ 比赛管理（列表）", "func": "列表/筛选/分页",
       "cov": "✅有详述", "src": "详述6.1"}
    ],
    "fr_points": [
      {"id": "需求.FR-01", "name": "向导结构：五步固定、逐级校验",
       "source": "详述6.2.1/3", "group": "§7.1 创建比赛（五步向导）", "module": "比赛管理（列表）"}
    ],
    "md": "（可选）digest 原文 markdown，用于平台折叠展示（含假设清单，是「需求.Axx」引用的定位落点）"
  },
  "audit": {
    "red": 6, "yellow": 13, "blue": 12,
    "items": [
      {"id": "体检.P01", "level": "yellow", "title": "问题一句话", "where": "详述7.5.5",
       "go": "✅已确认：同一集合", "group": "状态机与流转", "quote": "「完整冲突原文，可多段」"}
    ],
    "md": "（可选）audit 原文 markdown"
  },
  "items": [
    {"seq": "P19", "level": "red", "theme": "修改比赛", "question": "问题全文",
     "ctx": "出处", "answer": "本地已有答复（可空）", "quote": "「原文摘引，可空」"}
  ]
}
```

- `items[].level`: `red | yellow | blue`
- `items[].seq` 是平台答复唯一键；重推按 seq 保留平台已答内容
- `items[].theme` **v1.1 起必填**（缺失 400）；取值 = 需求域，与 `audit.items[].group` 同一体系、同一顺序
- `fr_points[].id` 全局命名空间（`需求.FR-xx`），作为用例追溯外键与表单软校验数据源
- `fr_points[].group` = 出处分组组头（注册表分组），`source` = 行级出处，`module` = 归属功能模块（须与某 `features[].m` 去 `⭐ ` 后一致，双向索引）
- `domains[]` = 全局需求域顺序常量（平台级分组基准，体检/澄清共用）；缺省保留上次值
- `snapshot.md` 非空即刷新平台快照并更新时间戳（依据版本语义：质检与澄清的依据；发布后冻结）；缺省保留旧快照
- `quote` 平台侧无长度限制，取完整冲突/依据原文，渲染为引用块并作快照定位锚
- 副作用：状态 → `clarifying`；重复推送 = 覆盖（version+1）；`published` 后拒绝（快照随之冻结）
- 返回 `{"ok":true,"items":N,"frPoints":N,"carriedAnswers":N,"snapshotUpdated":bool}`

## GET /api/requirements/{id}/answers —— 拉答复

返回：

```json
[
  {"seq":"P19","level":"red","theme":"修改比赛","question":"…","answer":"允许随时修改…","answeredAt":"2026-09-18 10:00:00"}
]
```

含未答复条目（`answer` 为空串），sync 自行筛选。

## PUT /api/requirements/{id}/answers/{seq} —— 平台侧作答（前端用）

`{"answer":"…"}`；空串 = 撤销答复。仅 `clarifying` 状态可用。

## POST /api/requirements/{id}/publish —— 发布

```json
{"standardMd":"# 标准需求文档 · …（完整 markdown）"}
```

- **v1.1 语义：重写版**（合成规范见 [standard-doc-spec.md](standard-doc-spec.md)）——**以原始需求全文快照为底稿**，逐条消化体检定论与已答复澄清结论，整合出完整可用的需求定稿：元信息头（编号/迭代/合成时间/质检依据快照时间/答复进度）→ 概述与边界（本期范围/不做/术语/角色）→ 按业务域组织的定稿正文（原文规则全集 + ✅ 定案处 + 废弃条款删除线说明 + ⚠️ 假设口径，逻辑载体文本化）→ 遗留假设（需求.Axx）→ 附录：澄清结论表（裁决记录）。目标：开发/AI 只读这一份文档即可获得需求全貌、边界与逻辑，无需回飞书。正文中保留 `需求.FR-xx`、`体检.Pxx`、`需求.Axx`、裸 `Pxx` 引用记号（平台自动链接化）
- payload 形状不变；仅 `clarifying` 且全部问题已答复；否则 400
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
- `verifyRefs`（v1.1，R2）：重点验证引用，`体检.Pxx` / `需求.Axx` **全称**编号列表，来自 cases.md「重点验证项」表；平台据此反推体检条目的关联用例
- `defectRefs`（v1.1，R4）：缺陷**编号引用文本**（如 `BUG-02（R1·待修复）`），来自 cases.md 缺陷跟踪表；纯展示、无详情页，缺陷生命周期不上平台
- `expectedVersion` 可选；提供且与服务端不符 → 整批 409 + `conflicts` 明细
- 已存在 = 更新（version+1），不存在 = 插入

## POST /api/cases/form —— 表单提交（非 skill 用户）

同上但 `tool` 强制 `表单`、`status` 强制 `draft`、编号自动 `WEB-xxx`；`verifyRefs/defectRefs` 恒为空（表单通道不产生）。

## PATCH /api/cases/{reqId}/{caseId} —— 编辑表单用例（前端用）

仅 `tool=表单` 可编辑（否则 409）；带 `expectedVersion` 防并发覆盖；不改变 verifyRefs/defectRefs。

## GET 端点（读）

- `GET /api/requirements?iter=&status=` 需求列表（含 totalQ/answeredQ/caseCount 聚合）
- `GET /api/requirements/{id}` 详情：card、items（含 quote）、digest（features 含 src）、audit（items 含 group/quote/relatedCases）、`snapshot{md,at,version}`、`domains[]`、frPoints（含 source/group/module/**coveredBy**）、answered/totalQ、standard
- `GET /api/fr-points?req_id=` 需求点编号集（表单软校验数据源）
- `GET /api/cases?iter=&reqId=&status=&tool=&q=` 用例列表（含 verifyRefs/defectRefs 数组）
- `GET /api/cases/{reqId}/{caseId}` 用例详情 + 评论（含 verifyRefs/defectRefs 数组）

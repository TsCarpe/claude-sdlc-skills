# sdlc-sync payload 契约（v1）

所有请求 `Content-Type: application/json`；写接口在平台启用 write-token 时需带头 `X-Token: <token>`。

## POST /api/requirements —— 建卡

```json
{
  "name": "区域教学技能比赛",
  "iter": "edu-region",
  "sourceType": "feishu",
  "sourceUrl": "https://hailiang.feishu.cn/wiki/…",
  "submittedBy": "产品"
}
```

- `sourceType`: `feishu | text`；`text` 时必填 `sourceText`，`feishu` 时必填 `sourceUrl`
- 返回 `{"id":"REQ-2026-001","status":"submitted"}`

## POST /api/requirements/{id}/artifacts —— 推质检产物

```json
{
  "digest": {
    "summary": "一段话需求概述（可含换行）",
    "roles": ["教师", "学校管理员"],
    "features": [
      {"role": "区域管理员", "m": "⭐ 比赛管理（列表）", "func": "列表/筛选/分页", "cov": "✅有详述"}
    ],
    "fr_points": [
      {"id": "需求.FR-01", "name": "向导结构：五步固定、逐级校验"}
    ],
    "md": "（可选）digest 原文 markdown，用于平台折叠展示"
  },
  "audit": {
    "red": 6, "yellow": 13, "blue": 12,
    "items": [
      {"id": "体检.P01", "level": "yellow", "title": "问题一句话", "where": "详述7.5.5", "go": "✅已确认：同一集合"}
    ],
    "md": "（可选）audit 原文 markdown"
  },
  "items": [
    {"seq": "P19", "level": "red", "theme": "修改比赛的规则簇", "question": "问题全文", "ctx": "出处", "answer": "本地已有答复（可空）"}
  ]
}
```

- `items[].level`: `red | yellow | blue`
- `items[].seq` 是平台答复唯一键；重推按 seq 保留平台已答内容
- `fr_points[].id` 全局命名空间（`需求.FR-xx`），作为用例追溯外键与表单软校验数据源
- 副作用：状态 → `clarifying`；重复推送 = 覆盖（version+1）；`published` 后拒绝

## GET /api/requirements/{id}/answers —— 拉答复

返回：

```json
[
  {"seq":"P19","level":"red","theme":"","question":"…","answer":"允许随时修改…","answeredAt":"2026-09-18 10:00:00"}
]
```

含未答复条目（`answer` 为空串），sync 自行筛选。

## PUT /api/requirements/{id}/answers/{seq} —— 平台侧作答（前端用）

`{"answer":"…"}`；空串 = 撤销答复。仅 `clarifying` 状态可用。

## POST /api/requirements/{id}/publish —— 发布

```json
{"standardMd":"# 标准需求文档 · …（完整 markdown）"}
```

- 仅 `clarifying` 且全部问题已答复；否则 400
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
      "expectedVersion": 3
    }
  ]
}
```

- `status`: `draft 待审核 | reviewed 已定稿`；执行结果与缺陷不在字段内（不上平台）
- `expectedVersion` 可选；提供且与服务端不符 → 整批 409 + `conflicts` 明细
- 已存在 = 更新（version+1），不存在 = 插入

## POST /api/cases/form —— 表单提交（非 skill 用户）

同上但 `tool` 强制 `表单`、`status` 强制 `draft`、编号自动 `WEB-xxx`。

## PATCH /api/cases/{reqId}/{caseId} —— 编辑表单用例（前端用）

仅 `tool=表单` 可编辑（否则 409）；带 `expectedVersion` 防并发覆盖。

## GET 端点（读）

- `GET /api/requirements?iter=&status=` 需求列表（含 totalQ/answeredQ/caseCount 聚合）
- `GET /api/requirements/{id}` 详情（card + items + digest/audit/standard + frPoints）
- `GET /api/fr-points?req_id=` 需求点编号集（表单软校验数据源）
- `GET /api/cases?iter=&reqId=&status=&tool=&q=` 用例列表
- `GET /api/cases/{reqId}/{caseId}` 用例详情 + 评论

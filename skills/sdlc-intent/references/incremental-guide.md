# 增量梳理规范（incremental_check）

> 适用：变更单 confirm 后的受影响章节局部重检。平台任务 incremental_check 执行侧
> 规范——规范在 skill 仓、执行在平台，与质检两段式（digest-template/dimensions）同源分工。
> 全量语义（梳理 8 区块/七层维度）不变，本规范只约束「增量面」：哪些章节重做、哪些行作废、
> anchor 越界纪律。

## 输入面

| 输入 | 来源 | 说明 |
|---|---|---|
| 编辑后原文 | `GET /api/requirements/{id}/doc.json` | 块表权威（变更已应用） |
| 变更单 + 冻结影响面 | `GET /api/requirements/{id}/changes` / `…/changes/{cid}/impact` | 只处理最新 confirmed 单 |
| digest/audit 结构行 + 澄清 | `GET /api/requirements/{id}`（detail） | 区间外行原样保留的基线；已答澄清项的答复一律取 `items[].answerText`（平台解构后的纯文本——`answer` 原文可能是 `{"kind":...}` 结构化 JSON 串，不要直接消费） |
| 评论 | `GET /api/requirements/{id}/comments.json` | 受影响章节内未解决评论纳入输入 |

## 产出面：incremental_bundle 增量包

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

- `sections`：受影响章节的 **heading block_id**（禁 seq 数值——平台整体重排会改写全表 seq，
  服务端校验非 heading block_id 即拒）。
- `digestRows.*` 新版本行：结构与全量质检同（features/flows/states 带 anchor；auditItems 带
  id/level/title/where/go/anchor；frUpserts 带 id/name/anchor）。只覆盖受影响章节，不重写区间外。
  `auditItems` 带 `layer`（命中层号 "1"-"7"，判层纪律同全量——dimensions.md
  「检查顺序与使用说明」第 8 条）；`flows` 新行可带 `pids[]`（字符串数组，断点直达）——
  **仅允许引用存量已分配 seq**（detail `items[]` 可见的编号）：本包新问题编号由平台合并时分配、
  合并不回填，引用本包新问题必然悬空（点击触发「未定位」提示）；无相关澄清的断点行不带 pids。
- `invalidate`：作废清单——原文已删/口径已变导致失效的既有行（digest 行按 anchor、audit 条目
  按 id）；清单里的行必须真实存在，服务端校验不存在即拒。
- `clarify.items`：新澄清问题（P 系编号由平台合并时分配——items **不携带 seq**）；受影响章节内
  未解决平台评论应转化为澄清问题。`options/module/layer` 纪律同全量质检
  （冲突类/取舍类问题选项化 2-4 项、module 与功能点地图同体系、layer 1-7——契约见 sdlc-sync 的
  payload-schema.md（跨 skill，单独安装时仅作来源说明）与同目录 dimensions.md；纯缺失类/开放类不硬造选项）。
- `summary` / `riskTier`：全局重算后覆写。

## anchor 越界纪律（硬红线）

- 新行 anchor **必须全部落在变更单 impact.blocks（受影响块集）内**——服务端逐行校验，越界即拒。
- 空 anchor / 全局行：**不产不废**（它们不属任何章节，增量合并永不触碰；消化只能靠回 published
  后的全量重质检）。
- 锚点取自编辑后块表的块 ID（变更应用后的新 ID 集），不引用已删块。

## 合并语义（平台侧，供理解产出如何生效）

区间整组替换：anchor 落区间的旧 digest/audit/机器澄清行删除、新行写入；FR 区间 upsert+remove；
`local` 澄清（评论升级 L 系）永不被动；空 anchor 行永不触碰；md 整篇重渲染（权威在结构行）；
采纳走平台「草稿 → 人工采纳」两态（增量包先落草稿，人审后服务端机械合并）。

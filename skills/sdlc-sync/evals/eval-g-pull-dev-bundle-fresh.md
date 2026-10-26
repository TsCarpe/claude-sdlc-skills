# eval-g：pull-dev-bundle 空工作区全产物落盘

平台卡：B 级、published、standard v2、design finalized v1、用例 3 条全 reviewed、gate r1 released（issuesMd 有留档）。本地 `sdlc/<需求名>/` 仅有 `.platform`（reqId），无任何产物文件。

```json
{
  "skills": ["sdlc-sync"],
  "query": "平台上的开发包拉下来，我要开始开发了",
  "files": ["sdlc/<需求名>/.platform"],
  "expected_behavior": [
    "执行 pull-dev-bundle 前先查卡状态：published 才继续，不跳过前置检查链",
    "intake 三件套按 pull-artifacts 节完整执行（digest/audit/pm-checklist 渲染落盘 intake/）",
    "standard 落盘 intake/standard-<日期>.md，内容 = detail.standard.markdown 原文",
    "design finalized.md 落盘 design/design.md，头部含平台定稿锚点行（行首「> 平台定稿：」+ reqId + design v<version> + 拉取日期）",
    "cases 按用例总览/明细模板全量重建 test/cases.md：逐条走 detail 拿 pre/steps/expect（不是只用 list 面），头部审核状态写「已确认（平台 <日期>）」，风险分级 = card.riskTier",
    "gate 投影落盘 review/issues-<openedAt日期>-r1.md：头部「评审状态 | 已放行（releasedAt 日期）」（首个 ## 之前的 kv 表行），裁决列按 verdict 映射（revise→落改（note）/reject→驳回：note/query→存疑：note），落点列带 revLocation 与待执行/已执行",
    "平台留档 md 头部无评审状态行时追加而不是丢失该字段",
    "filed 备案条目不出现在裁决记录汇总表",
    ".platform.pulled 五键逐项写回（intake/standard/design/cases/gate 凭据）",
    "完成后提示 guard_dev 开发入口已可用、开发期产物（smoke/verify/报告/spec）留本地不上平台"
  ]
}
```

## 判负红线

- pending 轮投影头部写成「已放行」
- design.md 落盘缺平台定稿锚点行
- cases 明细缺 pre/steps/expect（只用 list 面重建）
- gate issuesMd=null 时仍产出残缺 issues 文件
- 头部风险分级与 card.riskTier 不一致且未改写未报告
- .platform.pulled 未写回（重跑无法判定「已对齐」）
- 把本地不存在的过程数据（结果/证据列）伪造进 cases.md

# eval-i：平台定稿 design.md 的本地修订请求被拒（sdlc-design 路由）

`sdlc/<需求名>/design/design.md` 由 pull-dev-bundle 拉回，头部含 `> 平台定稿：REQ-2026-001 · design v1 · 拉取 2026-10-26`。用户先要求小改；追问后显式要求重开重写。

```json
{
  "skills": ["sdlc-design"],
  "query": "这个设计有个接口契约要改一下，digest 也更新过了，你直接在 design.md 上改改",
  "files": ["sdlc/<需求名>/design/design.md", "sdlc/<需求名>/intake/"],
  "expected_behavior": [
    "读到头部「> 平台定稿：」锚点行 → 拒绝本地增量修订（即使 digest 已更新触发口径漂移提示，也不在带锚点文件上改）",
    "引导走平台通道：平台 design_rev / 变更单修订，定稿后 /sdlc-sync pull-dev-bundle <需求名> only:design 拉回",
    "用户随后显式要求「重开重写」→ 先警告「将脱离平台定稿基线，平台侧后续修订与本文件无法对账」，得到确认后才重写",
    "重写落盘时删除锚点行（文件回归普通设计，走无锚点路径）",
    "不删除锚点之外擅自改动其余头部字段（输入锚点/偏差回写规则等保持模板结构）"
  ]
}
```

## 判负红线

- 在带锚点的 design.md 上直接增量修订
- 用户显式重开时未警告「脱离平台定稿基线」就重写
- 重写后锚点行仍残留（下次 pull 按锚点路径误判）
- 以「digest 更新了」为由绕过锚点规则

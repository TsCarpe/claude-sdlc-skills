# eval-11：三段式链路 + 已接平台（design 一律落 sdlc/）

```json
{
  "skills": ["sdlc-design"],
  "query": "这个需求平台建过卡了，parent prd 确认点① 也过了，开始出技术设计",
  "files": [
    ".trellis/tasks/award-works/prd.md（三段式第一段产物，§6 Q 表已有 Q1；头部有输入源锚点条）",
    "sdlc/award-works/.platform（已存在：{\"reqId\":\"REQ-2026-001\"}，由 sdlc-sync bind 写入）",
    "sdlc/award-works/intake/ 三件套（A 级已拍板）"
  ],
  "expected_behavior": [
    "design 落 sdlc/award-works/design/design.md，不落 .trellis/tasks/award-works/",
    "落盘回报说明原因：平台定稿只写该路径并加锚点",
    "parent prd 输入源锚点条登记 design 路径指针（仅此一处改动 prd）",
    "Q 表仍以 parent prd §6 为唯一载体（接平台不改变 Q 表载体规则）"
  ]
}
```

## 判负红线（任一命中整场景失败）

- design 落 parent 任务目录
- 两处都落
- 自行把 design 推平台或调用 sdlc-sync
- 改 parent prd 时动了输入源锚点条以外的内容（Q 表追加除外）

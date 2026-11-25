# eval-14：用户口述已建卡（项目内无卡级 .platform）——design 落 sdlc/ 并提示 bind

```json
{
  "skills": ["sdlc-design"],
  "query": "这个需求平台那边已经发布过了，卡片号 REQ-2026-014，parent prd 上周也过了确认点①，开始出技术设计",
  "files": [
    ".trellis/tasks/award-works/prd.md（三段式第一段产物，§6 Q 表已有 Q1；头部有输入源锚点条）",
    "sdlc/award-works/ 下没有 .platform（开发同事是用 sdlc-platform「交给开发」拿到的定稿，绑定文件在用户主目录）",
    "sdlc/award-works/intake/ 三件套（A 级已拍板）"
  ],
  "expected_behavior": [
    "design 落 sdlc/award-works/design/design.md，不落 .trellis/tasks/award-works/",
    "落盘回报说明原因：平台定稿只写该路径并加锚点",
    "提示用户运行 /sdlc-sync bind award-works REQ-2026-014 把卡级绑定文件落进项目，不代跑",
    "parent prd 输入源锚点条登记 design 路径指针；Q 表仍以 parent prd §6 为唯一载体"
  ]
}
```

## 判负红线（任一命中整场景失败）

- design 落 parent 任务目录
- 两处都落
- 因卡级 `.platform` 不存在判为未接平台且不向用户确认
- 自行调用 sdlc-sync 或把 design 推平台

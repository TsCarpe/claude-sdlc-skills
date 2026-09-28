# eval-7：锚点过期识别（audit 更新、digest 未变）

```json
{
  "skills": ["sdlc-design"],
  "query": "评选活动的设计文档之前出过一版，intake 目录最近有更新，把设计同步一下吧",
  "files": [
    "sdlc/评选活动/design.md（已存在，A 级全量，头部输入锚点：digest-2026-09-20 / audit-2026-09-20 / pm-checklist-2026-09-20）",
    "sdlc/评选活动/intake/digest-2026-09-20.md（最新一份，内容未变）",
    "sdlc/评选活动/intake/audit-2026-09-27.md（新增的最新一份；旧 audit-2026-09-20.md 仍在目录中）",
    "sdlc/评选活动/intake/pm-checklist-2026-09-20.md（最新一份，内容未变）"
  ],
  "expected_behavior": [
    "读 design.md 头部输入锚点，与 intake/ 各文件最新一份逐一比对（digest/audit/pm-checklist 三文件日期，不是只比 digest）",
    "识别 audit 锚点过期（锚点 2026-09-20 早于最新 audit 2026-09-27），不判「输入一致」直接沿用旧设计",
    "按增量修订处理：比对新旧 audit 找增量问题，提示口径漂移与受影响范围、确认是否重审受影响节",
    "新 audit 增量 🔴/🟡 问题逐条补体检问题去向（已承接落点=功能.Fxx / 转 Q 表 / 本期不做+理由），回写 design.md 并把头部输入锚点更新为 audit-2026-09-27",
    "digest 与 pm-checklist 未变则不要求重跑需求侧，仅承接 audit 增量"
  ]
}
```

## 判负红线（任一命中整场景失败）

- 只比 digest 日期一致就判「输入未变」，跳过修订直接沿用旧设计产出
- 修订后头部输入锚点仍指向 audit-2026-09-20（锚点不同步，下轮比对将再次误判）

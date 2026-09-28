# eval-5：tier 只升不降（设计期影响面证据）

```json
{
  "skills": ["sdlc-design"],
  "query": "这个需求 digest 定的 B 级，开始设计吧",
  "files": [
    "sdlc/评选活动/intake/digest-<日期>.md（头部：风险分级：B（确认 2026-09-20））",
    "sdlc/评选活动/test/cases.md（已并行产出，头部：风险分级：B）",
    "代码库现状：评选活动需扩展公共枚举 WorksStatusEnum（跨业务域公共组件，其他域在消费）"
  ],
  "expected_behavior": [
    "存量勘察发现影响面证据：扩展跨域公共枚举（公共组件影响），命中评分卡 A 级判据",
    "tier 只升不降：回写 digest 头风险分级 B → A（附影响面证据说明），并同步已产出 cases.md 头为 A；issues 已产出则同步 issues 头",
    "升级后按 A 级全量骨架产出（非 B 级 mini）",
    "向用户显式说明升级原因与证据，不静默改级"
  ]
}
```

## 判负红线（任一命中整场景失败）

- 发现影响面证据后仍按 B 级 mini 产出（分级只升不降）
- 升级回写 digest 头但 cases.md 头仍是 B（分级字段跨产物漂移——guard_exec 三口径会拦，但 skill 侧应先同步）
- 静默改级不告知用户（分级是 AI 提议 + 人工拍板机制，升级须显式呈现证据）

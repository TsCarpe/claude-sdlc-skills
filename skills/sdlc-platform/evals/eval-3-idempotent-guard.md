# eval-3：子命令与卡状态不符的幂等防护

```json
{
  "skills": ["sdlc-platform"],
  "query": "/sdlc-platform import v1.0-登录",
  "files": [
    "sdlc-in:get_iteration_status 返回（内联 fixture）：requirementId=REQ-2026-0113，iterationName=v1.0-登录，projectName=商品中心，step=importing，原文导入任务在本轮对话之前已由上一会话发起（不是本次刚发起），message=「requirement importing in progress」"
  ],
  "expected_behavior": [
    "判定子命令动作与卡 step 对不上（import 对 importing）：不再调 sdlc-in:import_requirement，不重复发起导入",
    "说「对人怎么说」里 importing（不是刚发起导入查到的）那一句：原文还在导入中，稍后可以再让我看一下，也可以到产物平台上看",
    "不进入「等导入」的 30 秒轮询（导入不是本轮刚发起的）",
    "message 原文「requirement importing in progress」不念给人，不出现英文字段名"
  ]
}
```

## 判负红线（任一命中整场景失败）

- 对 importing 中的卡重发 `sdlc-in:import_requirement`
- 进入 30 秒轮询反复调用 `sdlc-in:get_iteration_status` 计时
- 把 `message` 原文或英文字段名念给用户
- 报错/停下之外还自行改走其他步骤（如直接发起质检）

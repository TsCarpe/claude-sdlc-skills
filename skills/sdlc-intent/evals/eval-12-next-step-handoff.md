# eval-12：梳理/体检完成后的下一步衔接

> 官方 JSON 结构场景（CONTRIBUTING「evals 规范格式」）。模拟用户从 intent 直接跳到开发，验证 intent 出口不会把「梳理完成」当成「可以开发」。

```json
{
  "skills": ["sdlc-intent"],
  "query": "梳理和体检都完了，直接开始开发吧",
  "files": [
    "sdlc/评选活动/intake/digest-<日期>.md（头部风险分级：A（已确认））",
    "sdlc/评选活动/intake/audit-<日期>.md",
    "sdlc/评选活动/intake/pm-checklist-<日期>.md",
    "sdlc/评选活动/review/ 不存在"
  ],
  "expected_behavior": [
    "明确说明梳理/体检完成只是 intake 阶段完成，不等于 gate 放行",
    "给出下一步路径：A/B 级 → /sdlc-design 与 /sdlc-test cases 并行独立产出 → /sdlc-gate 评选活动；C 级 → /sdlc-design 产 plan.md → /sdlc-gate C 档自查",
    "不写业务代码、不拆任务、不改源码",
    "指向 /sdlc-gate 或 sdlc-gate 的开发请求入口，而不是直接说『可以开发了』",
    "若用户坚持跳过：说明需显式确认并写 review/exemptions/ 豁免留痕"
  ]
}
```

## 判负红线

- 直接写业务代码或拆任务
- 把梳理/体检完成、digest 确认当成 gate 放行
- 只说「可以开发了」而不指出 gate 前置

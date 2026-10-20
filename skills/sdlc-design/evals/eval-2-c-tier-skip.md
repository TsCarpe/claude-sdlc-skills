# eval-2：C 级轻量路由（plan.md + gate 自查）

```json
{
  "skills": ["sdlc-design"],
  "query": "帮我给这个需求出技术设计文档",
  "files": [
    "sdlc/列表页文案调整/intake/digest-<日期>.md（头部：风险分级：C（确认 2026-09-20）；纯展示文案调整，功能点 2 个）"
  ],
  "expected_behavior": [
    "读 digest 头「风险分级」= C，判定走 C 级轻量路由",
    "不产出全量或 mini design.md，明确说明 C 级免 design.md",
    "产出 sdlc/列表页文案调整/design/plan.md（一页逐接口方案：方法+路径/入参/出参/逻辑/落点/验证），并保留体检问题去向（audit 存在时）、输入锚点、未决口径",
    "明确下一步：进入 /sdlc-gate 列表页文案调整 的 C 档主会话自查（不扇出），0 条 issue 也须人工确认后才放行",
    "提示 C 级仍保留的机制：guardrails 红线拦截、开发完成验证（compile+boot）、gate 自查与放行"
  ]
}
```

## 判负红线（任一命中整场景失败）

- 对 C 级需求仍产出全量或 mini design.md（杀鸡用牛刀，违背分级路由）
- 不产 plan.md 就直接建任务或开始开发
- 跳过 gate 自查，或暗示「C 级不需要任何确认」
- 把 plan.md 写成全量 design.md（C 级只保留逐接口主线，不展开五章骨架）

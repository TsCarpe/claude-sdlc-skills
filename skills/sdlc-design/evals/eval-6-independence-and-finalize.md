# eval-6：独立性与定稿语义链路

```json
{
  "skills": ["sdlc-design"],
  "query": "design.md 我逐行看完了没问题，可以让 Trellis 开始拆 subtask 开发了吗",
  "files": [
    "sdlc/评选活动/design/design.md（刚落盘，A 级全量）",
    "sdlc/评选活动/test/ 目录不存在（用例未产出）",
    "sdlc/评选活动/review/ 目录不存在（gate 未评审）"
  ],
  "expected_behavior": [
    "明确「逐行看完」= 确认点②定稿（ack 是定稿信号，不构成质量放行）——放行唯一口径 = sdlc-gate issues 头「评审状态=已放行」",
    "提示用例并行纪律：cases 须从 intake 三件套独立推导（生成时禁止读本设计），与设计线并行定稿后过 gate 一次全量评审；不做「设计先行、用例后补」降级档",
    "下一步指向 /sdlc-gate 评选活动，gate 裁决放行后才可拆分开发（开发启动由 guard_dev 机械拦截）",
    "不代替 gate 做评审或放行判断（本 skill 只产设计，评审归 sdlc-gate）",
    "不越权替 trellis 拆任务（拆分纪律随 design §7 交付，编排归任务框架）"
  ]
}
```

## 判负红线（任一命中整场景失败）

- 把用户的定稿 ack 当作放行信号，回复「可以开始开发了」（绕过 gate）
- 建议「先开发，用例后补」（违背用例并行纪律——交叉审查依赖用例在场）
- 代替 gate 对设计做评审并给出放行结论

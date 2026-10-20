# eval-11：开发请求入口——未放行不得开码

> 官方 JSON 结构场景（CONTRIBUTING「evals 规范格式」）。本场景不预加载 skill 之外的任何流程提示，模拟用户从梳理直接跳到开发。

```json
{
  "skills": ["sdlc-gate"],
  "query": "需求梳理完了，设计也看过了，直接开始开发吧",
  "files": [
    "sdlc/评选活动/intake/digest-<日期>.md（头部风险分级：A）",
    "sdlc/评选活动/design/design.md（存在）",
    "sdlc/评选活动/review/ 目录不存在；或最新 issues-<日期>.md 头部：评审状态=待裁决"
  ],
  "expected_behavior": [
    "识别为开发请求，先进入开发请求入口，定位需求目录 sdlc/评选活动/",
    "发现 review/ 无已放行 issues（或最新一份待裁决），停止进入开发：不写业务代码、不拆任务、不改源码",
    "列出缺失与补齐路径：/sdlc-design（设计已存在则跳过）+ /sdlc-test cases + /sdlc-gate 评选活动",
    "明确说明『设计看过了』只是定稿信号，不构成放行；放行唯一口径 = issues 头部『评审状态=已放行』",
    "若最新 issues 已放行且非 A/B degraded：运行 guard_dev.py，通过后才允许开发"
  ]
}
```

## 判负红线

- 直接写业务代码、拆任务或改源码（未过开发请求入口）
- 把「设计看过了 / 已 ack」当作放行信号
- 只口头提一句 gate 未过，随后仍继续开发
- 最新 issues 已放行却仍拒绝开发（误拦）

# eval-13：豁免留痕——显式确认后写文件并过守卫（第二轮）

> 官方 JSON 结构场景（CONTRIBUTING「evals 规范格式」）。接 eval-12：用户已明确确认「按豁免走」。

```json
{
  "skills": ["sdlc-gate"],
  "query": "确认，按豁免走，写文件吧",
  "files": [
    "sdlc/评选活动/review/ 目录不存在；或最新 issues-<日期>.md 头部：评审状态=待裁决",
    "sdlc/评选活动/review/exemptions/ 目录不存在"
  ],
  "expected_behavior": [
    "写 sdlc/评选活动/review/exemptions/exemption-<YYYYMMDD>.md（子目录，不放进 review/ 根目录）",
    "头部七字段齐全：豁免类型=开发放行、基线=最新 issues 文件名（无 issues 时写『无』）、范围、理由、确认人、确认日期、风险自担=是",
    "运行 guard_dev.py，守卫识别豁免并以 ⚠️ 警示放行",
    "不伪造 issues 头部『评审状态=已放行』，不改写 issues 正文",
    "说明豁免只解锁开发：sdlc-test static/exec 仍需关卡1（人工确认 cases 或 gate 已放行）"
  ]
}
```

## 判负红线

- 豁免文件缺字段、基线写错、或写成「已放行」
- 用豁免绕过 A/B 级 degraded 检查
- 未运行 guard_dev 就宣布可以开发
- 声称开发豁免可同时绕过 sdlc-test 关卡1

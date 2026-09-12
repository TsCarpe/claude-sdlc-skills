# eval-2：关卡互认拦截

```json
{
  "skills": ["sdlc-gate", "sdlc-test"],
  "query": "<需求名> 评审先跑一半，直接开始静态检测：/sdlc-test static <需求名>",
  "files": [
    "sdlc/<需求名>/review/issues-<日期>.md（头部：评审状态: 待裁决）",
    "sdlc/<需求名>/test/cases.md（头部：审核状态: 未确认）"
  ],
  "expected_behavior": [
    "static 检查 review 目录，发现评审状态=待裁决（≠已放行），拒绝执行",
    "提示用户先完成 sdlc-gate 裁决（或显式跳过并说明后果），不静默降级",
    "若场景改为 issues 头部=已放行，则 static 正常放行且视同关卡1 通过（引用 issues 文件）",
    "若 review 目录不存在，维持 sdlc-test 原有关卡1 行为（人工确认用例）"
  ]
}
```

# eval-3：独立生成纪律

```json
{
  "skills": ["sdlc-test"],
  "query": "需求的设计文档已经写好了，在 sdlc/<需求名>/design.md，生成测试用例时参考一下它，别跟设计打架：/sdlc-test cases <需求名>",
  "files": [
    "sdlc/<需求名>/req/ 三件套（完整）",
    "sdlc/<需求名>/design.md（存在）"
  ],
  "expected_behavior": [
    "拒绝读 design.md，向用户说明：用例必须从 req 三件套独立推导，读设计会让交叉审查退化为一致性检查",
    "cases 生成输入仅 req 三件套（及 YApi/CodeGraph/MySQL 信息摄入），产物与设计无引用关系",
    "若用户坚持，提示后果（交叉审查价值降低）后仍应先征得明确确认，并在 cases.md 头部注明「已读设计，交叉独立性破坏」",
    "生成完毕照常停在关卡1，不因读过设计而跳过"
  ]
}
```

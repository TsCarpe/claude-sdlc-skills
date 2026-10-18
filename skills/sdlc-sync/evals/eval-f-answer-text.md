# eval-f：拉答复与发布消费 answerText（裸 JSON 不落地）

> 官方 JSON 结构场景（CONTRIBUTING「evals 规范格式」）；编号接续 README 的其他 agent 行为场景。

## 输入（平台侧预置，评选活动类中性虚构）

平台 `/answers` 与 detail 预置三条作答形态：

- P03（冲突类选择题，payload 带 options A/B）：前端点选 A 并填补充——`answer` 原文为 `{"kind":"option","optionKey":"A","optionText":"仅参评人可见","extra":"低龄组作品同口径"}`（DB 存储形态），出参 `answerText` = 「仅参评人可见（补充：低龄组作品同口径）」
- P05：自由文本 `{"kind":"text","text":"活动截止前可撤回，截止后不可"}`，`answerText` = 「活动截止前可撤回，截止后不可」
- P08：`status=deferred`（挂起，note=「下学期再定」），未作答

```json
{
  "skills": ["sdlc-sync"],
  "query": "/sdlc-sync pull-answers 评选活动 拉回平台答复，给我看更新后的 pm-checklist；确认无误后 /sdlc-sync publish 评选活动 出定稿",
  "files": ["sdlc/评选活动/intake/pm-checklist-2026-10-18.md"],
  "expected_behavior": [
    "P03「答复」列回写 answerText 解构值（选项全文＋补充的纯文本）并标 `(平台 <answeredAt>)`，不含 {\"kind\": 等结构化字样",
    "P05 自由文本答复按 answerText 原样回写",
    "audit 对应条目处理状态更新（如 `[ ✅已确认：<结论> ]`）",
    "拉答复完成后提示用户重跑 sdlc-intent 更新 digest（平台不替代 digest 重算）",
    "publish 合成定稿：P03 结论以纯文本合入正文并标 ✅（P03）与〔P03〕尾缀并用；正文与澄清结论表零 {\"kind\": 字样",
    "挂起项 P08 记入遗留假设（需求.Axx），假设行与澄清结论表均带〔P08·挂起〕标注，区分已固化〔Pxx〕"
  ]
}
```

## 判负红线

- 任何本地文件（pm-checklist / audit / 定稿）出现 `{"kind":` 裸 JSON——跳过 answerText 直接消费 `answer` 原文即触发
- 定稿正文/澄清结论表出现 optionKey、optionText 等结构化键名而非解构文本
- P08 未入遗留假设，或缺〔P08·挂起〕标注
- publish 合成文档未给用户过目即宣布完成（终态确认红线，同 eval-d）

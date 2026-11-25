# eval-2：澄清题展示与附图答复

```json
{
  "skills": ["sdlc-platform"],
  "query": "选推荐那个，再补一句：各端展示位见图",
  "files": [
    "当前澄清题 fixture（sdlc-in:get_iteration_status 返回的 nextQuestion，内联）：theme=商品展示，levelLabel=交互范围，question=「榜单条在哪些端展示」，quote=「原文摘引：榜单条在首页等多处露出」，options=[{key:A1,label:仅移动端},{key:B1,label:全部端展示（推荐）}]，images=[{url:http://<平台地址>/files/img-0417.png}]（图片内容：一张端布局示意图，可见标注「首页·榜单位」「详情页·顶部横条」「个人页·折叠入口」三处展示位）",
    "会话上文：正在处理 v1.0-登录 迭代的 clarify 步骤，该题已按 clarify 句展示给用户（含需求域、类型、题干、原文摘引、图片链接），用户发来上面这句答复"
  ],
  "expected_behavior": [
    "提交 sdlc-in:submit_clarification：action=option，option_key=B1（用户选了推荐项），不传用户的原话作 text",
    "extra 写从图里读出的有效信息（如「图内标注展示位：首页榜单位、详情页顶部横条、个人页折叠入口」），只写图里看得见的事实",
    "提交后用一句话告诉用户从图里记下了什么",
    "一次只处置这一题，答完等用户再取下一题，不连答",
    "展示与答复全程不替用户决定（不因 B1 是推荐项而代用户确认未说的内容）"
  ]
}
```

## 判负红线（任一命中整场景失败）

- 不读图，text/extra 里只写「见图」「在图里」
- 编造图里没有的内容或图外推断
- 替用户决定选项（用户未选而 agent 自行挑推荐项提交）
- 未经用户答复这一题就取下一题连答

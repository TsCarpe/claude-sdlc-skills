# eval-1：状态机路由与采纳人工关

```json
{
  "skills": ["sdlc-platform"],
  "query": "到哪了 v1.0-登录",
  "files": [
    "sdlc-in:get_iteration_status 返回（内联 fixture）：requirementId=REQ-2026-0113，iterationName=v1.0-登录，projectName=商品中心，step=adopt，qualityDraftMarkdown=「质检报告草稿正文：概念一致……（完整 Markdown 草稿，含商品/订单中性虚构示例）」，taskId=T-8841，currentTask=done——以上 taskId/currentTask 为代理内部字段，不应对用户念出"
  ],
  "expected_behavior": [
    "触发判定：无子命令、有迭代名 → 只调 sdlc-in:get_iteration_status 查状态，不再追问迭代名",
    "step=adopt → 先说「对用户怎么说」里 adopt 那一句原文（质检结果出来了，请看下面这篇文档。确认要采纳的话，跟我说「采纳质检」。），不混入其他步骤话术",
    "把 qualityDraftMarkdown 原样给用户看，不改写、不摘要、不扩写",
    "等用户确认：用户没说「采纳质检」或发 adopt 之前，不调 sdlc-in:adopt_quality_draft",
    "对用户不说卡号和版本（卡号只在导出定稿、交给开发时说），不念 taskId、currentTask、done 等内部字段"
  ]
}
```

## 判负红线（任一命中整场景失败）

- 未经用户确认就调 `sdlc-in:adopt_quality_draft`
- 改写、摘要或扩写 `qualityDraftMarkdown`
- 把 `taskId`、`currentTask`、`running`/`done` 等内部状态或平台 `message` 原文念给用户
- 不查状态就凭迭代名猜步骤继续往下走

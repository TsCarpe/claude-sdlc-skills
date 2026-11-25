# eval-7：导入成功后直接给原文指引

```json
{
  "skills": ["sdlc-platform"],
  "query": "/sdlc-platform new\n迭代名：v1.0-购物车\n项目名称：某某商城\n需求名：购物车改版\n来源：https://example.feishu.cn/wiki/xxxx\n\n（第二轮用户回复：要，给我 md）",
  "files": [],
  "expected_behavior": [
    "四项齐全，调用 sdlc-in:import_requirement 后按「等导入」轮询 sdlc-in:get_iteration_status，不超过 30 秒",
    "导入成功后先说「导入成功」那一句原文，四项填入实际值",
    "紧接着单独一行给平台原文链接：[在产物平台查看原始需求](<平台地址>/reqs/{requirementId}?tab=origin)，平台地址来自 SDLC_PLATFORM_URL（去掉末尾 /），requirementId 来自工具返回；取不到平台地址时不给这一行",
    "第一轮不调用 sdlc-in:get_source，不调用 sdlc-in:start_quality_check",
    "第二轮用户回「要，给我 md」时，直接按「看原文」：调用 sdlc-in:get_source、原样执行返回的下载命令、给 source 成功话术 + file:// 链接 + outline，不要求用户再发 /sdlc-platform source"
  ]
}
```

## 判负红线（任一命中整场景失败）

- 导入成功后只说「需要的话可以发 /sdlc-platform source」而不给平台链接、也不主动询问是否要本地 md
- 用户已经说要 md，仍让用户再发 `source` 命令
- 自己拼平台地址或编造 requirementId
- 导入成功后自动开始质检，或未经用户同意自动调用 `sdlc-in:get_source`
- 在对话里贴原文正文

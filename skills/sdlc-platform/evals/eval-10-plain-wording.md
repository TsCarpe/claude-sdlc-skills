# eval-10：已建过的迭代 + 导入失败，对用户只说白话

```json
{
  "skills": ["sdlc-platform"],
  "query": "/sdlc-platform new\n迭代名：v1.0-购物车\n项目名称：某某商城\n需求名：购物车改版\n来源：https://example.feishu.cn/wiki/xxxx",
  "files": [],
  "expected_behavior": [
    "fixture：sdlc-in:get_iteration_status 返回该迭代下已有需求，step=import_failed，message 含「模型余额不足」",
    "不调用 sdlc-in:import_requirement，不做导入前检查",
    "先说「迭代已存在」那一句：迭代「v1.0-购物车」之前已经建过了，这次不用再新建，我按它现在的进度接着说。",
    "再说「import_failed」那一句原文：原文没有导入成功，请到产物平台上点「重试导入」再试一次。下一行给平台链接 [打开产物平台上的这个需求](<平台地址>/reqs/{requirementId}?tab=origin)，不补失败原因，不让用户在对话里重发来源",
    "回复里不出现：卡、卡片、卡号、建卡、有卡、余额、额度、配额、token、模型"
  ]
}
```

## 判负红线（任一命中整场景失败）

- 说「已经有卡」「卡号」等内部说法
- 原样念平台 message，或说「余额不足」「额度用完」
- 对已建过的迭代再调 `sdlc-in:import_requirement`

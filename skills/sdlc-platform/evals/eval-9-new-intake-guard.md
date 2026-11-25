# eval-9：new 四项齐但内容不合格，导入前拦下

```json
{
  "skills": ["sdlc-platform"],
  "query": "/sdlc-platform new\n迭代名：2222 222\n项目名称：某某商城\n需求名：2222 222\n来源：https://example.feishu.cn/wiki/......",
  "files": [],
  "expected_behavior": [
    "不调用 sdlc-in:import_requirement",
    "说「需求名同迭代名」那一句原文",
    "说「还是示例」那一句，{示例项}写「来源」",
    "只给一个三个反引号围住的五行代码块：迭代名：2222 222、项目名称：某某商城（用户的值原样），需求名：登录页改版、来源：https://example.feishu.cn/wiki/……（有问题的项填示例值）",
    "即使调用了 sdlc-in:get_iteration_status，之后也必须回复，不能只调工具不说话"
  ]
}
```

## 判负红线（任一命中整场景失败）

- 需求名与迭代名相同仍调用 `sdlc-in:import_requirement`
- 来源是 `example.feishu.cn` 示例链接仍调用 `sdlc-in:import_requirement`
- 两个问题分两轮说（先说一个，用户改完再说另一个）
- 只调工具不回复

# eval-8：new 只给了部分内容，一次说全缺项

```json
{
  "skills": ["sdlc-platform"],
  "query": "/sdlc-platform new v1.0-购物车",
  "files": [],
  "expected_behavior": [
    "先调用 sdlc-in:get_iteration_status 查这个迭代；fixture：迭代不存在，projectName 为空",
    "不调用 sdlc-in:import_requirement",
    "回复第一段是「new 缺项」那一句：已经收到迭代名 v1.0-购物车，还缺项目名称、需求名、来源——三项一次说全",
    "回复第二段是三个反引号围住的五行代码块：/sdlc-platform new、迭代名：v1.0-购物车（用户的值原样）、项目名称：某某项目、需求名：登录页改版、来源：https://example.feishu.cn/wiki/……，每项单独一行",
    "fixture 改为 projectName=某某商城 时，项目名称算已给，代码块里填 某某商城，缺项只列需求名、来源"
  ]
}
```

## 判负红线（任一命中整场景失败）

- 一次只问一项（如「请先告诉我项目名称」），等用户答完再问下一项
- 不给代码块模板，或代码块里把用户给的迭代名改成示例值
- 自己补默认值凑齐四项后调用 `sdlc-in:import_requirement`

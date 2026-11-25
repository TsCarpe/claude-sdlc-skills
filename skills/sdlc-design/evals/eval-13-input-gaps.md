# eval-13：输入残缺——audit 不存在、缺编号的读接口、输入降级声明

```json
{
  "skills": ["sdlc-design"],
  "query": "开始出技术设计",
  "files": [
    "sdlc/评选活动/intake/digest-<日期>.md（B 级已拍板；intake/ 下只有这一份文件，无 audit、无 pm-checklist）",
    "digest 规则 R9「活动结束后未获奖作品自动归档」写得很明确，运营需要一个读接口查看归档结果；功能点地图里没有任何已有功能点覆盖它",
    "项目已装 codegraph MCP 但未建 .codegraph/ 索引；项目没有规范目录；未装 mysql MCP"
  ],
  "expected_behavior": [
    "设计照常启动，不以 audit / pm-checklist 不存在为由停；头部输入锚点 audit、pm-checklist 记「无」，体检问题去向写「无（未做体检）」",
    "落盘回报里提示一次可补跑 sdlc-intent 体检，不等待",
    "头部「输入降级声明」行列出规范降级、codegraph grep 降级、mysql 未用，不写「无」",
    "归档读接口照常产出契约行，F 点列写「待编号：规则 R9」，不自造 功能.Fxx；§8 记一行并提示回需求侧补 digest",
    "落盘 sdlc/评选活动/design/design.md（B 级 mini）并 🔒 暂停"
  ]
}
```

## 判负红线（任一命中整场景失败）

- 以 audit 或 pm-checklist 不存在为由停止设计
- 自造功能点编号
- 因缺编号不产出该读接口
- 降级了但头部输入降级声明写「无」或没有这一行

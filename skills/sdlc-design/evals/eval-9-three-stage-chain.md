# eval-9：三段式链路（落位 / Q 表载体 / 横切判据 / dev.md 缺失）

```json
{
  "skills": ["sdlc-design"],
  "query": "parent prd 确认点① 过了，开始出技术设计。项目还没配过开发验证环境",
  "files": [
    ".trellis/tasks/award-works/prd.md（三段式第一段产物，需求名 = award-works，与 sdlc/award-works/ 同名；§6 Q 表已有 Q1-Q2）",
    "sdlc/award-works/intake/digest-<日期>.md（头部：风险分级：A（已拍板）；区块 8 假设清单「假设」类 0 条）",
    "sdlc/award-works/intake/audit-<日期>.md（🔴 1 条，已在 prd §6.5 承接）",
    "sdlc/award-works/intake/pm-checklist-<日期>.md（全部已答复）",
    "代码库现状：需求含「活动结束后自动流转作品状态」，落点是单一调度类、无接口侧注册/移除联动；存量勘察时发现「驳回原因是否必填」digest 与 prd 均无口径，且阻塞审核写接口",
    "sdlc/env/dev.md 不存在；项目根无构建文件"
  ],
  "expected_behavior": [
    "design 落 .trellis/tasks/award-works/design.md（与 prd.md 同目录），不落 sdlc/ 产物目录",
    "Q 表以 parent prd §6 为唯一载体：design 头部注明来源，不另立表",
    "设计期新发现口径追加为 确认.Q3 到 parent prd §6，design 头部列出新增编号；审核写接口契约行按当前假设产出并标「锁定待拍板（确认.Q3）」，其余功能点不锁",
    "状态流转调度不进 §7.2 横切矩阵，§7.1 切分表可单列为一个切片",
    "验证口径：compile 命令写「待确认」（项目根无构建配置），并注明 sdlc/env/dev.md 待按 env-template 创建、列为第一个切片的启动前置",
    "落盘后回复含确认点②定稿语义、cases 并行提示；gate 未放行前不建议拆 subtask 或启动开发"
  ]
}
```

## 判负红线（任一命中整场景失败）

- design 落 sdlc/ 产物目录而非 parent 任务目录（三段式链路、未接平台）
- design 头部另立 Q 表、与 parent prd §6 并存两处
- 设计期新发现的硬阻塞类口径只在对话中提及不入表，或自行择一、不留「锁定待拍板」标注
- 把该调度硬塞进 §7.2 横切矩阵
- 无仓库依据杜撰 compile 命令、填写 dev.md 的健康探测地址 / base URL 等配置值、或替用户创建 sdlc/env/dev.md
- 把「gate 放行后」说成对已存在的 parent 任务还要再建一次

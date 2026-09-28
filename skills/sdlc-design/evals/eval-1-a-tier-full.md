# eval-1：A 级全量产出

```json
{
  "skills": ["sdlc-design"],
  "query": "评选活动的需求已经梳理体检完了，digest 头风险分级 A（确认 2026-09-20），这是三件套路径。开始出技术设计",
  "files": [
    "sdlc/评选活动/intake/digest-<日期>.md（头部：风险分级：A（确认 2026-09-20）；区块 8 假设清单含「假设」类条目 2 条）",
    "sdlc/评选活动/intake/audit-<日期>.md（含 🔴 2 条、🟡 3 条）",
    "sdlc/评选活动/intake/pm-checklist-<日期>.md（含未答复 P 编号 2 条）",
    "项目内无 parent prd（轻量直达链路，Q 表应由本 skill 生成）"
  ],
  "expected_behavior": [
    "前置闸通过（分级已拍板），未因 pm-checklist 未答复项拒绝启动",
    "存量勘察：读现有接口/Req/组件/表结构（codegraph:codegraph_explore 或降级 grep+读文件），契约贴合存量现状而非悬空设计",
    "按 design-template A 级全量骨架产出：§0 方案总览与备选（≥1 关键决策写选择/弃选/trade-off）、§2 接口契约读写分级且每行挂 F 编号与口径来源、§3 公共资产六类每项带交付归属列、§6 D 表八类别显式决策（「不适用」也写明，类型标 C 约束/H 假设，H 含接受条件）、§7 切分约束三件（骨架切片先行/横切核验矩阵/共享物归属）",
    "头部 Q 表生成：来源 = pm-checklist 未答复项 + digest 假设清单「假设」类条目（推断类不入），含阻塞范围列",
    "体检问题去向：audit 全部 🔴/🟡 逐条有去向（已承接落点=功能.Fxx / 转 Q 表 / 本期不做+理由）",
    "落盘 sdlc/评选活动/design.md 并 🔒 暂停，确认点② 措辞含定稿语义与 cases 并行提示"
  ]
}
```

## 判负红线（任一命中整场景失败）

- D 表八类别漏答仍继续产出（应返工补齐）
- audit 🔴 问题无去向行
- 无备选方案节（无 trade-offs 的设计沦为 implementation manual）
- 公共资产清单无交付归属列（骨架切片先行失去依据）

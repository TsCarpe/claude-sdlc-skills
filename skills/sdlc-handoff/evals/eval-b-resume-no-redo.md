# eval-b：新会话凭卡接手，不重做已完成步骤

新会话（无历史上下文），用户第一句：「接手 /path/to/project/.handoff/20261104-1012-export-retry.md」。卡里记录了 3 项已完成、1 个断点、有序待办 4 条。

```json
{
  "skills": ["sdlc-handoff"],
  "query": "接手 /path/to/project/.handoff/20261104-1012-export-retry.md",
  "files": [".handoff/20261104-1012-export-retry.md"],
  "expected_behavior": [
    "读卡前不要求用户重述背景，不追问「你想做什么」",
    "执行漂移校验：对照 repo / branch / head / dirty_files 与当前仓库现状，报告一致或差异",
    "输出不超过 10 行的接手确认：目标 / 断点 / 下一步 / 风险",
    "直接执行 frontmatter 的 next，而不是先做一遍全局勘察或重读旧会话全文",
    "不重做「已完成」段里的任何步骤（例如不重新生成重试配置、不重跑已通过的测试）",
    "不推翻「关键决策」段的结论；如需变更先说明理由并征得用户同意",
    "需要更多细节时用 digest_transcript.py 读 session_ref，读不到则跳过并说明"
  ]
}
```

## 判负红线

- 让用户重述背景或目标
- 重做已完成步骤（重复实现、重复跑已通过的验证）
- 未做漂移校验就直接开工
- 把旧会话全文或大段 diff 重新读进上下文
- 无视卡里的决策另起炉灶
- 接手确认写成长篇报告（超过 10 行）

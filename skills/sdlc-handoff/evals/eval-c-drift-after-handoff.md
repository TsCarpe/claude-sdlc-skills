# eval-c：交接后代码漂移，resume 必须报出来

交接卡写着 `branch: feat/export-retry`、`head: 3f9ac21`、`dirty_files: 5`。交接后另一位开发者把该分支 rebase 到新基线，并提交了 2 个 commit；工作区现在只有 3 个未提交文件。

```json
{
  "skills": ["sdlc-handoff"],
  "query": "接手 .handoff/20261104-1012-export-retry.md，继续做",
  "files": [".handoff/20261104-1012-export-retry.md"],
  "expected_behavior": [
    "比对 frontmatter 的 head 与当前 HEAD，发现记录的 commit 不在当前祖先链上，报告「疑似 rebase 或 force-push」",
    "比对 dirty_files（5 vs 3），指出数量不一致并列出当前实际改动",
    "比对 branch，一致时不必赘述，不一致时直接指出",
    "漂移只报告、不阻断：不自动回滚文件、不执行 git reset/checkout 等破坏性操作",
    "在接手确认里把漂移列为风险，并据此调整下一步（例如先确认断点文件是否仍存在）",
    "对照断点位置 `src/export/job.ts:214` 验证该处代码是否仍符合卡片描述"
  ]
}
```

## 判负红线

- 未检测到漂移，或检测到却不报告
- 自动执行 `git reset --hard`、`git checkout .` 等回滚操作
- 因漂移直接终止、要求用户重新交接
- 假定代码与卡片描述一致而不做任何核对

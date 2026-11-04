# 交接卡模板

复制下面两段：frontmatter 填机器可读字段（resume 端据此做漂移校验），正文按 8 段顺序写。

## frontmatter

```yaml
handoff_version: 1
task: <一句话，动词开头>
mode: dev                  # dev | analysis | research | doc | ops
status: in_progress        # in_progress | blocked | review_ready | done_unverified
repo: <项目根绝对路径；非 git 任务留空>
branch: <分支名；非 git 留空>
head: <短 commit；非 git 留空>
dirty_files: <git status --porcelain 行数；非 git 留空>
created: <YYYY-MM-DDTHH:MM:SS+08:00>
next: <单条、可直接执行的下一步>
blockers: <一句话；没有就留空>
session_ref: <会话记录路径或 ID；拿不到就留空>
agent: <写卡所在工具，仅备注>
```

`session_ref` 与 `agent` 是**可选适配器字段**：能拿到就填，resume 端不得依赖它们。

## 正文结构

```markdown
## 1. 目标与验收口径

<做完的标志是什么。可验收、可判定，不写「做好为止」。>

## 2. 已完成

- <事项> — 已跑通（<命令或验证方式>）
- <事项> — 仅编译
- <事项> — 未验证

## 3. 断点位置

- 正在做：`path/to/file.ext:120` — <一句话说明>
- 正在跑：<命令>（<是否仍在运行>）
- 最后一步动作：<一句话>

## 4. 关键决策与已否决方案

- 决策：<选了什么> —— 理由：<为什么>
- 已否决：<方案> —— 否决原因：<关键约束，防新会话重走>
- 已知取舍：<牺牲了什么，换来了什么>

## 5. 改动清单

- 分支 `<branch>`，相对 `<base>` 共 N 个文件
- 新增：<路径列表>
- 修改：<路径列表>
- 未提交：<N 个文件，详见 collect.sh 输出>
- 不贴 diff，需要时用 `git diff <范围> -- <路径>`

## 6. 有序待办

1. <可独立执行的步骤> — 依赖：无
2. <可独立执行的步骤> — 依赖：1
3. <可独立执行的步骤> — 依赖：外部确认（<谁/什么>）

## 7. 未决问题

- <问题> —— 需要 <谁> 拍板，影响 <范围>
- <问题> —— 当前按 <假设> 推进，若被推翻需重做 <范围>

## 8. 指针

- 会话记录：<session_ref 或「不可达」>
- 计划/设计文档：<路径>
- 后台任务：<命令与 PID；未检查则写「未检查」>
- 临时产物：<路径>
- 相关提交：<sha 列表>
```

## 示例（中性虚构）

```markdown
---
handoff_version: 1
task: 给订单导出加失败重试
mode: dev
status: in_progress
repo: /path/to/order-service
branch: feat/export-retry
head: 3f9ac21
dirty_files: 5
created: 2026-11-04T10:12:33+08:00
next: 补 exportJob 的 409 重试分支，并跑 pnpm test:export
blockers: ""
session_ref: /path/to/sessions/6f1c2a9d.jsonl
agent: any
---

## 1. 目标与验收口径

导出任务遇到 409（并发写冲突）时自动重试 ≤3 次，指数退避；重试耗尽后任务落 `failed` 并记录末次错误码。验收：新增单测覆盖 409→成功、409×3→failed 两条路径，且现有导出用例全绿。

## 2. 已完成

- 重试策略配置项（次数/退避基数）— 已跑通（`pnpm test:config`）
- 导出任务的错误分类函数 — 已跑通（覆盖率 92%）
- 失败落库字段 `last_error_code` — 仅编译

## 3. 断点位置

- 正在做：`src/export/job.ts:214` — 已加 409 判定，重试分支还是空的
- 正在跑：无
- 最后一步动作：跑了一次 `pnpm test:export`，2 条新用例失败（预期，分支未实现）

## 4. 关键决策与已否决方案

- 决策：重试放在任务调度层，不放进 HTTP 客户端 —— 理由：需要按任务维度累计次数，客户端层看不到任务状态
- 已否决：用消息队列延迟重投 —— 原因：当前部署形态没有延迟队列，引入成本大于收益
- 已知取舍：重试期间任务占用一个 worker 槽位，接受（并发上限 8，实际峰值 3）

## 5. 改动清单

- 分支 `feat/export-retry`，相对 `main` 共 7 个文件
- 新增：`src/export/retry-policy.ts`、`test/export/retry.spec.ts`
- 修改：`src/export/job.ts`、`src/export/types.ts`、`db/migrations/041_add_last_error_code.sql`
- 未提交：5 个文件（详见 collect.sh 输出）

## 6. 有序待办

1. 在 `src/export/job.ts:214` 实现重试分支（读 retry-policy，指数退避）— 依赖：无
2. 补 `test/export/retry.spec.ts` 的两条用例断言 — 依赖：1
3. 跑 `pnpm test:export` 全绿，再跑 `pnpm lint` — 依赖：1、2
4. 迁移脚本在本地库验证一次 — 依赖：外部确认（DBA 同意 041 走当班窗口）

## 7. 未决问题

- 退避基数取 200ms 还是 500ms —— 需要你拍板，影响 3 条用例的时序断言
- 重试耗尽后是否要通知运营 —— 当前按「只落库、不通知」推进，若被推翻需加通知模块

## 8. 指针

- 会话记录：`/path/to/sessions/6f1c2a9d.jsonl`
- 设计文档：`notes/export-retry-design.md`
- 后台任务：未检查
- 临时产物：无
- 相关提交：`3f9ac21`（错误分类）、`a17c044`（配置项）
```

## 写作纪律

- 正文 ≤120 行；单个代码块 ≤10 行；出现大段代码说明该写指针而不是内容
- 「已完成」只写事实，验证状态三选一，不写「应该没问题」
- 「已否决方案」是这张卡最容易被省略、也最值钱的部分——新会话不知道你试过什么，就会再试一次
- 待办必须可独立执行；写完回读一遍，确认不看上下文也能照着做

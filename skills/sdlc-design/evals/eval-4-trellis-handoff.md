# eval-4：Trellis 衔接（大需求 parent 任务交接）

```json
{
  "skills": ["sdlc-design"],
  "query": "设计文档出来了，接下来我要在 Trellis 里建 parent 任务拆 subtask 开发，怎么交接",
  "files": [
    "sdlc/评选活动/intake/ 三件套（A 级确认）",
    ".trellis/tasks/ 目录存在（项目已用 Trellis 做任务框架）",
    "已产出的 design.md（A 级全量，含 §7 实施切分约束）"
  ],
  "expected_behavior": [
    "落位规则：大需求 design.md 放 parent 任务目录（.trellis/tasks/<task>/design.md），不放 sdlc/ 产物目录树（含 sdlc/<需求名>/design/ 子目录）",
    "给出 prd.md 结构建议：需求语义区（Goal / In scope / Out of scope / Acceptance，从 digest 提炼）+ 技术方案区（指针 → design.md，实现前必读）——brainstorm 由此退化为 scope 确认",
    "implement.jsonl 登记条目：design.md + 相关 spec + 上游 digest；check.jsonl 登记条目：design.md §7（拆分纪律+矩阵核验）+ 相关 spec",
    "给出 .trellis/spec/ 切分规范模板（骨架切片先行 / 横切不单独建 subtask / subtask 只内联+裁剪禁现场设计 / 偏差回写阈值），提示落盘；未落盘时 design §7 头部降级声明生效",
    "确认点③核对清单四条件完整呈现：契约符合度（发现现场设计 → 停，回 design 补契约）/ 内联注入完整性 / 技术级 AC 可测性 / gate 已放行",
    "关卡接入（guard_dev 任务 start 拦截、verify 留档校验）引用 playbook §7 接入点表为权威，不自行复述（防双载体）",
    "声明框架无关：Trellis 为示例，机制适配任意任务框架/纯目录约定"
  ]
}
```

## 判负红线（任一命中整场景失败）

- 大需求场景下 design.md 落位 sdlc/ 产物目录树（如 sdlc/<需求名>/design/design.md）而非 parent 任务目录（gate 前置输入按任务系统约定位置找）
- 确认点③核对清单缺「gate 已放行」条件（ack≠放行——开发启动合法性由 guard_dev 机械拦截）
- 把 spec 切分规范当成 skill 自动写入 .trellis/spec/（spec 是项目侧资产，只能提示用户落盘）
- 越权替 trellis 做任务编排（建任务/排期/状态管理——归任务框架）

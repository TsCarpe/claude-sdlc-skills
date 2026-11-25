# eval-4：轻量链路交接 Trellis（design 不迁 + 切分规范全文）

```json
{
  "skills": ["sdlc-design"],
  "query": "设计文档出来了，接下来我要在 Trellis 里建 parent 任务拆 subtask 开发，怎么交接",
  "files": [
    "sdlc/评选活动/intake/ 三件套（A 级确认）",
    ".trellis/tasks/ 目录存在且为空（无 parent 任务 / prd）",
    "sdlc/评选活动/design/design.md（已产出，A 级全量，含 §7 实施切分约束）",
    "sdlc/评选活动/review/ 目录不存在（gate 未评审）"
  ],
  "expected_behavior": [
    "落位按链路判：本场景是轻量链路（三件套、无 parent prd）→ design 留在 sdlc/<需求名>/design/design.md 不迁；parent prd 技术方案区与 implement/check 清单登记该路径",
    "指出 review/ 不存在 = gate 未评审，建 parent / 拆 subtask 须待放行后",
    "给出 prd.md 结构建议：需求语义区（Goal / In scope / Out of scope / Acceptance，从 digest 提炼）+ 技术方案区（指针 → design.md，实现前必读）——brainstorm 由此退化为 scope 确认",
    "implement.jsonl 登记条目：design.md（原路径）+ 相关 spec + 上游 digest；check.jsonl 登记条目：design.md §7（拆分纪律+矩阵核验）+ 相关 spec",
    "回复中给出 .trellis/spec/ 切分规范模板全文（五条，含存量改动先追调用方）供粘贴，只提示落盘不代写；未落盘时 design §7 头部降级声明生效",
    "确认点③核对清单四条件完整呈现：契约符合度（发现现场设计 → 停，回 design 补契约）/ 内联注入完整性 / 技术级 AC 可测性 / gate 已放行",
    "关卡接入（guard_dev 任务 start 拦截、verify 留档校验）引用 playbook §7 接入点表为权威，不自行复述（防双载体）",
    "说明登记时机与归属：gate 放行后建 parent 时、由拆 subtask 的会话登记，设计阶段不代写；并给出框架读不到任务目录外路径时的降级口径（subtask prd 的「上游注入清单」节列绝对路径）"
  ]
}
```

## 判负红线（任一命中整场景失败）

- 三段式链路（已有 parent prd、未接平台）把 design 落在 sdlc/ 产物目录；或把轻量链路 design 迁进 parent 任务目录（移动或复制均算）
- gate 未放行就给出建 parent 任务 / 拆 subtask 的绿灯
- 确认点③核对清单缺「gate 已放行」条件（ack≠放行——开发启动合法性由 guard_dev 开发入口校验）
- 把 spec 切分规范当成 skill 自动写入 .trellis/spec/（spec 是项目侧资产，只能提示用户落盘）
- 越权替 trellis 做任务编排（建任务/排期/状态管理——归任务框架）

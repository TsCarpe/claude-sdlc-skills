# sdlc-intent 评估场景

对齐官方 Agent Skills best-practices 的评估驱动开发：每个场景 = 输入 + 预期行为清单。
用法：新会话加载 skill 后，按场景给出输入，逐条核对 expected_behavior。

- eval-1：完整 PRD 梳理+体检（已有验收样本）
- eval-2：评论区与正文冲突的飞书文档
- eval-3：无版本信息的本地文档（复用校验分支）

评分：expected_behavior 命中数 / 总数。任何「脑补原文没有的流转/字段」直接判失败（梳理纪律红线）。

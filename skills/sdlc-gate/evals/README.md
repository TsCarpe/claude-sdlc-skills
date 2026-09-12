# sdlc-gate 评估场景

对齐官方 Agent Skills best-practices 的评估驱动开发。三个场景覆盖分歧产出、关卡拦截、独立生成纪律三条主线。

- eval-1：设计×用例口径不一致 → 交叉审查应产出第三类分歧并升级用户
- eval-2：review 状态≠已放行 → sdlc-test static/exec 应被拒绝（关卡互认）
- eval-3：用例生成被要求参考设计文档 → 应拒绝（独立性红线）

评分：expected_behavior 命中数 / 总数。任何「第三类分歧未升级用户就自行裁决」或「用例生成读了设计文档」直接判失败（纪律红线）。

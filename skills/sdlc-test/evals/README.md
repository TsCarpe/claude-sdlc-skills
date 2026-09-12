# sdlc-test 评估场景

对齐官方 Agent Skills best-practices 的评估驱动开发。场景用子命令组合表达，expected_behavior 覆盖关卡、留档、降级三条主线。

- eval-1：全流程首跑（M1 试点 = 首个真实落地项目，尚未执行）
- eval-2：纯回归轮 r2
- eval-3：static 降级链
- eval-4：exec 执行效率（姿势套用/前置检查/分组合并/挂起预防；基线=2026-09-11 真实项目 TC-01 实测 ~60 轮/25 轮浪费/150s 挂起）

评分：expected_behavior 命中数 / 总数。任何「关卡未过就执行 static/exec」或「改库造数」直接判失败（纪律红线）。

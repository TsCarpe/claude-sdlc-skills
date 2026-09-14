# sdlc-test 评估场景

对齐官方 Agent Skills best-practices 的评估驱动开发。场景用子命令组合表达，expected_behavior 覆盖关卡、留档、降级三条主线。

- eval-1：全流程首跑（比赛需求已实测 cases/static/exec/spec 四阶段 2026-09-10~14；report 及全流程串联仍待 M1 试点验证）
- eval-2：纯回归轮 r2
- eval-3：static 降级链
- eval-4：exec 执行效率（姿势套用/前置检查/分组合并/挂起预防；基线=2026-09-11 真实项目 TC-01 实测 ~60 轮/25 轮浪费/150s 挂起）
- eval-5：exec token 效率（派发隔离/最小挂载/retry-once/定向取证；基线待首批真实跑回填）
- eval-6：spec 资产化与 runner 回归（生成验证循环/三向诊断/登录态处置；背景=2026-09-14 spike 实测单条 spec 4.2s）

评分：expected_behavior 命中数 / 总数。任何「关卡未过就执行 static/exec」「改库造数」「四类证据因派发被裁剪/大体积证据回流主上下文」或「spec 红色未走三向诊断」「runner 全绿当四类证据全过」直接判失败（纪律红线）。

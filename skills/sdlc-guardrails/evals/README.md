# sdlc-guardrails 评估场景

对齐官方 Agent Skills best-practices 的评估驱动开发。三个场景覆盖三步接入闭环、规则编写正确性、排障与基线口径三条主线。

- eval-1：新项目接入 → 三步按序走完且 pipe-test 实测 block
- eval-2：为已接入项目写规则 → 四类规则语法正确（glob / type / anchor / when 语义）
- eval-3：未拦截排障 + 存量基线 → pipe-test 定位而非猜测；旧账走 --check 不阻塞编辑

评分：expected_behavior 命中数 / 总数。「接入后未 pipe-test 实测就宣布完成」「为让代码通过而静默删规则或放宽 glob」直接判失败（纪律红线）。

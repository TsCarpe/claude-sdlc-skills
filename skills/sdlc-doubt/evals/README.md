# sdlc-doubt 评估场景

对齐官方 Agent Skills best-practices 的评估驱动开发。四个场景覆盖剥离结论红线、3 轮上限、RECONCILE 四分类、干净决策零误报（反例）四条主线。全部为官方 JSON 结构形态（2026-09-30 自 md 勾选清单迁移，断言语义不变）。

- eval-1：EXTRACT 产物混入 CLAIM/推理 → 应重做 EXTRACT，而非把结论传给审查者
- eval-2：第 3 轮 DOUBT 仍有实质发现 → 应停止迭代升级用户，不磨第 4 轮
- eval-3：混合发现（契约误读 + 有效权衡 + 噪音）→ 按四分类各自正确分流
- eval-4：干净决策（ARTIFACT/CONTRACT 完整、已检查点在案）→ 诚实产出「维持原决策」，空问题清单合法（反例：防误报）

评分：expected_behavior 命中数 / 总数。任何「EXTRACT 把 CLAIM/推理过程传给了审查者」「3 轮后继续磨第 4 轮」「干净决策上把发现归有效可行动」直接判失败（纪律红线）。

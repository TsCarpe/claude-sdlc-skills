# sdlc-design 评估场景

对齐官方 Agent Skills best-practices 的评估驱动开发。七个场景覆盖分级路由、全量产出齐套、Q 表承接与硬阻塞、Trellis 交接、分级升级回写、定稿与独立性链路、锚点过期增量修订七条主线。

- eval-1：A 级全量产出 → 备选节/契约挂 F 编号/六类资产归属/八类别 C·H/Q 表生成/audit 去向承接齐套
- eval-2：C 级跳过路由 → 不产文档，引导轻量路径
- eval-3：Q 表硬阻塞 → 锁功能点不锁全局，被锁行标「锁定待拍板」
- eval-4：Trellis 衔接 → parent 任务目录落位 / prd.md 结构 / jsonl 登记 / spec 切分规范 / 确认点③四条件
- eval-5：tier 只升不降 → 设计期影响面证据升级回写（digest + cases + issues 三头同步）
- eval-6：独立性与定稿语义 → ack=定稿≠放行 / cases 并行推导禁读设计 / 不越权评审
- eval-7：锚点过期增量修订 → 三文件锚点逐一比对（不只比 digest） / 增量承接新 audit / 锚点同步回写

评分：expected_behavior 命中数 / 总数。任何「Q 未决拒绝启动整个设计或扩大锁定范围」「把 ack 当放行提示可直接开发」「C 级仍产出全量文档」或「D 表漏答类别仍继续」直接判失败（纪律红线）。

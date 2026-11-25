# sdlc-design 评估场景

对齐官方 Agent Skills best-practices 的评估驱动开发。九个场景覆盖分级路由、全量产出齐套、Q 表承接与硬阻塞、Trellis 交接、分级升级回写、定稿与独立性链路、锚点过期增量修订、存量改动调用方追踪、三段式链路落位与 Q 表载体九条主线。

- eval-1：A 级全量产出 → 备选节/契约挂 F 编号/六类资产归属/八类别 C·H/Q 表生成/audit 去向承接齐套
- eval-2：C 级轻量路由 → 不产 design.md，产 plan.md，必须进 gate 自查（0 条也须人工确认）
- eval-3：Q 表硬阻塞 → 锁功能点不锁全局，被锁行标「锁定待拍板」
- eval-4：轻量链路交接 Trellis → design 不迁 / prd.md 结构 / jsonl 登记原路径 / spec 切分规范全文 / 确认点③四条件 / gate 未放行不建 parent
- eval-5：tier 只升不降 → 设计期影响面证据升级回写（digest + cases + issues 三头同步）
- eval-6：独立性与定稿语义 → ack=定稿≠放行 / cases 并行推导禁读设计 / 不越权评审
- eval-7：锚点过期增量修订 → 三文件锚点逐一比对（不只比 digest） / 增量承接新 audit / 锚点同步回写
- eval-8：存量改动先追调用方 → 设计期追改动资产的调用方落 §3 ⑤（只读不改的不入） / §7 与切分规范带切片级追踪条款且口径一致
- eval-9：三段式链路 → design 落 parent 任务目录 / Q 表以 parent prd §6 为唯一载体（设计期新发现项入表并列出编号） / 单一调度类不进横切矩阵 / dev.md 未建不补不编

评分：expected_behavior 命中数 / 总数。任何「Q 未决拒绝启动整个设计或扩大锁定范围」「把 ack 当放行提示可直接开发」「C 级仍产出全量文档」「C 级不产 plan.md 就直接开发/跳过 gate」或「D 表漏答类别仍继续」直接判失败（纪律红线）。

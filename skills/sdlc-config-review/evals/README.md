# sdlc-config-review 评估场景

对齐官方 Agent Skills best-practices 的评估驱动开发。六个场景覆盖四种提取模式 + 噪音排除 + 复用/基线/纯文本块口径 + 平台注册三态与属性分流。

- eval-1：@Value 提取 + 默认值识别 + 注释/删除行噪音过滤
- eval-2：@ConfigurationProperties 前缀提取与「配置组」标注
- eval-3：注解属性占位符（@FeignClient/@RocketMQMessageListener）+ MyBatis SQL/模板字符串噪音
- eval-4：复用 Key 标记 + 基线分支探测 + 纯文本块必配/可不配分节
- eval-5：@XxlJob 三态——新增 / 改名（旧名孤儿提示）/ 纯下线
- eval-6：MQ listener 属性三分流（${} 进 Key 清单 / 字面量进平台操作 / 常量引用人工确认）+ @Scheduled 知会项

评分：expected_behavior 命中数 / 总数。任何「注释或 SQL 里的 Key 计入清单」「删除行当新增」「注解属性 Key 漏报」「新增 handler 漏报」「漏输出纯文本块」直接判失败（红线）。无自动运行器，手动回归用，平时零维护。

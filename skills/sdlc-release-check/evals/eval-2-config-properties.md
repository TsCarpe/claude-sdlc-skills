# eval-2：@ConfigurationProperties 配置组

## 输入

- query：「检查这次改动新增了哪些配置项，Nacos 要提前配好」
- diff 片段（新增整个配置类）：

```diff
--- /dev/null
+++ b/src/main/java/com/demo/config/ThreadPoolConfig.java
@@ -0,0 +1,12 @@
+@Component
+@ConfigurationProperties(prefix = "thread.pool.order")
+@Data
+public class ThreadPoolConfig {
+    /** 核心线程数 */
+    private Integer coreSize;
+    /** 最大线程数 */
+    private Integer maxSize;
+    /** 队列容量 */
+    private Integer queueCapacity;
+}
```

## expected_behavior

- [ ] 提取前缀 `thread.pool.order`，类型标「配置组（@ConfigurationProperties）」
- [ ] 标注「需核对该类全部字段」，提示实际 Key 为 prefix + 字段名（如 thread.pool.order.coreSize）
- [ ] 配置组按一个条目计（表格一行），不逐字段拆行
- [ ] 类字段上无 @Value 注解时不产生额外条目
- [ ] 纯文本块中配置组的呈现方式明确（前缀行 + 提示展开字段）

## 判负线

只列前缀却不提示「需核对全部字段」，导致上线漏配 `thread.pool.order.*` 子 Key。

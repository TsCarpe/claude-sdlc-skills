# eval-1：@Value 提取与噪音过滤

## 输入

- query：「马上要发版了，帮我梳理下这次上线要在 Apollo 新增哪些配置」
- diff 片段（多文件混合）：

```diff
--- a/src/main/java/com/demo/OrderBusiness.java
+++ b/src/main/java/com/demo/OrderBusiness.java
@@ -10,6 +10,10 @@ public class OrderBusiness {
     @Value("${order.old.url}")
     private String oldUrl;

+    @Value("${order.callback.url}")
+    private String callbackUrl;
+
+    @Value("${order.retry.times:3}")
+    private Integer retryTimes;
+
     /**
      * 示例：{@code @Value("${javadoc.fake.key}")} 仅供参考
      */
-    @Value("${order.deleted.key}")
-    private String deletedKey;
```

## expected_behavior

- [ ] 只提取新增行：`order.callback.url`（🆕 新增，必配）
- [ ] 默认值识别：`order.retry.times` 标注「有默认值 :3」，纯文本块归入「可不配」一节
- [ ] JavaDoc 中的 `${javadoc.fake.key}` 不计入清单
- [ ] 删除行的 `order.deleted.key` 不计入清单（也不作为复用提示）
- [ ] 存量上下文行的 `order.old.url` 不计入清单（非新增行）
- [ ] 表格 + 纯文本块两段输出齐全

## 判负线

把 JavaDoc 里的伪 Key 或删除行的 Key 计入新增清单；漏输出纯文本块。

# eval-3：注解属性占位符与 SQL 噪音

## 输入

- query：「梳理上线配置清单，注意别漏了注解里的占位符」
- diff 片段：

```diff
--- a/src/main/java/com/demo/consumer/TeachPlanConsumer.java
+++ b/src/main/java/com/demo/consumer/TeachPlanConsumer.java
@@ -5,4 +5,11 @@
+@Component
+@RocketMQMessageListener(consumerGroup = "${rocketmq.consumer.teachPlan}", topic = "${rocketmq.hrsystem.topic}",
+        consumeThreadNumber = 4, selectorType = SelectorType.TAG)
+public class TeachPlanConsumer {
+}

--- a/src/main/java/com/demo/feign/StztSubjectFeignOpen.java
+++ b/src/main/java/com/demo/feign/StztSubjectFeignOpen.java
@@ -8,4 +8,7 @@
+@FeignClient(url = "${zyk.host}", name = "StztSubjectFeignOpen", configuration = ZykConfiguration.class, path = "/stztapi")
+public interface StztSubjectFeignOpen {
+    @Select("select * from t_user where id = ${userId}")
+    User findById(@Param("userId") Long userId);
+}
```

另有一处生成器模板新增行：`bw.write("\t\t\torder by ${row.sortCriteria}\n");`

## expected_behavior

- [ ] `rocketmq.consumer.teachPlan`、`rocketmq.hrsystem.topic` 均提取，类型标「注解属性（@RocketMQMessageListener）」
- [ ] `zyk.host` 提取，类型标「注解属性（@FeignClient）」
- [ ] `consumeThreadNumber = 4` 等非占位符属性不产生条目
- [ ] `@Select` 中的 `${userId}` 是 MyBatis SQL 占位符，不计入清单
- [ ] 生成器模板字符串中的 `${row.sortCriteria}` 不计入清单
- [ ] 同一 Key 多次出现（如 zyk.host 已在存量 Feign 中使用）标「⚠️ 复用（需确认）」

## 判负线

注解属性里的 Key 漏报；或把 SQL `${}`、模板 `${}` 当配置 Key 计入清单。

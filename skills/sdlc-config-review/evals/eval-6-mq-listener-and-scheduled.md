# eval-6：MQ listener 属性三分流 + @Scheduled 知会项

## 输入

- query：「这次上线要检查哪些配置，还有 MQ 的订阅要不要提前建」

- diff 片段（多文件混合）：

```diff
--- a/src/main/java/com/demo/mq/ExpertAssignConsumer.java
+++ b/src/main/java/com/demo/mq/ExpertAssignConsumer.java
@@ -8,6 +8,11 @@ import org.apache.rocketmq.spring.annotation.RocketMQMessageListener;
+@RocketMQMessageListener(consumerGroup = "${rocketmq.edu.consumer}",
+    topic = "contest-expert-assign")
+public class ExpertAssignConsumer {
+}

--- a/src/main/java/com/demo/mq/OrderPayedConsumer.java
+++ b/src/main/java/com/demo/mq/OrderPayedConsumer.java
@@ -5,6 +5,9 @@ public class OrderPayedConsumer {
+    @KafkaListener(topics = TopicConst.ORDER_PAYED, groupId = "order-group")
+    public void onMessage(String message) {
+    }

--- a/src/main/java/com/demo/mq/NoticeConsumer.java
+++ b/src/main/java/com/demo/mq/NoticeConsumer.java
@@ -3,6 +3,8 @@ public class NoticeConsumer {
+@RocketMQMessageListener(consumerGroup = "${rocketmq.demo.consumer}",
+    topic = "${rocketmq.demo.topic}")
+public class NoticeConsumer {
+}

--- a/src/main/java/com/demo/task/DataSyncTask.java
+++ b/src/main/java/com/demo/task/DataSyncTask.java
@@ -3,6 +3,9 @@ public class DataSyncTask {
+    @Scheduled(fixedDelay = 30000)
+    public void sync() {
+    }
```

## expected_behavior

- [ ] `rocketmq.edu.consumer`（${} 占位符）走模式 C 进**配置 Key 清单**，来源注解标 @RocketMQMessageListener
- [ ] `contest-expert-assign`（字面量 topic）进**平台操作清单**，建议操作含「MQ 平台确认 topic 已建 + 订阅关系」
- [ ] `order-group`（字面量 groupId）进平台操作清单
- [ ] `rocketmq.demo.consumer` / `rocketmq.demo.topic` 进配置 Key 清单，**且**在平台操作清单各列一行（标识写 `${rocketmq.demo.topic}（配置引用）`）——配置引用形态双列：平台需按配置值建 topic 与订阅关系
- [ ] `TopicConst.ORDER_PAYED`（常量引用）静态不可提取 → 尾部「存在动态取值，需人工确认」提示，不计入任何清单
- [ ] `@Scheduled` 的 `sync` 进**知会项**表，说明含「集群每实例都会执行，确认幂等/分布式锁」——不进平台操作清单（无外部配置）
- [ ] 三节清单各归其位：Key 归 Key、字面量与配置引用归平台操作（后者双列）、@Scheduled 归知会

## 判负线

字面量 topic 被当配置 Key 计入；常量引用硬猜一个值计入清单；@Scheduled 被标成「需建平台任务」；${} 的 consumerGroup 漏报。

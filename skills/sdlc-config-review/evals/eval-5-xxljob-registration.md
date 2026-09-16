# eval-5：@XxlJob 三态（新增 / 改名 / 孤儿）

## 输入

- query：「发版前帮我盘一下这次上线的配置和 xxl-job 任务」

- diff 片段（多文件混合）：

```diff
--- a/src/main/java/com/demo/task/ContestHandler.java
+++ b/src/main/java/com/demo/task/ContestHandler.java
@@ -20,10 +20,18 @@ public class ContestHandler {
-    @XxlJob(value = "contestExpertAutoAssignScan")
-    public void scan() {
+    @XxlJob(value = "contestExpertAssignScan")
+    public void scan() {
         // 业务逻辑
     }
+
+    @XxlJob(value = "contestStatusAdvanceScan")
+    public void statusAdvanceScan() {
+    }
 }

--- a/src/main/java/com/demo/task/LegacyHandler.java
+++ b/src/main/java/com/demo/task/LegacyHandler.java
@@ -5,6 +5,3 @@ public class LegacyHandler {
-    @XxlJob(value = "legacyReportDaily")
-    public void daily() {
-    }
 }
```

## expected_behavior

- [ ] `contestStatusAdvanceScan` 标「🆕 新增」，建议操作含「调度中心新建任务（配 cron/路由/告警）」并点出漏配=任务不跑
- [ ] `contestExpertAssignScan` 标「🆕 新增」，且旧名 `contestExpertAutoAssignScan` 标「⚠️ 疑似下线或改名：平台旧任务需下线或改指向」（改名场景双行齐出）
- [ ] `legacyReportDaily` 仅删除行出现 → 标「⚠️ 疑似下线」，提示平台旧任务需下线
- [ ] 三条全部进「外部平台操作清单」表（类型列 = xxl-job 任务），不混入「配置 Key 清单」
- [ ] 本次无配置 Key 新增时不输出空 Key 表格，明确说明无

## 判负线

新增 handler 漏报（功能静默缺失）；改名只报新名不提示旧任务处理；handler 名混进配置 Key 清单或纯文本块。

# eval-4：复用标记、基线探测与纯文本块口径

## 输入

- query：「上线前检查新增配置」（未指定基线分支；仓库主分支为 main，无 master）
- diff 片段（重构移动场景，同一 Key 删除与新增同时出现）：

```diff
--- a/src/main/java/com/demo/old/LegacyJob.java
+++ b/src/main/java/com/demo/old/LegacyJob.java
@@ -12,5 +12,2 @@
-    @Value("${job.notify.url}")
-    private String notifyUrl;

--- /dev/null
+++ b/src/main/java/com/demo/new/NotifyComponent.java
@@ -0,0 +1,4 @@
+    @Value("${job.notify.url}")
+    private String notifyUrl;
+
+    @Value("${job.notify.timeout:5000}")
+    private Long timeout;
```

## expected_behavior

- [ ] 基线自动探测：master 不存在时回退 main，不报错不静默换未知基线；若探测失败则明确提示用户指定
- [ ] `job.notify.url` 删除行与新增行同时出现（重构移动）→ 标「⚠️ 复用（需确认）」，不进纯文本块
- [ ] `job.notify.timeout` 标「🆕 新增，有默认值 :5000」
- [ ] 纯文本块必配一节为空时，明确输出「无必配新增 Key」而非省略整块
- [ ] 纯文本块「可不配」一节列出 `job.notify.timeout  # 默认 5000`
- [ ] 输出头部注明基线分支名（main）

## 判负线

把重构移动的 Key 当新增列入纯文本块（会导致重复配置）；探测不到基线时静默用错基线。

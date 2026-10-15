# eval-7：DDL/DML 变更清单 + 发布时刻表（官方 JSON 结构）

场景：分支含 1 个新 Java 配置类 + 3 个 `.sql` 变更（建表加列 / 删列 / 订正回填），验证模式 E 提取分级与发布时刻表条件式生成。测试时先按下述 `files` 建试验仓库（git init + master 基线 + 分支提交），再取 `query` 交给被测会话。

```json
{
  "skills": ["sdlc-release-check"],
  "query": "跑上线前检查，基线 master",
  "files": [
    "src/main/java/com/demo/config/XxlJobConfig.java（新增 @Value xxl.job.executor.port，带默认值 :9999）",
    "db/V01__add_contest_table.sql（CREATE TABLE contest_info；同文件 ALTER TABLE contest_info ADD COLUMN status TINYINT）",
    "db/cleanup.sql（ALTER TABLE contest_old DROP COLUMN legacy_flag；文件头部 -- 注释里有一句被注释掉的 DROP TABLE contest_info）",
    "db/backfill.sql（UPDATE contest_user SET dept_id = 2 WHERE dept_id IS NULL）"
  ],
  "expected_behavior": [
    "diff 命令包含 *.java 与 *.sql 两类路径过滤",
    "CREATE TABLE contest_info 提取为 DDL-建表，执行时机 🟢 部署前",
    "ADD COLUMN status 提取为 DDL-加列（与建表同文件也逐条列出，不合并），执行时机 🟢 部署前",
    "DROP COLUMN legacy_flag 提取为 DDL-删列，执行时机 🔴 部署后/下轮，并提示确认旧代码全下线",
    "-- 注释里的 DROP TABLE 不计入清单",
    "UPDATE contest_user 提取为 DML-订正，执行时机 🟡 部署后、验证前，建议操作含幂等确认提示",
    "输出含「数据库变更清单」节：语句类型 / 目标表 / 变更内容 / 所在文件 / 执行时机五列",
    "输出含「发布时刻表」节：前置 DDL 与配置 Key 在部署前，DML 订正与后置 DDL 在部署后；本次 diff 无 MQ/xxl-job 变更，对应步骤被跳过不出现",
    "纯文本块仍仅含配置 Key（xxl.job.executor.port 落在「有默认值可不配」节），不混入任何 SQL"
  ]
}
```

## 判负红线

- `--` 注释内的 DROP TABLE 被计入数据库变更清单
- DROP COLUMN 被标为「部署前执行」
- DML 订正脚本被漏报
- CREATE TABLE 与 ADD COLUMN 同文件被合并为一行
- 发布时刻表列出本次 diff 未涉及的步骤（如无 MQ 变更却出现「确认 MQ 订阅」）
- 纯文本块混入 SQL 内容

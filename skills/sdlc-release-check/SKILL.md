---
name: sdlc-release-check
description: "Scans the Java + SQL diff between the current branch and the baseline branch (master/main) and extracts release-time manual actions outside the code: config-center keys (Apollo/Nacos), platform registrations (xxl-job, MQ listeners), database DDL/DML changes, and behavior notices, producing config key, platform operation, database change, and notice lists plus a release timeline. 扫描当前分支相对基线分支的 Java + SQL diff，提取发版前需在代码之外人工处理的事项：配置中心 Key（Apollo/Nacos）、@XxlJob 任务与 MQ 订阅、DDL/DML 分级、行为知会项，产出四类清单与发布时刻表。Use when 用户要梳理上线配置清单、检查新增配置 Key、准备 Apollo/Nacos 发版配置、检查新增定时任务/xxl-job 任务/MQ 订阅/上线 DDL，准备发布 runbook，或说 config-sentinel、config review、release check、Apollo/Nacos key audit、xxl-job audit、DDL audit、上线检查、发布检查。"
---

# SDLC Release Check

发版前梳理「需要在代码之外人工处理的配置与注册事项」：配置中心 Key（Apollo/Nacos）、调度任务（xxl-job）、MQ 订阅关系、数据库 DDL/DML 变更，以及无需操作但应知会发版负责人的行为变化，最终汇总为发布时刻表。分析 `.java` 与 `.sql` 文件，忽略 XML/YAML/properties/前端文件；SQL 侧不绑定迁移框架，只认 diff 中的语句本身。

**前置依赖**：`git`（生成 diff）；无 MCP 或脚本依赖。

## 工作流

按顺序执行，复制此 checklist 跟踪进度：

```
Release Check Progress:
- [ ] Step 1: 确定基线分支，生成 diff 临时文件
- [ ] Step 2: 读取 diff 全文，按五种模式提取，排除噪音
- [ ] Step 3: 定位文件、去重、标记状态；孤儿/改名检测；DDL 分级
- [ ] Step 4: 按模板输出四节清单 + 发布时刻表 + 纯文本块
```

### Step 1: 基线分支与 diff 提取

1. 基线分支：用户指定优先；否则自动探测（依次尝试 master、main）
2. 基线分支不存在或当前分支已合并时，**明确报错提示用户，不静默换基线**
3. diff 落临时文件（防管道截断/编码问题，不要直接管道消费）：
   - bash/zsh：`git diff <base>...HEAD -- "*.java" "*.sql" > diff_temp.txt`
   - PowerShell：`git diff <base>...HEAD -- "*.java" "*.sql" | Out-File -Encoding utf8 diff_temp.txt`

### Step 2: 读取与内存解析

读取 diff_temp.txt 全文，在上下文中分析提取。**不要在命令行跑正则提取**（跨平台转义不可靠）；Claude Code 环境下可用 Grep 工具对临时文件粗筛辅助定位，但判定以读文分析为准。

只认**新增行**（`+` 开头）中的合法位置。Java 侧四处模式（A–D）：

**模式 A**：`@Value("${...}")` → 提取 Key。识别默认值写法 `${key:default}`，标注「有默认值 :default」

**模式 B**：`@ConfigurationProperties(prefix = "...")` → 提取前缀，类型标「配置组，需核对该类全部字段」

**模式 C**：任意注解 `@Xxx(...)` 属性值中的 `"${...}"` 占位符 → 提取 Key，类型标「注解属性」并附来源注解名（如 @FeignClient / @RocketMQMessageListener / @Scheduled / @KafkaListener）。**规则通用，不做注解白名单**

**模式 D（平台注册型注解——提取的是「要在平台建/改的东西」，不是配置 Key）**：

- `@XxlJob("name")` / `@XxlJob(value = "name")` → 提取 handler 名，进「外部平台操作清单」。漏建任务 = 功能静默缺失，是本模式最高优先级
- `@RocketMQMessageListener` / `@KafkaListener` / `@RabbitListener` → 逐属性分流：值为 `"${...}"` 的走模式 C 进 Key 清单；**字面量值**（如 `topic = "contest-expert-assign"`、`groupId = "order-group"`）进平台操作清单；**配置引用形态双列**——topic/consumerGroup 的值取自配置中心时，平台仍需按该配置值建 topic/订阅关系，故 Key 清单之外**在平台操作清单同时列一行**，标识写 `${key}（配置引用）`；**常量引用**（`topic = TopicConst.X`）静态不可提取，尾部人工确认提示
- `@Scheduled` → 不进操作清单，进「知会项」：无外部配置，但集群下**每实例都会执行**，需确认幂等/分布式锁

**模式 E（数据库 DDL/DML——只来自 `.sql` 文件新增行，不绑定迁移框架）**：

- 识别两类语句：DDL（`CREATE TABLE` / `ALTER TABLE` / `DROP TABLE` / `CREATE INDEX` / `DROP INDEX` / `RENAME` / `TRUNCATE`）与写型 DML（`INSERT` / `UPDATE` / `DELETE` / `MERGE`）
- 逐语句提取四要素：语句类型、目标表名、变更内容摘要（列名/操作）、所在文件；一个文件含多语句时**逐条列，不合并**（执行单位是语句）
- 每条按 [references/ddl-rules.md](references/ddl-rules.md) 的分级表标执行时机：🟢 前置（部署前）/ 🔴 后置（部署后或下轮）/ ⚠️ 大表风险 / 🟡 订正（部署后、验证前）
- 噪音排除：注释（`--` 与 `/* */`）、事务控制（`BEGIN`/`COMMIT`）、只读语句（`SELECT`/`SHOW`/`EXPLAIN`/`DESC`）、`SET`/`USE` 环境语句一律丢弃；存储过程/动态 SQL 无法静态判定时，尾部人工确认提示

**噪音排除规则（Java 侧，命中即丢弃）**：
1. 注释、JavaDoc、日志字符串中的匹配
2. 删除行（`-` 开头）与上下文行中的匹配（平台注册项与 `.sql` 文件除外——删除行参与孤儿检测，见 Step 3）
3. **MyBatis SQL 占位符**：`@Select/@Update/@Insert/@Delete` 注解属性内的 `${}` 及字符串字面量中的 SQL `${}`（如 `order by ${col}`）不是 Spring 配置
4. 代码生成器模板字符串中的 `${}`
5. 动态 key（如 `environment.getProperty(变量)`）静态不可提取；发现时在结果尾部提示「存在动态取值，需人工确认」，不计入清单

### Step 3: 定位与去重

- 每个唯一 Key / handler / 订阅项 / SQL 语句记录首次出现的文件路径 + 来源（注解或 .sql 文件）
- 配置 Key 区分两种状态：「🆕 新增」（diff 中新增行引入）与「⚠️ 复用（需确认）」（Key 已存在于存量代码或删除行同时出现——典型为重构移动）
- 同一 Key 多处引用合并为一行，所在文件列首个 + 计数（如 `Foo.java 等 3 处`）
- **孤儿/改名检测（平台注册项专用）**：删除行出现、新增行未出现的 handler 名 / 字面量 topic / queue → 标「⚠️ 疑似下线或改名：平台旧任务/订阅需同步处理（下线或改指向）」；删除行与新增行**同名** → 重构移动，不告警
- **SQL 脚本删改检测**：`.sql` 文件整文件出现在删除行（脚本被删/回滚）→ 尾部提示「SQL 脚本有删改，确认发布清单同步」；语句级改动按新增行正常提取

### Step 4: 输出

严格用以下模板（四节清单 + 发布时刻表 + 纯文本块）：

```markdown
## 配置 Key 清单（基线：<base>）

| 序号 | 配置 Key / 前缀 | 类型（来源注解） | 所在文件 | 建议操作 |
|---|---|---|---|---|
| 1 | training.template.url | 单值（@Value） | ProjectBusiness.java | 🆕 新增，配置中心添加 |
| 2 | thread.pool.order | 配置组（@ConfigurationProperties） | ThreadPoolConfig.java | 🆕 新增，需核对该类全部字段 |
| 3 | open.url | 注解属性（@FeignClient） | AuthFeignInner.java 等 17 处 | ⚠️ 复用（需确认） |
| 4 | xxl.job.executor.port | 单值（@Value，有默认值 :9999） | XxlJobConfig.java | 🆕 新增，可不配 |

## 外部平台操作清单（基线：<base>）

| 序号 | 类型 | 标识（handler / topic / queue） | 所在文件 | 建议操作 |
|---|---|---|---|---|
| 1 | xxl-job 任务 | contestStatusAdvanceScan | ContestHandler.java | 🆕 调度中心新建任务（配 cron/路由/告警）——漏配=任务不跑 |
| 2 | MQ 订阅 | topic: contest-expert-assign | ExpertAssignConsumer.java | 🆕 MQ 平台确认 topic 已建 + 订阅关系 |
| 3 | xxl-job 任务 | contestOldScan | ContestHandler.java | ⚠️ 疑似下线/改名，平台旧任务需下线或改指向 |

## 数据库变更清单（基线：<base>）

| 序号 | 语句类型 | 目标表 | 变更内容 | 所在文件 | 执行时机 |
|---|---|---|---|---|---|
| 1 | DDL-建表 | contest_info | CREATE TABLE | V01__contest.sql | 🟢 部署前 |
| 2 | DDL-加列 | contest_info | ADD COLUMN status | V01__contest.sql | 🟢 部署前 |
| 3 | DDL-删列 | contest_old | DROP COLUMN legacy_flag | cleanup.sql | 🔴 部署后/下轮，确认旧代码全下线 |
| 4 | DML-订正 | contest_user | UPDATE 回填 dept_id | backfill.sql | 🟡 部署后、验证前 |

## 知会项（无需操作，发版负责人应知）

| 事项 | 所在文件 | 说明 |
|---|---|---|
| 新增 @Scheduled 后台任务 | DataSyncTask.java | 集群每实例都会执行，确认幂等/分布式锁 |

## 发布时刻表（按本次 diff 汇总）

（条件式生成：每步只列本次 diff 实际产出的项，该类无产出则整步跳过）

1. **部署前**：执行前置 DDL（列出）→ 配置中心添加必配 Key（列出；有默认值项可不配）→ MQ 平台确认 topic 已建 + 订阅关系（列出——消费者启动即订阅，必须先于部署）
2. **部署应用**
3. **部署后**：xxl-job 调度中心新建任务（列出——executor 注册后再建，避免旧实例触发不存在的 handler）→ 执行 DML 订正（列出）→ 执行后置 DDL（列出，先确认旧代码全下线）
4. **验证**：destructive DDL 准备反向回滚语句（列出）；孤儿任务/订阅下线（列出）
```

末尾纯文本代码块，仅列「新增」状态的**配置 Key**，每行一个，供直接粘贴到配置中心；有默认值的单独一节与必配项区分（平台操作、数据库变更与知会项无可粘贴形态——SQL 的执行载体是 .sql 文件本身——均不进纯文本块）：

```
training.template.url
thread.pool.order.core-size
（…其余必配 Key）

# 以下有默认值，可不配
xxl.job.executor.port  # 默认 9999
```

各节均无新增时，明确输出「本次 diff 无新增配置 Key、平台操作项与数据库变更」，不要输出空表格（发布时刻表随之无内容，同样不输出）。

## 术语

全篇统一使用：配置 Key、基线分支、新增行、复用、注解属性、配置组、默认值、平台操作清单、handler 名、订阅关系、孤儿任务、知会项、前置 DDL、后置 DDL、订正脚本、发布时刻表。

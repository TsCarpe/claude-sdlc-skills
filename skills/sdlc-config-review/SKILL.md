---
name: sdlc-config-review
description: 扫描当前分支相对基线分支（master/main）的 Java 代码 diff，提取发版前需在代码之外人工处理的事项——①配置中心（Apollo/Nacos）Key：@Value 单值、@ConfigurationProperties 前缀、任意注解属性中的 ${...} 占位符；②外部平台注册操作：@XxlJob 任务（新增/改名/孤儿检测）、RocketMQ/Kafka/Rabbit listener 订阅关系；③行为知会项（@Scheduled 集群重复执行等）。产出配置 Key 清单 + 平台操作清单 + 知会项。Use when 用户要梳理上线配置清单、检查新增配置 Key、准备 Apollo/Nacos 发版配置、检查新增定时任务/xxl-job 任务/MQ 订阅，或说 config-sentinel、config review、Apollo/Nacos key audit、release config checklist、xxl-job audit、上线检查。
---

# SDLC Config Review

发版前梳理「需要在代码之外人工处理的配置与注册事项」：配置中心 Key（Apollo/Nacos）、调度任务（xxl-job）、MQ 订阅关系，以及无需操作但应知会发版负责人的行为变化。只分析 `.java` 文件，忽略 XML/YAML/properties/前端文件。

## 工作流

按顺序执行，复制此 checklist 跟踪进度：

```
Config Review Progress:
- [ ] Step 1: 确定基线分支，生成 diff 临时文件
- [ ] Step 2: 读取 diff 全文，按四种模式提取，排除噪音
- [ ] Step 3: 定位文件、去重、标记状态；孤儿/改名检测
- [ ] Step 4: 按模板输出三节清单 + 纯文本块
```

### Step 1: 基线分支与 diff 提取

1. 基线分支：用户指定优先；否则自动探测（依次尝试 master、main）
2. 基线分支不存在或当前分支已合并时，**明确报错提示用户，不静默换基线**
3. diff 落临时文件（防管道截断/编码问题，不要直接管道消费）：
   - bash/zsh：`git diff <base>...HEAD -- "*.java" > diff_temp.txt`
   - PowerShell：`git diff <base>...HEAD -- "*.java" | Out-File -Encoding utf8 diff_temp.txt`

### Step 2: 读取与内存解析

读取 diff_temp.txt 全文，在上下文中分析提取。**不要在命令行跑正则提取**（跨平台转义不可靠）；Claude Code 环境下可用 Grep 工具对临时文件粗筛辅助定位，但判定以读文分析为准。

只认**新增行**（`+` 开头）中的四处合法位置：

**模式 A**：`@Value("${...}")` → 提取 Key。识别默认值写法 `${key:default}`，标注「有默认值 :default」

**模式 B**：`@ConfigurationProperties(prefix = "...")` → 提取前缀，类型标「配置组，需核对该类全部字段」

**模式 C**：任意注解 `@Xxx(...)` 属性值中的 `"${...}"` 占位符 → 提取 Key，类型标「注解属性」并附来源注解名（如 @FeignClient / @RocketMQMessageListener / @Scheduled / @KafkaListener）。**规则通用，不做注解白名单**

**模式 D（平台注册型注解——提取的是「要在平台建/改的东西」，不是配置 Key）**：

- `@XxlJob("name")` / `@XxlJob(value = "name")` → 提取 handler 名，进「外部平台操作清单」。漏建任务 = 功能静默缺失，是本模式最高优先级
- `@RocketMQMessageListener` / `@KafkaListener` / `@RabbitListener` → 逐属性分流：值为 `"${...}"` 的走模式 C 进 Key 清单；**字面量值**（如 `topic = "contest-expert-assign"`、`groupId = "order-group"`）进平台操作清单；**配置引用形态双列**——topic/consumerGroup 的值取自配置中心时，平台仍需按该配置值建 topic/订阅关系，故 Key 清单之外**在平台操作清单同时列一行**，标识写 `${key}（配置引用）`；**常量引用**（`topic = TopicConst.X`）静态不可提取，尾部人工确认提示
- `@Scheduled` → 不进操作清单，进「知会项」：无外部配置，但集群下**每实例都会执行**，需确认幂等/分布式锁

**噪音排除规则（命中即丢弃）**：
1. 注释、JavaDoc、日志字符串中的匹配
2. 删除行（`-` 开头）与上下文行中的匹配（平台注册项除外——删除行参与孤儿检测，见 Step 3）
3. **MyBatis SQL 占位符**：`@Select/@Update/@Insert/@Delete` 注解属性内的 `${}` 及字符串字面量中的 SQL `${}`（如 `order by ${col}`）不是 Spring 配置
4. 代码生成器模板字符串中的 `${}`
5. 动态 key（如 `environment.getProperty(变量)`）静态不可提取；发现时在结果尾部提示「存在动态取值，需人工确认」，不计入清单

### Step 3: 定位与去重

- 每个唯一 Key / handler / 订阅项记录首次出现的文件路径 + 来源注解
- 配置 Key 区分两种状态：「🆕 新增」（diff 中新增行引入）与「⚠️ 复用（需确认）」（Key 已存在于存量代码或删除行同时出现——典型为重构移动）
- 同一 Key 多处引用合并为一行，所在文件列首个 + 计数（如 `Foo.java 等 3 处`）
- **孤儿/改名检测（平台注册项专用）**：删除行出现、新增行未出现的 handler 名 / 字面量 topic / queue → 标「⚠️ 疑似下线或改名：平台旧任务/订阅需同步处理（下线或改指向）」；删除行与新增行**同名** → 重构移动，不告警

### Step 4: 输出

严格用以下模板（三节清单 + 纯文本块）：

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

## 知会项（无需操作，发版负责人应知）

| 事项 | 所在文件 | 说明 |
|---|---|---|
| 新增 @Scheduled 后台任务 | DataSyncTask.java | 集群每实例都会执行，确认幂等/分布式锁 |
```

末尾纯文本代码块，仅列「新增」状态的**配置 Key**，每行一个，供直接粘贴到配置中心；有默认值的单独一节与必配项区分（平台操作与知会项无可粘贴形态，不进纯文本块）：

```
training.template.url
thread.pool.order.core-size
（…其余必配 Key）

# 以下有默认值，可不配
xxl.job.executor.port  # 默认 9999
```

三节均无新增时，明确输出「本次 diff 无新增配置 Key 与平台操作项」，不要输出空表格。

## 术语

全篇统一使用：配置 Key、基线分支、新增行、复用、注解属性、配置组、默认值、平台操作清单、handler 名、订阅关系、孤儿任务、知会项。

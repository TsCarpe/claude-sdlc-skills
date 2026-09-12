---
name: sdlc-config-review
description: 扫描当前分支相对基线分支（master/main）的 Java 代码 diff，提取三类需要配置中心（Apollo/Nacos）注入的配置项——@Value 单值、@ConfigurationProperties 前缀、任意注解属性中的 ${...} 占位符（如 @FeignClient/@RocketMQMessageListener），产出上线新增 Key 清单（结果表格 + 可复制纯文本块）。Use when 用户要梳理上线配置清单、检查新增配置 Key、准备 Apollo/Nacos 发版配置、提到配置项 diff、@Value、ConfigurationProperties、注解占位符，或说 config-sentinel、config review、Apollo/Nacos key audit、release config checklist。
---

# SDLC Config Review

发版前梳理「需要在配置中心新增哪些配置 Key」。只分析 `.java` 文件的**新增行**，忽略 XML/YAML/properties/前端文件。

## 工作流

按顺序执行，复制此 checklist 跟踪进度：

```
Config Review Progress:
- [ ] Step 1: 确定基线分支，生成 diff 临时文件
- [ ] Step 2: 读取 diff 全文，按三种模式提取，排除噪音
- [ ] Step 3: 定位文件、去重、标记新增/复用
- [ ] Step 4: 按模板输出表格 + 纯文本块
```

### Step 1: 基线分支与 diff 提取

1. 基线分支：用户指定优先；否则自动探测（依次尝试 master、main）
2. 基线分支不存在或当前分支已合并时，**明确报错提示用户，不静默换基线**
3. diff 落临时文件（防管道截断/编码问题，不要直接管道消费）：
   - bash/zsh：`git diff <base>...HEAD -- "*.java" > diff_temp.txt`
   - PowerShell：`git diff <base>...HEAD -- "*.java" | Out-File -Encoding utf8 diff_temp.txt`

### Step 2: 读取与内存解析

读取 diff_temp.txt 全文，在上下文中分析提取。**不要在命令行跑正则提取**（跨平台转义不可靠）；Claude Code 环境下可用 Grep 工具对临时文件粗筛辅助定位，但判定以读文分析为准。

只认**新增行**（`+` 开头）中的三处合法位置：

**模式 A**：`@Value("${...}")` → 提取 Key。识别默认值写法 `${key:default}`，标注「有默认值 :default」

**模式 B**：`@ConfigurationProperties(prefix = "...")` → 提取前缀，类型标「配置组，需核对该类全部字段」

**模式 C**：任意注解 `@Xxx(...)` 属性值中的 `"${...}"` 占位符 → 提取 Key，类型标「注解属性」并附来源注解名（如 @FeignClient / @RocketMQMessageListener / @Scheduled / @KafkaListener）。**规则通用，不做注解白名单**

**噪音排除规则（命中即丢弃）**：
1. 注释、JavaDoc、日志字符串中的匹配
2. 删除行（`-` 开头）与上下文行中的匹配
3. **MyBatis SQL 占位符**：`@Select/@Update/@Insert/@Delete` 注解属性内的 `${}` 及字符串字面量中的 SQL `${}`（如 `order by ${col}`）不是 Spring 配置
4. 代码生成器模板字符串中的 `${}`
5. 动态 key（如 `environment.getProperty(变量)`）静态不可提取；发现时在结果尾部提示「存在动态取值，需人工确认」，不计入清单

### Step 3: 定位与去重

- 每个唯一 Key 记录首次出现的文件路径 + 来源注解
- 区分两种状态：「🆕 新增」（diff 中新增行引入）与「⚠️ 复用（需确认）」（Key 已存在于存量代码或删除行同时出现——典型为重构移动）
- 同一 Key 多处引用合并为一行，所在文件列首个 + 计数（如 `Foo.java 等 3 处`）

### Step 4: 输出

严格用以下模板：

```markdown
## 配置 Key 清单（基线：<base>）

| 序号 | 配置 Key / 前缀 | 类型（来源注解） | 所在文件 | 建议操作 |
|---|---|---|---|---|
| 1 | training.template.url | 单值（@Value） | ProjectBusiness.java | 🆕 新增，配置中心添加 |
| 2 | thread.pool.order | 配置组（@ConfigurationProperties） | ThreadPoolConfig.java | 🆕 新增，需核对该类全部字段 |
| 3 | open.url | 注解属性（@FeignClient） | AuthFeignInner.java 等 17 处 | ⚠️ 复用（需确认） |
| 4 | xxl.job.executor.port | 单值（@Value，有默认值 :9999） | XxlJobConfig.java | 🆕 新增，可不配 |
```

末尾纯文本代码块，仅列「新增」状态的 Key，每行一个，供直接粘贴到配置中心；有默认值的单独一节与必配项区分：

```
training.template.url
thread.pool.order.core-size
（…其余必配 Key）

# 以下有默认值，可不配
xxl.job.executor.port  # 默认 9999
```

无新增配置时，明确输出「本次 diff 无新增配置 Key」，不要输出空表格。

## 术语

全篇统一使用：配置 Key、基线分支、新增行、复用、注解属性、配置组、默认值。

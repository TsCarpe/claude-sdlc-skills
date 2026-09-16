# eval-2：规则编写正确性

## 输入

- query：「加三条规则：Controller 禁 printStackTrace；每个 @PostMapping 必须带 @LogRecord；Req 类含 page 字段必须有 @Min(1)」
- 已接入项目：`guardrails.yaml` 已有 `version: 1` 与两条存量规则

## expected_behavior

- [ ] printStackTrace → `type: forbid`，glob 覆盖 Controller 或 `**/*.java`
- [ ] @LogRecord → `type: count_ge` + `anchor: "@PostMapping"`（锚点计数语义，不误用 require）
- [ ] page/@Min → `type: require_if` + `when` 命中 page 字段模式（require_if 必带 when）
- [ ] id 唯一、message 中文可读；正则注意 YAML 转义（README 提示单引号防转义坑）
- [ ] 改完至少 pipe-test 复验一条新规则实际拦截

## 判负线

「每个接口必须带注解」写成 require（文件出现一次即通过的语义错配）；require_if 漏写 when。

# 开发放行豁免模板

路径：`sdlc/<需求名>/review/exemptions/exemption-<YYYYMMDD>.md`

用于用户显式确认跳过评审关口、但需要留痕的场景。放在 `exemptions/` 子目录，避免被 `review/*.md` 的 issues 扫描器误认。值内禁止 `|`（会截断头部 kv 解析）。

```markdown
# <需求名> 开发放行豁免（<日期>）

| 字段 | 值 |
|---|---|
| 豁免类型 | 开发放行 |
| 基线 | <最新 issues 文件名；无 issues 写「无」> |
| 范围 | 全量 / <功能点或切片列表>（留痕字段，不机械限制代码范围） |
| 理由 | <为什么本次跳过评审> |
| 确认人 | <用户> |
| 确认日期 | <YYYY-MM-DD> |
| 风险自担 | 是 |
```

## 校验规则（guard_dev.py）

- 七字段齐全；`豁免类型` 以「开发放行」开头；`风险自担` 以「是」开头。
- `基线` 必须等于 `review/` 最新 issues 文件名；无 issues 时写「无」。基线不匹配 = 旧豁免已失效，拒绝放行。
- A/B 级 issues 头部 `reviewMode=degraded` 时不允许豁免绕过。
- 豁免只解锁开发；`sdlc-test static/exec` 仍受关卡1约束（人工确认 cases 或 gate 已放行）。

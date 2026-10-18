# eval-11：选择题化产出纪律（options / module / layer / pids）

> 官方 JSON 结构场景（CONTRIBUTING「evals 规范格式」）。

## 输入（文档特征，评选活动类中性虚构）

- query：「体检这份需求文档 <本地 md 文件>，产出体检报告 + PM 确认清单，并按 sdlc-sync 契约整理 payload 字段」
- 冲突格：「作品可见范围」正文 A 处写「仅参评人可见」，B 处写「全体参评人可见」——冲突类，应选项化
- 缺失格：全文未见「活动截止后能否撤回作品」——纯缺失类，无可枚举候选
- 补充格：某条款「评审」误写为「平审」——维度外「补充」类命中
- 断点：主流程「提交作品 → ?」（可见范围未定，关联上述冲突）

```json
{
  "skills": ["sdlc-intent"],
  "query": "体检这份需求文档 <本地 md 文件>，产出体检报告 + PM 确认清单，并按 sdlc-sync 契约整理 payload 字段",
  "files": ["sdlc/评选活动/req-评选活动.md"],
  "expected_behavior": [
    "冲突类问题（可见范围两处口径不一致）在 pm-checklist 问题格内换行列出选项：`<br>可选：A. <选项全文>（推荐——<一句理由>）` 形态，2-4 项，选项文本自包含全文",
    "AI 有倾向时至多一项标「（推荐——理由）」且常显理由；无倾向则一项都不标",
    "纯缺失类问题（撤回规则）不出现「可选：」选项行，走自由文本作答",
    "payload `items[]` 冲突类问题带 `options` 数组（key 大写字母唯一 / text 全文快照 / why 一句话 / recommended 至多一项 true）与 `module`（= digest 功能点地图的模块，与 `fr_points[].module` 同体系）",
    "payload `items[]` 与 `audit.items[]` 每条命中带 `layer`（字符串 \"1\"-\"7\"，七层枚举内取值）",
    "维度外「补充」类命中（错别字）不携带 layer 字段，不发明 0 号层",
    "pm-checklist md 本身不渲染模块名与层号（module/layer 落 payload 不渲染，PM 无感）",
    "digest `flows[]` 断点行的 `pids[]` 仅引用本 payload `items[].seq`（或存量 L 系 seq）；无相关澄清的断点行不带 pids"
  ]
}
```

## 判负红线

- 纯缺失类/开放类问题硬造「可选：」选项（无可枚举候选却编 options）
- 维度外「补充」类命中携带 layer，或发明 0 号层/七层之外的层号
- options text 写「同上」「见上文」类指代（非自包含全文快照，重推后会 key 漂移）
- pm-checklist 渲染出模块名或层号（module/layer 只落 payload）
- flows `pids[]` 引用本 payload 之外的机器编号（存量 P 系/平台合并后才分配的编号）

# eval-a：推送用例只带缺陷编号引用（defectRefs）

> 官方 JSON 结构场景（CONTRIBUTING「evals 规范格式」）。缺陷生命周期与执行证据留在本地 cases.md，不上平台。

## 输入（本地用例文件，评选活动类中性虚构）

`sdlc/评选活动/test/cases.md` 含：

- 缺陷跟踪表：`BUG-01（R1·已修复）`、`BUG-02（R1·待修复）`，附现象/预期差异/证据引用
- 用例结果字段：`TC-03 失败（R1）→ BUG-02`，证据含截图名与接口 URL
- 双向追踪表：用例 `需求.FR-03` 关联

```json
{
  "skills": ["sdlc-sync"],
  "query": "/sdlc-sync push-cases 评选活动",
  "files": ["sdlc/评选活动/test/cases.md"],
  "expected_behavior": [
    "payload 的用例条目只带缺陷编号引用文本（defectRefs，如 `BUG-02（R1·待修复）`），不含缺陷详情、生命周期、执行结果或证据",
    "用例状态按 cases.md 头部「审核状态」映射：已确认 → reviewed，否则 draft",
    "verifyRefs 从「重点验证项」表提取，使用 `体检.Pxx` / `需求.Axx` 全称编号",
    "首推前向用户展示条数并抽样 3 条，确认后再 POST /api/cases",
    "409 版本冲突时展示 conflicts 明细等用户裁决，不强行重推"
  ]
}
```

## 判负红线

- payload 中出现缺陷详情/生命周期/执行结果/证据字段（缺陷生命周期不上平台）
- 把 `BUG-02（R1·待修复）` 之外的缺陷描述或截图/接口原文写进 payload
- 未展示条数与抽样即推送；409 后强行重推

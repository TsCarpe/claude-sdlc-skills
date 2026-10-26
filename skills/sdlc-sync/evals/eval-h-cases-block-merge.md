# eval-h：pull-dev-bundle 本地已有 cases.md 的区块合并

平台卡：published，用例 TC-01（标题已变）/TC-02 不变/新增 TC-04，**本地曾推 TC-03 已被平台删除**（全量替换语义），本地 TC-01 有执行结果 + TC-03 失败挂 BUG-02 且有证据行；本地另含非 FR 追踪行（状态机边）与「静态.01」重点验证项行。

```json
{
  "skills": ["sdlc-sync"],
  "query": "/sdlc-sync pull-dev-bundle 评选活动 only:cases",
  "files": ["sdlc/评选活动/test/cases.md", "sdlc/评选活动/.platform"],
  "expected_behavior": [
    "先产出 diff 报告（新增 TC-04 / 删除 TC-03 及其将带走的执行历史：结果列、BUG-02 关联、证据行 / 变更 TC-01 标题 / 不变 TC-02），等待用户确认，确认前不改文件",
    "确认后按区块合并：总览 ID/标题/优先级列按平台刷新；TC-01 结果列保留、TC-04 三列（设计技术/结果/spec/BUG）留空",
    "TC-03 已删但有过程数据 → 总览与明细行保留并标注「已下线（平台删除于 <拉取日>）」，不随平台删除",
    "缺陷跟踪表整块保留，BUG-02 关联 TC-03 不清理（diff 报告中已提示）",
    "双向追踪表 FR 行按平台 frPoints/coveredBy 重建，本地非 FR 前缀行（状态机边）原样保留",
    "重点验证项：体检.P/需求.A 行按 verifyRefs 并集重建，「静态.」前缀行保留",
    "头部审核状态按平台刷新（全 reviewed→已确认（平台 日期）），阶段进度勾选保留",
    ".platform.pulled.cases 凭据写回（count + maxUpdatedAt）"
  ]
}
```

## 判负红线

- 未等用户确认直接覆盖 cases.md
- TC-03（有执行历史）被静默删除、或删除其结果/BUG 关联/证据
- 任何过程数据列（结果/spec/BUG/证据/缺陷表/阶段进度）被平台重建清空
- 非 FR 追踪行或「静态.」验证项行被清掉
- 追踪表漏掉平台新增的 FR 行
- 仅凭 list 面（无 pre/steps/expect）重建明细

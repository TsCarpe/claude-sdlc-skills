# pull-dev-bundle 细则：凭据 / cases 区块合并 / gate 投影

SKILL.md 第 7 节的主干在此展开。本文件是 sdlc-sync 的操作细则，不是新契约源——API 字段以 [payload-schema.md](payload-schema.md) 为准。

## 凭据与重拉（.platform.pulled）

```json
{
  "reqId": "REQ-2026-001",
  "pulled": {
    "intake":   {"digestVersion": 3, "at": "2026-10-26"},
    "standard": {"version": 2, "at": "2026-10-26"},
    "design":   {"version": 1, "at": "2026-10-26"},
    "cases":    {"count": 42, "maxUpdatedAt": "2026-10-20 10:00:00", "at": "2026-10-26"},
    "gate":     {"roundNo": 1, "releasedAt": "2026-10-22 10:00:00", "at": "2026-10-26"}
  }
}
```

- 每产物**落盘成功后立即写回对应键**（半程失败时已写键即「已完成」，重跑跳过或按用户指示刷新）
- 重拉比对口径：intake ← `detail.digest.version`；standard ← `detail.standard.version`；design ← design view `finalized.version`；cases ← list 的条数 + `max(updatedAt)`；gate ← 最新轮 `roundNo` + `releasedAt`。任一变化 → 该产物重拉（cases 变化仍走 diff+确认流程）
- design 为 skipDeclared 时写 `"design": {"skipDeclared": {"by": "…", "at": "…"}, "at": "…"}`
- **评论盲区**：平台用例评论不 bump updatedAt（add_comment 不写 test_case.updated_at），凭据检测不到评论变化——SKILL 主干已声明「评论不回流、人工上平台查看」，不在此重复建凭据

## cases 区块合并

### 第一步：diff 报告（本地已有 cases.md 时必做，用户确认前不动文件）

平台 list + 逐条 detail 与本地 cases.md 逐用例比对，报告分四段：

1. **新增**：平台有、本地总览无的 ID（列出标题/优先级）
2. **删除**：本地有、平台无的 ID——**逐条列明将带走的执行历史**（该 ID 的结果列/spec 列/BUG 列/证据行/缺陷表关联，非空才列）
3. **变更**：标题/优先级/pre/steps/expect/points 任一不同（列字段级差异）
4. **不变**：计数

### 第二步：确认后按区块合并（过程数据一律保留）

| 区块 | 平台重建 | 本地保留 |
|---|---|---|
| 头部元数据 | 审核状态（全 reviewed → `已确认（平台 <拉取日>）`；任一 draft → `草稿` 并提示）、风险分级（card.riskTier） | 阶段进度勾选 |
| 设计技术覆盖矩阵 | —（平台无此维度） | 整区块；平台用例集变化后过时 → 提示重跑 `/sdlc-test cases`（用户拍板） |
| 双向追踪表 | FR 行集 = detail.frPoints 全集、来源列 = fr_point.source、覆盖用例 ID 列 = frPoints.coveredBy 反查 | **非 `需求.FR-` 前缀行**（状态机边/章节行）原样保留；FR 行的「未覆盖原因」列原文随行保留（平台行仍有未覆盖时） |
| 重点验证项 | `体检.P` / `需求.A` 前缀行 = 各用例 verifyRefs 并集 + 关联用例 ID | **`静态.` 前缀行**原样保留（平台无对应物） |
| 执行分组（如有） | — | 整区块 |
| 用例总览 | ID/标题/优先级三列按平台对齐（行集增删、行内值刷新） | 设计技术列（按 ID 匹配回填）、结果/spec/BUG 列；新增行此三列留空 |
| 用例明细 | 行集按平台 ID 对齐；每条的 优先级/前置/步骤/预期/关联规则(points) 按平台刷新 | 反馈层级/设计技术/角色、证据行（按 ID 匹配回填） |
| 缺陷跟踪表 | — | 整区块；「关联用例」指向已删 ID 时不清理，diff 报告里提示 |

### 已删用例处置（「删除」≠ 清除）

- 平台已删、本地**有过程数据**（结果/spec/BUG/证据任一非空）→ **保留行**：总览与明细行尾标注 `已下线（平台删除于 <拉取日>）`，缺陷表关联不动
- 平台已删、本地**纯空白** → 随平台删除
- 理由：push-cases 是全量替换语义（本地精简重推即触发平台删除），执行历史是本地资产、不可随重推蒸发

## gate 投影

输入：gate view 最新轮（rounds 末位）+ 该轮 issuesMd + detail.card.riskTier。

1. **底稿** = 平台留档 md 原文（ingest 时已过 md×json 同源校验），文件名 `issues-<openedAt的YYYYMMDD>-r<roundNo>.md`
2. **头部改写**（兼容两种原文形态——已有该行则改写、无则追加到头部 kv 表末行；行必须落在首个 `##` 之前，guard 的 header_kv 只认这里）：
   - `| 评审状态 | <released ? 已放行（releasedAt 的 YYYY-MM-DD） : 待裁决> |`
   - `reviewMode` / `fanout` / `contextMode` 三行与 round 落库值逐行核对，不一致以 round 落库值改写并向用户报告
   - **风险分级行**与 `card.riskTier` 不一致 → 以 card.riskTier 改写并向用户报告（否则 tier 升级后 guard_exec 三口径校验永久拦死且无出路）
3. **裁决回填**（按 issue.code 定位原文行）：

   | 平台字段 | 裁决列写法 | 落点/状态列写法 |
   |---|---|---|
   | verdict=revise | `落改（<verdictNote>）` | `落点：<revLocation> ｜ <revStatus=pending→待执行 / done→已执行>`（revLocation 平台不约束内容形态，已含「｜待执行/｜已执行」类后缀时不再追加状态段，以 revStatus 为准） |
   | verdict=reject | `驳回：<verdictNote>` | `—` |
   | verdict=query | `存疑：<verdictNote>` | `—` |
   | verdict 空（未裁决） | 留空 | 留空 |

4. **裁决记录汇总**（第四节）按 units 分组重建：revise / 驳回 / 存疑 / 未裁决 四类 + 计数行；**filed 备案组不进本表**（备案计数归原文速览统计，防止造出模板外裁决行）。released 轮在计数行后写放行结论行：`放行结论：平台放行（by <releasedBy> at <releasedAt>）`
5. **落盘守卫**：
   - 落盘前扫 `review/`（一层，排除 exemptions/）：同名文件先比对再覆盖
   - **双向核对**：存在**轮号 ≥ 投影轮号**的任何本地 issues 文件 → 停，列两侧文件让用户裁决（latest_by_name 是日期优先，旧日期高轮号的本地待裁决轮不能被静默绕过）
   - 向用户注明：文件名日期 = 开轮日（openedAt），头部放行日 = releasedAt，两者可以不同

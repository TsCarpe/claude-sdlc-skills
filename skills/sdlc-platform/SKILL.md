---
name: sdlc-platform
description: "Drives the first-round requirement flow on the product platform through two MCP endpoints: import a source, start quality check, adopt the quality draft, answer one clarification at a time, synthesize and publish the platform standard draft, export the published markdown, or hand it to a developer as a local file plus a starter sentence. The platform stays the source of truth. The agent never writes its own standard document, never answers clarifications, and never publishes without an explicit human yes. Use when the user wants to 导入需求 / 开始质检 / 采纳质检 / 澄清这题 / 生成标准文档 / 发布标准文档 / 导出定稿 / 交给开发 / 到哪了. 触发词：导入需求、开始质检、采纳质检、澄清这题、生成标准文档、发布标准文档、导出定稿、交给开发、到哪了。"
---

# 平台首发链路（sdlc-platform）

人在对话里走完首发需求。正式数据在产物平台。本 skill 只调用两个 MCP，不自己做质检、不自己写标准文档、不调用 `sdlc-sync`。

设计、用例、门禁、变更重走不在这一版。卡片 `step` 为 `changed` 时，只告诉人这张卡在变更流程里，然后停下。点名了步骤也一样。

## 前置

两个 MCP 都要连上。平台地址是环境变量 `SDLC_PLATFORM_URL`。

| MCP | 路径 | 工具 |
|---|---|---|
| 输入 `sdlc-in` | `/mcp/in` | `get_iteration_status`、`import_requirement`、`start_quality_check`、`adopt_quality_draft`、`submit_clarification`、`start_standard_doc`、`publish_standard` |
| 输出 `sdlc-out` | `/mcp/out` | `export_standard`、`handoff_to_developer` |

平台开了写保护时，输入 MCP 要带同一个 `X-Token`。查状态、导出、交给开发不带。工具返回 `ok: false` 时，把 `error` 告诉人并停下。有 `pendingAssumptions` 时向人要放行理由，再带 `confirm_note` 重发。有 `machineCheck` 时把失败项给人，不要改文档。

## 进入哪一步

先看人有没有点名步骤（命令速查里的那九句）。点了就做那一步。没点名，或只给了迭代名，就先 `get_iteration_status`。

| `step` | 做什么 |
|---|---|
| `new` | 按新建。缺什么单独问什么：迭代名、需求名、来源（飞书链接或正文）。三样都在就立刻导入，并复述这三样。需求名不要照抄迭代名 |
| `importing` | 见下方「等导入」 |
| `import_failed` | 立刻停下，转述 `message` |
| `quality_ready` | 告诉人原文已在，问要不要「开始质检」。不要自己开跑 |
| `quality_running` / `synthesize_running` | 告诉人还在跑。不要在对话里等。让人去平台看，或稍后再说「到哪了」 |
| `adopt` | 把 `qualityDraftMarkdown` 给人看。人说「采纳质检」才调用 `adopt_quality_draft` |
| `clarify` | 只展示 `nextQuestion` 这一题，然后等人。推荐项只标注「推荐」，不要替人选、不要替人打字 |
| `synthesize_ready` | 告诉人澄清已全部处置，问要不要「生成标准文档」 |
| `publish` | 把 `standardDraftMarkdown` 原样给人核对。人说「发布标准文档」才调用 `publish_standard`。不要改这篇草稿 |
| `published` | 告诉人已发布，可以「导出定稿」或「交给开发」 |
| `changed` | 只提示，停下 |

人说的是新建，但这张卡其实已经在：改走上表，不要再建一张。

## 等导入

`import_requirement` 返回后开始计时，反复调用 `get_iteration_status`，累计不超过 30 秒。

- `step` 离开 `importing` 和 `import_failed`，并且原文块已经在（`quality_ready` 或更后）：成功。复述迭代名、需求名、来源，然后问要不要「开始质检」。不要调用 `start_quality_check`。
- `import_failed`，或当前任务已是失败/取消：立刻停下，转述原因。
- 满 30 秒仍是 `importing`：停下。告诉人下次用同一个迭代名再说「到哪了」。

质检和标准文档合成发起后都不要等。

## 澄清这一题

`submit_clarification` 的 `action` 只能是 `option`、`text`、`reject`、`defer` 之一，而且必须是人刚刚说的：

| 人的决定 | action | 其他字段 |
|---|---|---|
| 选某个选项 | `option` | `option_key` |
| 选某个选项，再补一句 | `option` | `option_key` 加 `extra`。告诉人这会记成「选项全文（补充：…）」 |
| 选项不对，或这题没有选项 | `text` | `text` 为人的原话。不传 `option_key` |
| 驳回 | `reject` | `note` 必填。这句话不进定稿 |
| 挂起 | `defer` | 可带 `note` |

一次只处置人正在答的那一题。答完再取下一题，不要连答。

## 发布

`publish_standard` 提交的是平台上已有的标准文档草稿，不是你重写的正文。红级挂起不能发布。黄级或蓝级挂起时，工具会拒绝并给出 `pendingAssumptions`：向人要一句放行理由，放进 `confirm_note` 再发。理由必须是人写的。

## 导出定稿

调用 `export_standard`。把返回的 `markdown` 贴回对话，并带上卡号和版本。不要写文件。`ok: false` 时什么都不要写。

## 交给开发

调用 `handoff_to_developer`。`ok: false` 时不要写任何文件。成功后在当前开发仓库根目录写两份，路径用工具返回的，不要改名：

1. 把 `markdown` 写到 `markdownPath`。目录没有就建。同一天的同名文件覆盖。
2. `.platform` 按 `platformWrite` = `keep-if-same-req`：文件已在，且 JSON 里的 `reqId` 等于返回的 `requirementId`，则一个字都不要改（里面可能有拉取凭据）。文件没有、读不出 JSON、或 `reqId` 是另一张卡，则把 `platformJson` 原样写入 `platformPath`。

写完后，把返回的 `starter` 原句交给人。不要改写。

## 命令速查

| 人说 | 调用 |
|---|---|
| 导入需求 | `import_requirement`，然后按「等导入」 |
| 开始质检 | `start_quality_check` |
| 采纳质检 | `adopt_quality_draft` |
| 澄清这题 | `submit_clarification` |
| 生成标准文档 | `start_standard_doc` |
| 发布标准文档 | `publish_standard` |
| 导出定稿 | `export_standard` |
| 交给开发 | `handoff_to_developer`，然后按上面写文件 |
| 到哪了 | 只调用 `get_iteration_status` |

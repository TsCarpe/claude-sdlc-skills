---
name: sdlc-platform
description: "在产物平台上走完首发需求：新建并导入原文、开始质检、采纳质检草稿、逐题澄清、合成并发布标准文档、导出定稿、交给开发。平台是定稿出处。不自己写标准文档，不替人采纳、答题或发布。用法：/sdlc-platform new|status|import|quality|adopt|clarify|synthesize|publish|export|handoff [迭代名]。不带子命令时先列出命令，再问要做哪一步。也响应：导入需求、开始质检、采纳质检、澄清这题、生成标准文档、发布标准文档、导出定稿、交给开发、到哪了。"
---

# 平台首发链路（sdlc-platform）

人在对话里输入 `/sdlc-platform`，再跟子命令。正式数据在产物平台。本 skill 只调用两个 MCP，不自己做质检、不自己写标准文档、不调用 `sdlc-sync`。

设计、用例、门禁、变更重走不在这一版。卡片 `step` 为 `changed` 时，只告诉人这张卡在变更流程里，然后停下。点名了步骤也一样。

## 用法

菜单里这一项是 `/sdlc-platform`，旁边的说明来自上面的 description。MCP 工具不是给人点的命令，由本 skill 按子命令去调。

| 子命令 | 等同 | 做什么 |
|---|---|---|
| `new [迭代名]` | 新建迭代 | 缺迭代名、需求名、来源就分开问。三样齐了再导入 |
| `status [迭代名]` | 到哪了 | 只查状态 |
| `import [迭代名]` | 导入需求 | 导入并等原文落库 |
| `quality [迭代名]` | 开始质检 | 触发质检，不等草稿 |
| `adopt [迭代名]` | 采纳质检 | 采纳平台上的质检草稿 |
| `clarify [迭代名]` | 澄清这题 | 处置当前一题 |
| `synthesize [迭代名]` | 生成标准文档 | 发起平台合成，不等草稿 |
| `publish [迭代名]` | 发布标准文档 | 发布平台上已有的草稿 |
| `export [迭代名]` | 导出定稿 | 把已发布 Markdown 回到对话 |
| `handoff [迭代名]` | 交给开发 | 写本地定稿和 `.platform`，给出开工句 |

没写子命令，也没给迭代名：把这张表给人，问要做哪一步。不要一上来只问迭代名。

只给了迭代名、没有子命令：先 `get_iteration_status`，按卡片状态继续。

子命令缺迭代名：只问迭代名。`new` 还缺需求名或来源时，缺哪样问哪样。中文命令和子命令同等。

## 前置

两个 MCP 都要连上。平台地址是环境变量 `SDLC_PLATFORM_URL`。

| MCP | 路径 | 工具 |
|---|---|---|
| 输入 `sdlc-in` | `/mcp/in` | `get_iteration_status`、`import_requirement`、`start_quality_check`、`adopt_quality_draft`、`submit_clarification`、`start_standard_doc`、`publish_standard` |
| 输出 `sdlc-out` | `/mcp/out` | `export_standard`、`handoff_to_developer` |

平台开了写保护时，输入 MCP 要带同一个 `X-Token`。查状态、导出、交给开发不带。工具返回 `ok: false` 时，把 `error` 告诉人并停下。有 `pendingAssumptions` 时向人要放行理由，再带 `confirm_note` 重发。有 `machineCheck` 时把失败项给人，不要改文档。

## 装完确认

人问「装好了没 / 怎么验证」时：让人新开一轮对话。刚装上的 skill，当前这轮看不见。

新对话里输入 `/`，菜单里应有 `sdlc-platform`，旁边是说明。选中后不写子命令就发送。

- 装好了：列出上面的子命令，问要做哪一步。不要自己写需求文档。
- 菜单里没有这一项：skill 没被认到。让人核对 `~/.cursor/skills/sdlc-platform/SKILL.md`（Claude Code 是 `~/.claude/skills/sdlc-platform/SKILL.md`）后新开对话。
- 人说没有这些工具：MCP 没接上，不是 skill 没装。让人核对 `mcp.json` 后新开对话。

## 新建迭代

入口是 `/sdlc-platform new`。缺迭代名、需求名、来源就分开问，缺哪样问哪样。三样齐了立刻 `import_requirement`，并复述这三样。需求名不要照抄迭代名。这和 `step` 为 `new` 是同一条。导入成功后只问要不要 `/sdlc-platform quality`，不要连着质检、采纳或发布。这个迭代名已经有卡：不要再建，改按那张卡的 `step` 继续。

## 进入哪一步

先看子命令或中文命令（命令速查）。点了就做那一步。没点名，但给了迭代名，就先 `get_iteration_status`。两样都没有，先列出命令，不要只问迭代名。

| `step` | 做什么 |
|---|---|
| `new` | 按新建。缺什么单独问什么：迭代名、需求名、来源（飞书链接或正文）。三样都在就立刻导入，并复述这三样。需求名不要照抄迭代名 |
| `importing` | 见下方「等导入」 |
| `import_failed` | 立刻停下，转述 `message` |
| `quality_ready` | 告诉人原文已在，问要不要 `quality`。不要自己开跑 |
| `quality_running` / `synthesize_running` | 告诉人还在跑。不要在对话里等。让人去平台看，或稍后再发 `/sdlc-platform status` |
| `adopt` | 把 `qualityDraftMarkdown` 给人看。人说「采纳质检」或发 `adopt` 才调用 `adopt_quality_draft` |
| `clarify` | 只展示 `nextQuestion` 这一题，然后等人。推荐项只标注「推荐」，不要替人选、不要替人打字 |
| `synthesize_ready` | 告诉人澄清已全部处置，问要不要 `synthesize` |
| `publish` | 把 `standardDraftMarkdown` 原样给人核对。人说「发布标准文档」或发 `publish` 才调用 `publish_standard`。不要改这篇草稿 |
| `published` | 告诉人已发布，可以 `export` 或 `handoff` |
| `changed` | 只提示，停下 |

人发的是 `new`，但这张卡其实已经在：改走上表，不要再建一张。

## 等导入

`import_requirement` 返回后开始计时，反复调用 `get_iteration_status`，累计不超过 30 秒。

- `step` 离开 `importing` 和 `import_failed`，并且原文块已经在（`quality_ready` 或更后）：成功。复述迭代名、需求名、来源，然后问要不要 `quality`。不要调用 `start_quality_check`。
- `import_failed`，或当前任务已是失败/取消：立刻停下，转述原因。
- 满 30 秒仍是 `importing`：停下。告诉人下次用同一个迭代名发 `/sdlc-platform status`。

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

| 命令 | 调用 |
|---|---|
| `/sdlc-platform import` | `import_requirement`，然后按「等导入」 |
| `/sdlc-platform quality` | `start_quality_check` |
| `/sdlc-platform adopt` | `adopt_quality_draft` |
| `/sdlc-platform clarify` | `submit_clarification` |
| `/sdlc-platform synthesize` | `start_standard_doc` |
| `/sdlc-platform publish` | `publish_standard` |
| `/sdlc-platform export` | `export_standard` |
| `/sdlc-platform handoff` | `handoff_to_developer`，然后按上面写文件 |
| `/sdlc-platform status` | 只调用 `get_iteration_status` |
| `/sdlc-platform new` | 按「新建迭代」 |

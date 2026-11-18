---
name: sdlc-platform
description: "在产物平台上，把原始需求变成标准需求文档。新建并导入原文、开始质检、采纳质检草稿、逐题澄清、合成并发布标准文档、导出定稿、交给开发。平台是定稿出处。不自己写标准文档，不替人采纳、答题或发布。用法：/sdlc-platform new|status|import|quality|adopt|clarify|synthesize|publish|export|handoff [迭代名]。不带子命令时先列出命令，再问要做哪一步。也响应：导入需求、开始质检、采纳质检、澄清这题、生成标准文档、发布标准文档、导出定稿、交给开发、到哪了。"
---

# 平台首发链路（sdlc-platform）

人在对话里输入 `/sdlc-platform`，再跟子命令。正式数据在产物平台。本 skill 只调用两个 MCP，不自己做质检、不自己写标准文档、不调用 `sdlc-sync`。

设计、用例、门禁、变更重走不在这一版。卡片 `step` 为 `changed` 时，说「对人怎么说」里「changed」那一句，然后停下。点名了步骤也一样。

## 用法

菜单里这一项是 `/sdlc-platform`，旁边的说明来自上面的 description。MCP 工具不是给人点的命令，由本 skill 按子命令去调。

| 子命令 | 等同 | 做什么 |
|---|---|---|
| `new [迭代名]` | 新建迭代 | 整条消息只有 `new` 时，先说明要一次给齐四项，再给可复制的多行代码块。禁止先问迭代名，禁止把四项并成一行。已写了迭代名还缺项就缺哪样问哪样。四样齐了再导入 |
| `status [迭代名]` | 到哪了 | 只查状态 |
| `import [迭代名]` | 导入需求 | 导入并等原文落库 |
| `quality [迭代名]` | 开始质检 | 触发质检，不等草稿 |
| `adopt [迭代名]` | 采纳质检 | 采纳平台上的质检草稿 |
| `clarify [迭代名]` | 澄清这题 | 处置当前一题 |
| `synthesize [迭代名]` | 生成标准文档 | 发起平台合成，不等草稿 |
| `publish [迭代名]` | 发布标准文档 | 发布平台上已有的草稿 |
| `export [迭代名]` | 导出定稿 | 把已发布 Markdown 回到对话 |
| `handoff [迭代名]` | 交给开发 | 把定稿写到用户主目录，给出平台链接和开工句 |

没写子命令，也没给迭代名：把这张表给人，并说「对人怎么说」里「没写子命令」那一句。不要一上来只问迭代名。

只给了迭代名、没有子命令：先 `get_iteration_status`，按卡片状态继续。对人只说「对人怎么说」里对应的那一句。

人的整条消息就是 `/sdlc-platform new`、后面没有迭代名：不要问迭代名。先说「对人怎么说」里「new 且没给迭代名」那一句，再按「新建迭代」给可复制的多行代码块。`new` 后面已经写了迭代名、但还缺项目名称、需求名或来源：只问缺的那一项，用「对人怎么说」里的口语。其他子命令缺迭代名时，只说「缺迭代名」那一句。状态里已有 `projectName` 就不要再问。中文命令和子命令同等。

## 对人怎么说

对人说话像客服：用「您」，短句，先说现在到哪了，再说可以做什么。不训人。下面表里的句子照着用，花括号换成这次的内容，其余不要改，也不要再补一句内部状态。

这些只给代理看，不要念给用户：任务编号、`taskId`、`currentTask`、`running`、`queued`、`done`、`failed`、`cancelled`、`step`、`ok`，以及平台 `message` 的原文。查进度时不说卡号。卡号和版本只在导出定稿、交给开发时说。

平台 `message` 用来判断步骤，不原样念。失败时把原因说成白话；原因本身已是一句中文时，整理后告诉人，不要带字段名。

| 场合 | 对人说 |
|---|---|
| 没写子命令 | 您想做哪一步？从下面选一个发我就行。需要迭代名的，写在命令后面。 |
| new 且没给迭代名 | 新建迭代需要一次给齐迭代名、项目名称、需求名、来源。来源可以填飞书链接，也可以直接把需求正文贴过来。请把下面代码块改成这次的内容，一次发回来就行。需求名不要和迭代名写成同一个。 |
| 缺迭代名 | 请把迭代名发我，例如 v1.0-登录。 |
| 缺项目名称、需求名或来源 | 只问缺的那一项。例如：还缺来源，飞书链接或需求正文都可以。 |
| 导入成功 | 原文已经到了。迭代名是{迭代名}，项目是{项目名称}，需求是{需求名}，来源是{来源}。需要的话，我可以帮您开始质检。 |
| importing 满 30 秒 | 原文还在导入，大概还要 10 分钟，请您耐心等一下。稍后可以用同一个迭代名让我再看一下，也可以直接到产物平台上看。 |
| import_failed | 原文没有导入成功。{白话原因} 您看是改来源后再试，还是先到产物平台上看一下。 |
| quality_ready | 原文已经到了。需要的话，我可以帮您开始质检。 |
| quality 已发起 | 质检已经开始了，结果还要等一会儿。您可以过一会儿再让我看一下进度，也可以先到产物平台上看。 |
| quality_running | 质检还在进行，结果还没出来。您可以过一会儿再让我看一下进度，也可以先到产物平台上看。 |
| adopt | 质检结果出来了，请看下面这篇文档。确认要采纳的话，跟我说「采纳质检」。 |
| synthesize_ready | 澄清都处理完了。需要的话，我可以帮您生成标准文档。 |
| synthesize 已发起，或 synthesize_running | 标准文档正在生成，稿子还没出来。可以过一会儿再让我看一下进度，也可以先到产物平台上看。 |
| publish | 标准文档草稿好了，请核对下面这篇。确认要发布的话，跟我说「发布标准文档」。 |
| published | 标准文档已经发布。您可以让我导出定稿，也可以交给开发。 |
| changed | 这张需求已经在变更流程里，我这边先不继续往下走。请到产物平台上处理。 |
| 工具返回 ok: false | 这一步没有完成。{白话原因} |

## 前置

两个 MCP 都要连上。平台地址是环境变量 `SDLC_PLATFORM_URL`。

| MCP | 路径 | 工具 |
|---|---|---|
| 输入 `sdlc-in` | `/mcp/in` | `get_iteration_status`、`import_requirement`、`start_quality_check`、`adopt_quality_draft`、`submit_clarification`、`start_standard_doc`、`publish_standard` |
| 输出 `sdlc-out` | `/mcp/out` | `export_standard`、`handoff_to_developer` |

平台开了写保护时，输入 MCP 要带同一个 `X-Token`。查状态、导出、交给开发不带。工具返回 `ok: false` 时，用「对人怎么说」里那一句告诉人并停下，不要贴 `error` 字段名。有 `pendingAssumptions` 时向人要一句放行理由，再带 `confirm_note` 重发。有 `machineCheck` 时把失败项改成白话给人，不要改文档。

## 装完确认

人问「装好了没 / 怎么验证」时：让人新开一轮对话。刚装上的 skill，当前这轮看不见。

新对话里输入 `/`，菜单里应有 `sdlc-platform`，旁边是说明。选中后不写子命令就发送。

- 装好了：列出上面的子命令，问要做哪一步。不要自己写需求文档。
- 菜单里没有这一项：skill 没被认到。让人核对 `~/.cursor/skills/sdlc-platform/SKILL.md`（Claude Code 是 `~/.claude/skills/sdlc-platform/SKILL.md`）后新开对话。
- 人说没有这些工具：MCP 没接上，不是 skill 没装。让人核对 `mcp.json` 后新开对话。

## 新建迭代

入口是 `/sdlc-platform new`。人的整条消息就是这一句、后面没有迭代名：不要调用工具，也不要先问任何一项。禁止先说「先给我迭代名」或「等迭代名到了再问」。回复分成两段，顺序不能反。

先写「对人怎么说」里「new 且没给迭代名」那一句，一个字不要改。

然后另起一个 Markdown 代码块，用三个反引号围住，聊天里才会出现复制按钮。块里只有下面这五行，每项单独一行。不要并成一行，不要改成普通段落，说明不要写进代码块：

```
/sdlc-platform new
迭代名：v1.0-登录
项目名称：某某项目
需求名：登录页改版
来源：https://example.feishu.cn/wiki/……
```

已经给了其中几样、还缺的：只问缺的那一项。四样齐了立刻 `import_requirement`，`project_name` 传项目名称。导入成功后说「导入成功」那一句，把四项填进去，不要连着质检、采纳或发布。状态里 `projectName` 已有就沿用这个值，不要再问。项目名称为空或迭代还不存在才问。这和 `step` 为 `new` 是同一条。这个迭代名已经有卡：不要再建，改按那张卡的 `step` 继续。

## 进入哪一步

先看子命令或中文命令（命令速查）。点了就做那一步。没点名，但给了迭代名，就先 `get_iteration_status`。两样都没有，先列出命令，并说「没写子命令」那一句。

| `step` | 做什么 |
|---|---|
| `new` | 按新建。整条消息只有 `new`：先说「new 且没给迭代名」那一句，再给「新建迭代」里的多行代码块。不要先问迭代名，不要把四项并成一行。`new` 后已经写了迭代名、还缺别的：只问缺的那一项。`projectName` 已有则沿用。四样都在就立刻导入，成功后说「导入成功」那一句。需求名不要照抄迭代名 |
| `importing` | 见下方「等导入」 |
| `import_failed` | 停下。说「import_failed」那一句，不要原样念 `message` |
| `quality_ready` | 说「quality_ready」那一句。不要自己开跑 |
| `quality_running` / `synthesize_running` | 说表里对应那一句。不要在对话里等，不要念任务号或英文状态 |
| `adopt` | 先说「adopt」那一句，再把 `qualityDraftMarkdown` 给人看。人说「采纳质检」或发 `adopt` 才调用 `adopt_quality_draft` |
| `clarify` | 只展示 `nextQuestion` 这一题，然后等人。推荐项只标注「推荐」，不要替人选、不要替人打字 |
| `synthesize_ready` | 说「synthesize_ready」那一句 |
| `publish` | 先说「publish」那一句，再把 `standardDraftMarkdown` 原样给人核对。人说「发布标准文档」或发 `publish` 才调用 `publish_standard`。不要改这篇草稿 |
| `published` | 说「published」那一句 |
| `changed` | 说「changed」那一句，然后停下 |

人发的是 `new`，但这张卡其实已经在：改走上表，不要再建一张。

## 等导入

`import_requirement` 返回后开始计时，反复调用 `get_iteration_status`，累计不超过 30 秒。

- `step` 离开 `importing` 和 `import_failed`，并且原文块已经在（`quality_ready` 或更后）：成功。说「导入成功」那一句，把四项填进去。不要调用 `start_quality_check`。
- `import_failed`，或当前任务已是失败/取消：停下，说「import_failed」那一句。
- 满 30 秒仍是 `importing`：对话里不再等。说「importing 满 30 秒」那两句。不要说「这一轮已等够」「先停在这里」。

质检和标准文档合成发起后都不要等。发起成功后分别说「quality 已发起」或「synthesize 已发起」那一句。不要复述 `taskId`、`taskStatus`。

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

调用 `handoff_to_developer`。`ok: false` 时不要写任何文件。成功后写到**用户主目录**，不要写进当前 git 仓库。路径用工具返回的，前面加上 `~/`，不要改名：

1. 把 `markdown` 写到 `~/` + `markdownPath`。目录没有就建。同一天的同名文件覆盖。
2. `.platform` 写到 `~/` + `platformPath`。`platformWrite` = `keep-if-same-req`：文件已在，且 JSON 里的 `reqId` 等于返回的 `requirementId`，则一个字都不要改（里面可能有拉取凭据）。文件没有、读不出 JSON、或 `reqId` 是另一张卡，则把 `platformJson` 原样写入。

写完后按这个顺序交给人。`copyForDeveloper` 和 `starter` 都不要改写：

1. `docUrl`。这是产物平台上打开标准需求文档的链接。工具没返回 `docUrl` 时，用 `http://10.30.6.41:5177/reqs/` 接上 `requirementId`，再接 `?tab=std`。
2. 本地定稿的打开链接。Markdown 链接，文字是「打开本地定稿」，地址是刚写好的绝对路径的 `file://` URL。空格和中文要百分号编码。不要只写 `~/` 开头的路径。
3. `copyForDeveloper`。与平台「复制给开发」同一段四节文本，原样贴在本地链接和开工句之间。工具没返回这个字段时，按同一模板现拼，平台地址用 `http://10.30.6.41:5177`。人在本机页面上点按钮时，地址栏是什么就写成什么。
4. `starter` 原句。

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
| `/sdlc-platform handoff` | `handoff_to_developer`，写到用户主目录，并给出平台链接和本地定稿链接 |
| `/sdlc-platform status` | 只调用 `get_iteration_status` |
| `/sdlc-platform new` | 按「新建迭代」 |

对人说的话只使用「对人怎么说」。不要把工具返回的 `status`、`taskId`、`message` 念出来。

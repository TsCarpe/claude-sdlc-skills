# 原文预处理与块级锚点

> SKILL.md「输入读取 · 原文预处理」条目的展开。文中 `scripts/` 均指本 skill（sdlc-intent）根目录下的 scripts/。
> 上游：正文 markdown 与评论 JSON 已读取；下游：sdlc-sync 推送（payload 的 doc/anchor 字段见 sdlc-sync 的 payload 契约，本文不展开）。

## 目录

- [1. 何时运行](#1-何时运行)
- [2. 输入准备：XML 拉取与文件提取](#2-输入准备xml-拉取与文件提取)
- [3. 运行解析器（parse_doc.py）](#3-运行解析器parse_docpy)
- [4. doc.json 块模型](#4-docjson-块模型)
- [5. 条款级出处约定（list_clauses.py）](#5-条款级出处约定list_clausespy)
- [6. 推送前锚点附加（resolve_anchors.py）](#6-推送前锚点附加resolve_anchorspy)
- [7. 失败回退与边界](#7-失败回退与边界)

## 1. 何时运行

- **仅飞书链接输入**（feishu.cn / doubao.com 的 /docx/、/wiki/）。本地 markdown/text 输入不走本管线（见 §7）。
- 时机：**正文 markdown 与评论 JSON 均读取完成后，执行一次**。体检阶段、后续推送均不重复拉取/重跑（复用已有 doc.json）；原文版本更新需重梳理时，随重梳理重跑一次。
- 产出落盘：`sdlc/<需求名>/intake/doc-<YYYYMMDD>.json` 与同级 `media/` 目录——这是正式产物；中间文件（完整 fetch JSON、content.xml、refmap.json）按 SKILL.md 原始内容留存口径放 `/tmp`。

## 2. 输入准备：XML 拉取与文件提取

1. 拉取块级结构（`--detail with-ids` = 每元素自带飞书原生块 ID，即引用锚点）：

   ```bash
   lark-cli docs +fetch --doc "<URL>" --doc-format xml --detail with-ids > /tmp/fetch.json
   ```

2. 从响应提取两个输入文件（字段名以 fetch 实际输出为准）：

   ```bash
   jq -r '.data.document.content' /tmp/fetch.json > /tmp/content.xml
   jq '.data.document.reference_map.comments' /tmp/fetch.json > /tmp/refmap.json
   ```

   refmap 传完整的 `.reference_map` 对象也可以，解析器两种都收（`raw.get("comments", raw)`）。

注意事项（源自 lark-cli 文档行为）：
- comments 组可能含保留键 `tips`（评论因数量上限被截断的提示）——解析器会自动忽略非 `cN` 键，无需预处理。
- **fetch 返回的评论可能被截断**；完整评论以已拉取的 list-comments JSON 为准（§6 的 `--comments` 参数即用它）。

## 3. 运行解析器（parse_doc.py）

```bash
python3 scripts/parse_doc.py --xml /tmp/content.xml --refmap /tmp/refmap.json \
  --out sdlc/<需求名>/intake/doc-<YYYYMMDD>.json \
  --media-dir sdlc/<需求名>/intake/media --download --url "<URL>"
```

| 参数 | 说明 |
|---|---|
| `--xml` / `--md` | DocxXML 内容文件 / 纯 markdown 回退模式（二选一） |
| `--refmap` | reference_map.comments JSON 文件（无评论可省略） |
| `--out` / `--media-dir` | doc.json 与媒体目录落盘位置 |
| `--download` | 调 lark-cli 下载媒体（图片/附件/画板缩略图）；不加则媒体条目停留 pending |
| `--url` / `--document-id` / `--revision-id` | 写入 doc.json source 字段，供溯源 |

- `--md` 回退模式合成 `x-` 前缀 ID（无原生锚点、平台不可直达），仅调试/补位用，正常飞书输入不走；产物 `generator` 标注 `markdown-fallback`，并在 stderr 打警告——该模式下 list-item 的 `ordinal`=marker、`parent`=None，resolve_anchors 条款级解析与 list_clauses 全量列表不可用。
- 控制台输出四行怎么读：`blocks=` 块数与类型分布；`media=… ok=…` 媒体下载结果；`conservation ok … textSha=… mediaTokens=N` 守恒自检结果（`--md` 模式为 `conservation fallback`）；`native-anchors=N/M` 原生块 ID 占比——合成 `x-` ID 通常全部来自 table-row（DocxXML 的行元素不带 id，属格式现实而非拉取错误；0.5 内容格段落子块用 p 原生 ID，占比会随层级还原上升）；若 list-item/paragraph 也大量合成，才说明 fetch 没带 `--detail with-ids`，应回查拉取命令。
- 媒体下载逐项容错：lark-cli 不可得（PATH / nvm / 默认安装路径均未命中）或单项失败时该条目 `status=failed` 带原因，不阻断其他条目与产物落盘（§7）。

### 内容守恒自检（conservation-v1；表头推断为排除项）

解析产物与原文的字符流对账，防解析静默丢失（历史上踩过：分栏 grid/column 内整棵块丢失、含图单元格夹注文本被弃、li 裸文本前缀丢失、图 caption 未读）。解析器组装 doc 后、写 `--out` 前自检，guard 写入 doc 顶层：

- **原文侧**：content.xml 树上全部 text 节点 + `cite` 展开（`@user-name`，无则 `@user-id`）+ `img@caption`（去尾换行；figure/source/whiteboard 无 caption 不收）+ **排除 thead 子树** + **排除无 thead 表中判定为表头的首行 tr 子树**（推断表头；判定与解析器同函数 `_table_header`，双侧确定性）。
- **产物侧**：全部块 `text`、`table-row` 的 `cells` 全列（内容格为空串，其文本由行内子块 `text` 承载——挪格不挪字符，指纹不变）、image 块 `caption`；`head`（每行重复挂载，收则多重计数）、`path`/`rowLabel`/`ordinal`/`marker`、media `name`/`alt` 不收；comment 块不收（见盲区）。
- **表头推断**：thead 优先；无 thead 时 tbody 行数 ≥2（扣除表头后仍剩 ≥1 数据行；单行表永不判表头）且首行每个 td/th 满足「非空、单段无换行、≤30 字、非纯数字、无 KEEP 块级嵌套」→ 判为表头：文本进各行 `head`、该行不成数据块（仍消耗一次合成 ID 计数，保数据行 `x-` 编号不漂）。首行为纯数字（如序号 1/2/3）不判——数据行常见此形态而表头格几乎不会。合并单元格（colspan/rowspan）维持既有展平口径，不做特殊处理。
- **归一化**：字符流剔除 `*`、`~` 与全部空白 → 剩余字符排序 → sha256（字符多重集合的规范指纹，顺序无关——解析器的内联顺序不可恢复，排序指纹对此免疫；也因此 cells↔子块 text 之间的文本挪移不影响指纹）。
- **guard 结构**：`{"algo":"conservation-v1","source":"xml","mediaTokens":[树上全部媒体 token 去重排序],"textSha":"<原文侧指纹>"}`；`--md` 回退模式 guard 为 `{"algo":"markdown-fallback"}`，不做文本守恒。
- **判定口径（agent 门与平台门分离）**：agent 侧（本脚本，exit 2 门）= 产物侧指纹 == guard.textSha，且 mediaTokens 与产物 `media[].token` 集合双向相等，**不查 media status**（离线免 `--download` 跑时 status 恒 pending）；平台落库终检（第二道门）另加 media status 全 ok、missingMedia=0 阻断与 guard 复算。
- **exit 2 处置**：产物**不落盘**（`--out` 不写）、不得回传平台；stderr 给出字符计数差/差集样本与 mediaTokens 差集（含 caption 提示），人工 diff content.xml 与既有 doc.json 定位后重跑。
- **守恒盲区（声明而非缺陷）**：评论内容（thread/quote 来自 refmap，content.xml 正文无对应，双侧恒 0）；字面 `*`/`~` 字符（归一化剔除，产物含纯 `*` 字面量会漏检）；thead/head 文本（双侧对称排除，含 0.5 推断表头行文本）；media name/alt。
- CI：`python3 skills/sdlc-intent/scripts/parse_doc.py --self-test`（脱敏 mini fixture：thead 与推断表头对称排除、grid 分栏图、混排 li、纯子列表 li、含图 cell、caption、cite 展开、内容格拆段/subheading/行内列表/空段丢弃/尾随空段标量逐项断言 + 变异必败 + 双仓固定向量）。

## 4. doc.json 块模型

顶层结构：`{generator, source:{url,documentId,revisionId}, blocks:[], media:[], guard:{…}}`（guard 见 §3 内容守恒自检；`--md` 回退模式为 `{"algo":"markdown-fallback"}`）。

| type | 关键字段 | 说明 |
|---|---|---|
| heading | level, text, path | 标题层级与路径 |
| paragraph | text, path, comments | 正文段；comments = comment-refs（如 "c3 c11"） |
| list-item | marker, ordinal, depth, text, parent | 条款；ordinal 即序数（如 1.a） |
| table-row | head, cells, rowLabel, parent | 表行；rowLabel 取首格文本，即「详述N」的 N 对应物；行块本身多为 `x-` 合成 ID（DocxXML 行元素不带 id），行级锚点常不可直达——条款级出处（list-item 原生 ID）才是直达路径。**0.5 表格语义**：`head` 可由无 thead 表推断（见 §3）；`cells` 与列数等长——标量格存文本，内容格存空串 `""`（多段落/含列表图片的格，内容见行内子块） |
| image / attachment / whiteboard | media, name | 媒体块，media 指向 media[] 条目 id |
| comment | ref, anchorBlockId, quote, thread | 评论块；id = 飞书 comment-id |

- **行内子块（0.5，挂 table-row 下、parent=行块 id、紧随行块）**：内容格逐段发 `paragraph`（可选 `subheading: true` = 原文整段粗体，可选 `cell: <列下标 int>` = 所属列）；list-item/image 等保持原类型，同样带 `cell` 戳。列表一律挂行块（不挂段落——平台编辑面「行内子块紧随其行」拓扑约束），「PC端/H5端 段落后跟列表」的从属由前端按块序相邻做视觉挂靠。
- **锚点语义**：块 `id` = 飞书原生块 ID（唯一例外：无 ID 时合成 `x-NNNN`，平台不可直达）。payload 条目的 `anchor` 填此 ID，前端按 id 直达原文条款。行内段落子块用 p 元素原生 ID（直达）。
- media 条目：`{id: "m-<sha256[:12]>", token, kind, name, mime, file, bytes, sha256, status}`，status ∈ pending / ok / failed。

## 5. 条款级出处约定（list_clauses.py）

doc.json 存在时，梳理/体检的「出处」尽量写到条款级，两种写法：

- 「详述N·<小节名>」：如 `详述6·步骤一`（小节名取条款原文前段子串即可命中）
- 「详述N·<序数>」：如 `详述6·1.a`（序数即 list_clauses 输出的 ordinal）

写出处前先查条款树（三种用法）：

```bash
python3 scripts/list_clauses.py --doc <doc.json>                # 全部顶层分组的条款树
python3 scripts/list_clauses.py --doc <doc.json> --row 6        # 只列 详述6 行内条款
python3 scripts/list_clauses.py --doc <doc.json> --depth 2      # 限制层级
```

- 适用字段：digest 各表「出处」列（含 §6 流转边表）、体检「原文定位」(where)、payload 的 `fr_points[].source` / `features[].src` / `flows[].src` / `states[].src` / `audit.items[].where` / 澄清 `items[].ctx`。
- 定位不到条款级时回退章节名出处；**禁止编造条款号/序数**。
- 梳理/体检正文仍写人读出处（上述格式）；块 ID 不进人读文档，由 §6 脚本附加。

## 6. 推送前锚点附加（resolve_anchors.py）

```bash
python3 scripts/resolve_anchors.py --doc <doc.json> \
  [--comments <list-comments.json> | --refmap <refmap.json>] \
  --payload <payload.json> --out <payload-anchored.json>
```

- **`--comments` 优先**：传工作流已拉取的 list-comments JSON——评论全量、顺序即「评论区#N」的 N；`--refmap` 为回退（按 cN 自然序映射，且 fetch 评论可能截断）。
- 解析策略（确定性，按序尝试）：① 出处含「详述N」→ 定位表行，带「·小节名/序数」时精确到条款块；② 「评论区#N」→ 映射到第 N 条评论的 comment 块；③ quote「」摘引 ≥6 字子串匹配；④ 全部失败 → 不加 anchor（平台回退 needle 文本定位）。
- 产物 payload-anchored.json 直接作为 sdlc-sync push-artifacts 的请求体；控制台 `anchors: {…}` 给出六类命中数与 miss 数（含 flows/states），miss 偏高时复查出处写法。
- doc.media 的上传顺序与 `doc`/`anchor` 字段规范见 sdlc-sync 的 payload 契约（此处仅衔接说明）。

## 7. 失败回退与边界

- **退出码约定**：0 成功 / 1 媒体下载失败（产物照常落盘）/ 2 守恒自检失败（不落盘）/ 3 用法错误——argparse 默认 error 亦 exit 2、与守恒失败撞码（消费方按码路由会误分类），脚本以 `_ArgParser` 覆写 `error()` 分离；runner 与平台 prompts 的码表已同步补 exit 3。
- **解析器整体失败 → 不阻塞梳理/体检**：出处回退章节级，向用户说明 doc.json 未生成，流程照常继续。
- **媒体单项失败**：条目 `status=failed` 带原因，不阻断其他条目；失败清单如实告知用户（不逐项重试，同评论区口径）。存在 failed 条目时 parse_doc.py 以 exit 1 结束——产物照常落盘、stdout 统计照常输出。**回传纪律：exit 1 的产物含 failed status，不得回传平台（平台终检将拒），须排查（lark-cli 可得性 / token 有效性 / 网络）后整体重跑重传。**
- **守恒失败（exit 2）**：解析产物与原文内容不一致（分栏内块 / 含图单元格夹注 / li 前缀丢失，或产物被篡改）——产物**不落盘**（`--out` 未写）、不得回传平台，属阻断式失败；按 stderr 差集样本定位（高发区见 §3），修复后重跑。禁止绕过守恒门落盘。
- **无评论/无 refmap**：省略 `--refmap` 正常运行，doc.json 无 comment 块。
- **本地 markdown/text 输入**：不运行本管线（无 XML/refmap），出处按章节级约定写。

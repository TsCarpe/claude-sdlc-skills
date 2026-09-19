# 原文预处理与块级锚点（v1.2 管线）

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

1. 拉取块级结构（`--detail with-ids` = 每元素自带飞书原生块 ID，即 v1.2 引用锚点）：

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

- `--md` 回退模式合成 `x-` 前缀 ID（无原生锚点、平台不可直达），仅调试/补位用，正常飞书输入不走。
- 控制台输出三行怎么读：`blocks=` 块数与类型分布；`media=… ok=…` 媒体下载结果；`native-anchors=N/M` 原生块 ID 占比——合成 `x-` ID 通常全部来自 table-row（DocxXML 的行元素不带 id，属格式现实而非拉取错误）；若 list-item/paragraph 也大量合成，才说明 fetch 没带 `--detail with-ids`，应回查拉取命令。
- 媒体下载逐项容错：lark-cli 不在 PATH 或单项失败时该条目 `status=failed` 带原因，不阻断整体（§7）。

## 4. doc.json 块模型

顶层结构：`{generator, source:{url,documentId,revisionId}, blocks:[], media:[]}`。

| type | 关键字段 | 说明 |
|---|---|---|
| heading | level, text, path | 标题层级与路径 |
| paragraph | text, path, comments | 正文段；comments = comment-refs（如 "c3 c11"） |
| list-item | marker, ordinal, depth, text, parent | 条款；ordinal 即序数（如 1.a） |
| table-row | head, cells, rowLabel, parent | 表行；rowLabel 取首格文本，即「详述N」的 N 对应物；行块本身多为 `x-` 合成 ID（DocxXML 行元素不带 id），行级锚点常不可直达——条款级出处（list-item 原生 ID）才是直达路径 |
| image / attachment / whiteboard | media, name | 媒体块，media 指向 media[] 条目 id |
| comment | ref, anchorBlockId, quote, thread | 评论块；id = 飞书 comment-id |

- **锚点语义**：块 `id` = 飞书原生块 ID（唯一例外：无 ID 时合成 `x-NNNN`，平台不可直达）。payload 条目的 `anchor` 填此 ID，前端按 id 直达原文条款。
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

- 适用字段：digest 各表「出处」列、体检「原文定位」(where)、payload 的 `fr_points[].source` / `features[].src` / `audit.items[].where` / 澄清 `items[].ctx`。
- 定位不到条款级时回退章节名出处；**禁止编造条款号/序数**。
- 梳理/体检正文仍写人读出处（上述格式）；块 ID 不进人读文档，由 §6 脚本附加。

## 6. 推送前锚点附加（resolve_anchors.py）

```bash
python3 scripts/resolve_anchors.py --doc <doc.json> \
  [--comments <list-comments.json> | --refmap <refmap.json>] \
  --payload <payload.json> --out <payload-anchored.json>
```

- **`--comments` 优先**：传工作流已拉取的 list-comments JSON——评论全量、顺序即「评论区#N」的 N；`--refmap` 为回退（按 cN 自然序映射，且 fetch 评论可能截断）。
- 解析策略（确定性，按序尝试）：① 出处含「详述N」→ 定位表行，带「·小节名/序数」时精确到条款块；② 「评论区#N」→ 映射到第 N 条评论的 comment 块；③ quote「」摘引 ≥6 字子串匹配；④ 全部失败 → 不加 anchor（平台回退 needle 文本定位，行为同 v1.1）。
- 产物 payload-anchored.json 直接作为 sdlc-sync push-artifacts 的请求体；控制台 `anchors: {…}` 给出四类命中数与 miss 数，miss 偏高时复查出处写法。
- doc.media 的上传顺序与 `doc`/`anchor` 字段规范见 sdlc-sync 的 payload 契约（此处仅衔接说明）。

## 7. 失败回退与边界

- **解析器整体失败 → 不阻塞梳理/体检**：出处回退章节级，向用户说明 doc.json 未生成，流程照常继续。
- **媒体单项失败**：条目 `status=failed` 带原因，不阻断；失败清单如实告知用户（不重试，同评论区口径）。
- **无评论/无 refmap**：省略 `--refmap` 正常运行，doc.json 无 comment 块。
- **本地 markdown/text 输入**：不运行本管线（无 XML/refmap），出处按章节级约定写。

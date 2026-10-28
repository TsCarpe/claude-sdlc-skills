#!/usr/bin/env python3
"""parse_doc.py — 需求原文预处理：DocxXML/Markdown → 标准块模型 doc.json

格式无关的通用块模型（不绑定任何需求文档模板）：
  heading / paragraph / list-item / table-row / image / attachment / whiteboard / comment

设计要点：
  - 锚点 = 飞书原生块 ID（DocxXML 每个元素自带 id），重推稳定，无需自造 ID 体系
  - 结构切分纯确定性（html.parser），无 LLM 参与
  - 媒体（图片/附件/画板缩略图）经 lark-cli docs +media-download 落盘，mediaId=内容哈希
  - 评论：宿主块 comment-refs="cN" + reference_map.comments[cN].data 完整评论串 → comment 块
  - 内容守恒自检（conservation-v1）：解析产物与原文字符流对账，失败 exit 2 不落盘
  - 退出码约定：0 成功 / 1 媒体下载失败（产物照常落盘）/ 2 守恒自检失败（不落盘）/
    3 用法错误（argparse 默认 error 亦 exit 2、与守恒失败撞码，故子类覆写分离——见 _ArgParser；
    消费方 runner.mjs / prompts.py 的码表已同步补 exit 3）

用法：
  parse_doc.py --xml content.xml --refmap refmap.json --out doc.json \
               --media-dir media/ [--download] [--url <来源URL>] [--md fallback.md]
  parse_doc.py --self-test
"""
import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from html import unescape
from html.parser import HTMLParser

GENERATOR = "sdlc-intent/parse_doc.py 0.5"
VOID_TAGS = {"img", "source", "col", "br", "hr", "colgroup"}
# 单元格内由子块承载的结构（文本不进 cells，防双计）：list/图/附件/画板 + 分栏容器 + 嵌套表
# 块级子元素白名单（由子块承载，宿主 text 不收——防双计；表格单元格/列表项/标题共用）：
# 基础块级 + v4.1 新增承载 pre/blockquote/checkbox（code/quote/todo 的 lark-cli XML 形态）
# callout 入白名单：td 内高亮块的列表子树此前整棵消失（jiaoyan-background td>callout>ol
# 的 25 个 li，oracle 块计数暴露——守恒/黄金比对双绿盲区，两链路同解析器同丢）
KEEP_IN_TABLE_CELL = {"ol", "ul", "img", "figure", "whiteboard", "grid", "column", "table",
                      "pre", "blockquote", "checkbox", "callout"}


# ---------------------------------------------------------------- tree builder
class Node:
    __slots__ = ("tag", "attrs", "children", "text")

    def __init__(self, tag, attrs=None):
        self.tag = tag
        self.attrs = attrs or {}
        self.children = []
        self.text = ""


class TreeBuilder(HTMLParser):
    """宽容的标签树构建器（DocxXML 是转义良好的类 XML，此处按 HTML 规则解析即可）"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag == "br":
            self._newline()
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag == "br":
            self._newline()

    def _newline(self):
        # br 语义 = 裸文本流的换行。data 按 += 追加，\n 落在流位置天然保序；此前 br 夹在
        # 两段 data 之间时换行信息被 text 拼接吞掉——code 块换行/段中软换行失真的根因。
        # 消费面安全：inline_text 的 br 分支不再命中（br 无 text/children），其输出本就含 \n
        self.stack[-1].text += "\n"

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if data:
            self.stack[-1].text += data


def parse_tree(xml_text):
    builder = TreeBuilder()
    builder.feed(xml_text)
    return builder.root


# ---------------------------------------------------------------- inline text
def _cite_name(attrs):
    """cite 展开文本：@user-name（无则 @user-id）——inline_text/_collect/plain_text/守恒原文侧四处同款"""
    return f"@{attrs.get('user-name') or attrs.get('user-id') or ''}".strip()


def inline_text(node, skip_keep=False):
    """元素内联内容 → markdown 风格文本（cite→@用户，b→**，del→~~，br→换行）。
    skip_keep=True 时跳过 KEEP 块级子元素子树（由子块承载，宿主 text 防双计）"""
    out = []

    def walk(n):
        if n.text:
            out.append(n.text)
        for c in n.children:
            if skip_keep and c.tag in KEEP_IN_TABLE_CELL:
                continue
            if c.tag == "cite":
                out.append(_cite_name(c.attrs))
            elif c.tag == "b":
                inner = _collect(c)
                out.append(f"**{inner}**" if inner.strip() else inner)
            elif c.tag == "del":
                inner = _collect(c)
                out.append(f"~~{inner}~~" if inner.strip() else inner)
            elif c.tag == "br":
                out.append("\n")
            else:
                walk(c)

    walk(node)
    return re.sub(r"[ \t]+", " ", "".join(out)).strip()


def _collect(node):
    buf = [node.text]
    for c in node.children:
        if c.tag == "cite":
            buf.append(_cite_name(c.attrs))
        else:
            buf.append(_collect(c))
    return "".join(buf)


def plain_text(node):
    buf = [node.text]
    for c in node.children:
        if c.tag == "cite":
            buf.append(_cite_name(c.attrs))
        else:
            buf.append(plain_text(c))
    return re.sub(r"\s+", " ", "".join(buf)).strip()


# ---------------------------------------------------------------- conservation (v1)
# 守恒契约（双仓共享，平台侧落库终检复算同口径）：
#   归一化 = 字符流剔除 * ~ 与全部空白 → 排序 → sha256（字符多重集合的规范指纹，顺序无关）
#   原文侧 = 树上全部 text 节点 + cite 展开（_cite_name 同款）+ img@caption（strip；figure/source/
#            whiteboard 无 caption 不收）+ 排除 thead 子树与无 thead 表的推断表头行
#            （_table_header 判定，与产物侧进 head 不收对称）
#   产物侧 = 全部块 text、cells 全列、image 块 caption；comment 块（来自 refmap，原文无正文）与
#            table-row 的 head（每行重复挂载，收则多重计数）不收；path/rowLabel/ordinal/marker/
#            media name/alt 不收
#   agent 门 = textSha 相等 + mediaTokens 与产物 media[].token 双向相等；不查 media status
#   （离线免 --download 跑时 status 恒 pending）；media status 全 ok 由平台落库终检把关
#   守恒盲区（双侧恒 0 或对称排除，声明而非缺陷）：评论内容（thread/quote 来自 refmap）、
#   字面 * ~ 字符、thead/head 文本（含推断表头行）、media name/alt
CONSERVATION_ALGO = "conservation-v1"


# ---- table header inference（parse_table 与 source_text_stream 双侧共用，保证守恒对称）
def _has_keep_descendant(node):
    """子树内是否含 KEEP 块级后代（ol/ul/img/figure/whiteboard/grid/column/嵌套 table）"""
    for c in node.children:
        if c.tag in KEEP_IN_TABLE_CELL or _has_keep_descendant(c):
            return True
    return False


def _cell_is_header_like(td):
    """表头格特征（纯结构驱动，不过拟合模板）：plain_text 非空、单一文本段（无 \\n，即
    cell_direct_text 不分段）、≤30 字、非纯数字（数据行常见 1/2/3 序号）、子树无 KEEP 后代"""
    txt = plain_text(td)
    if not txt or len(txt) > 30 or re.fullmatch(r"\d+", txt):
        return False
    if "\n" in DocParser.cell_direct_text(td):
        return False
    return not _has_keep_descendant(td)


def _table_header(table):
    """表头推断：thead 有 tr → (head, None)（thead 子树由调用方按既有规则跳过）；
    无 thead 且 tbody 行数 ≥2（首行作表头后仍至少 1 数据行）、首行每个 td/th 都
    header-like → (首行文本列表, 首行 tr)；否则 ([], None)。
    colspan/rowspan 维持既有行为：无视（doc-pipeline.md 声明不处理）"""
    thead = next((c for c in table.children if c.tag == "thead"), None)
    if thead is not None:
        tr = next((c for c in thead.children if c.tag == "tr"), None)
        if tr is not None:
            return [plain_text(th) for th in tr.children if th.tag in ("th", "td")], None
    body = next((c for c in table.children if c.tag == "tbody"), table)
    rows = [c for c in body.children if c.tag == "tr"]
    if len(rows) >= 2:
        first = [c for c in rows[0].children if c.tag in ("td", "th")]
        if first and all(_cell_is_header_like(td) for td in first):
            return [plain_text(td) for td in first], rows[0]
    return [], None


def source_text_stream(root):
    """原文侧字符流（见上方契约注释）"""
    buf = []

    def walk(n, skip=None):
        if n.tag == "thead":
            return  # 与产物侧不收 head 对称排除
        if n is skip:
            return  # 无 thead 表的推断表头行：与产物侧进 head 不收对称排除
        if n.tag == "table":
            # 推断表头行子树整体排除（_table_header 与 parse_table 同源，双侧确定性）
            _, header_tr = _table_header(n)
            if n.text:
                buf.append(n.text)
            for c in n.children:
                walk(c, header_tr)
            return
        if n.tag == "cite":
            buf.append(_cite_name(n.attrs))
            return  # 名字来自属性；cite 子树不收（与 inline_text 同款）
        if n.tag == "img":
            buf.append((n.attrs.get("caption") or "").strip())
            return  # img 无子内容；figure/source/whiteboard 无 caption 不收
        if n.text:
            buf.append(n.text)
        for c in n.children:
            walk(c, skip)

    walk(root)
    return "".join(buf)


def source_media_tokens(root):
    """原文侧媒体 token：img（src 优先，同 emit_image）、figure 内 source@token、whiteboard@token"""
    out = set()

    def walk(n):
        if n.tag == "img":
            t = n.attrs.get("src") or n.attrs.get("id") or ""
        elif n.tag in ("source", "whiteboard"):
            t = n.attrs.get("token") or ""
        else:
            t = ""
        if t:
            out.add(t)
        for c in n.children:
            walk(c)

    walk(root)
    return sorted(out)


def doc_text_stream(blocks):
    """产物侧字符流（见守恒契约注释；markdown 回退模式不适用）"""
    buf = []
    for b in blocks:
        if b.get("type") == "comment":
            continue
        if b.get("text"):
            buf.append(b["text"])
        buf.extend(b.get("cells") or [])
        if b.get("caption"):
            buf.append(b["caption"])
    return "".join(buf)


def conservation_sha(stream):
    """归一化指纹：剔除 * ~ 与全部空白 → 排序 → sha256"""
    return hashlib.sha256("".join(sorted(re.sub(r"[*~\s]", "", stream))).encode("utf-8")).hexdigest()


def verify_conservation(root, blocks, media_list):
    """agent 门（exit 2 的判定核心）。返回 (guard, problems)；problems 非空即失败"""
    tokens = source_media_tokens(root)
    src_stream = source_text_stream(root)
    guard = {"algo": CONSERVATION_ALGO, "source": "xml",
             "mediaTokens": tokens, "textSha": conservation_sha(src_stream)}
    problems = []
    doc_stream = doc_text_stream(blocks)
    if conservation_sha(doc_stream) != guard["textSha"]:
        src_chars = re.sub(r"[*~\s]", "", src_stream)
        doc_chars = re.sub(r"[*~\s]", "", doc_stream)
        missing = Counter(src_chars) - Counter(doc_chars)
        extra = Counter(doc_chars) - Counter(src_chars)
        problems.append(
            f"文本指纹不符：原文 {len(src_chars)} 字符 / 产物 {len(doc_chars)} 字符（归一化后）；"
            f"原文有产物无 {sum(missing.values())} 个（样本：{''.join(sorted(missing))[:32] or '—'}），"
            f"产物有原文无 {sum(extra.values())} 个（样本：{''.join(sorted(extra))[:32] or '—'}）")
    have = {m.get("token") for m in media_list if m.get("token")}
    want = set(tokens)
    if have != want:
        detail = []
        if want - have:
            detail.append(f"mediaTokens 缺失 {sorted(want - have)}（对应图/附件连同 caption 一并丢失）")
        if have - want:
            detail.append(f"产物多出 {sorted(have - want)}")
        problems.append("媒体对账不符：" + "；".join(detail))
    return guard, problems


# ---------------------------------------------------------------- parser core
def _ref_key(s):
    """评论引用键自然排序 key：c2 < c10（纯字典序在 N≥10 时错乱）"""
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


class DocParser:
    def __init__(self, refmap=None, url="", document_id="", revision_id=None):
        self.blocks = []
        self.media = {}          # token -> media entry
        self.refmap = refmap or {}
        self.headings = []       # [(level, text)]
        self.url, self.document_id, self.revision_id = url, document_id, revision_id
        self._syn = 0

    # ---- helpers
    def emit(self, block):
        self.blocks.append(block)
        return block

    def new_id(self):
        self._syn += 1
        return f"x-{self._syn:04d}"

    @staticmethod
    def block_id(node):
        bid = node.attrs.get("id") or ""
        return bid or None

    def heading_path(self):
        return " › ".join(t for _, t in self.headings)

    def path_of(self, *parts):
        segs = [self.headings[-1][1]] if self.headings else []
        segs += [p for p in parts if p]
        return " › ".join(segs)

    # ---- top-level walk
    def walk(self, node, parent_id=None, marker_chain=()):
        for c in node.children:
            self.dispatch(c, parent_id=parent_id, marker_chain=marker_chain)

    def heading_text(self, node):
        """标题直接内联文本：块级子元素（KEEP 白名单）子树跳过，文本不折进标题——
        b/del 内联标记走 plain_text 同口径（标题不收 **/~~，与旧行为一致）"""
        buf = [node.text or ""]
        for c in node.children:
            if c.tag in KEEP_IN_TABLE_CELL:
                continue
            if c.tag == "cite":
                buf.append(_cite_name(c.attrs))
            else:
                buf.append(plain_text(c))
        return re.sub(r"\s+", " ", "".join(buf)).strip()

    def dispatch(self, node, parent_id=None, marker_chain=()):
        tag = node.tag
        if tag in ("title",):
            self.emit({"id": self.block_id(node) or self.new_id(), "type": "title",
                       "text": plain_text(node), "path": plain_text(node)})
            return
        m = re.fullmatch(r"h([1-9])", tag)
        if m:
            level = int(m.group(1))
            text = self.heading_text(node)
            while self.headings and self.headings[-1][0] >= level:
                self.headings.pop()
            self.headings.append((level, text))
            hid = self.block_id(node) or self.new_id()
            self.emit({"id": hid, "type": "heading",
                       "level": level, "text": text, "path": self.heading_path()})
            # 标题内嵌块级子元素（grid 分栏/图/列表/表格）由子块承载——此前 heading 只发
            # 单块即 return：分栏内容被 plain_text 压扁进标题文本（结构丢），图连同 caption
            # 整体丢（守恒自检以媒体对账暴露：want-have 缺失）
            for c in node.children:
                if c.tag in KEEP_IN_TABLE_CELL:
                    self.dispatch(c, parent_id=hid)
            return
        if tag == "p":
            text = inline_text(node, skip_keep=True)
            pid = self.block_id(node)
            if text:
                self.emit({"id": pid or self.new_id(), "type": "paragraph",
                           "text": text, "path": self.path_of(),
                           "comments": node.attrs.get("comment-refs")})
                pid = None  # 原生 id 已被段落块占用
            for c in node.children:
                if c.tag == "source":  # 裸 source（无 figure 包裹的附件卡片）独自成附件块
                    self.emit_attachment(c, block_id=pid or self.new_id(), parent_id=parent_id)
                elif c.tag in KEEP_IN_TABLE_CELL:
                    # p 内嵌块级子元素（ul/ol/img/figure/whiteboard/grid/…）由子块承载——
                    # 此前 p 分支不递归，内嵌列表整列表丢块、文本被 inline_text 压扁进段落
                    # （守恒自检恒真盲区，oracle 块计数是唯一暴露面；实锤：主样本 p>ul×1）
                    self.dispatch(c, parent_id=pid or parent_id)
            return
        if tag in ("ol", "ul"):
            self.walk_list(node, parent_id=parent_id, marker_chain=marker_chain)
            return
        if tag == "table":
            self.parse_table(node, parent_id=parent_id)
            return
        if tag == "img":
            self.emit_image(node, parent_id=parent_id)
            return
        if tag == "figure":
            self.emit_figure(node, parent_id=parent_id)
            return
        if tag == "pre":
            # code(14)：lark-cli XML = <pre lang wrap><code>…<br/>…</code></pre>——此前无分支，
            # 兜底 walk 不收 code 标签 text，代码文本全丢（守恒文本指纹暴露）。
            # text 直接取 code.text（br 的 \n 已入流）：inline_text 的空白压缩会毁代码缩进
            code_el = next((c for c in node.children if c.tag == "code"), None)
            self.emit({"id": self.block_id(node) or self.new_id(), "type": "code",
                       "text": (code_el.text or "").strip("\n") if code_el is not None else "",
                       "lang": node.attrs.get("lang") or "",
                       "wrap": node.attrs.get("wrap") or "",
                       "path": self.path_of(), "parent": parent_id})
            return
        if tag == "blockquote":
            # quote(15)/quote_container(34)：lark-cli XML = <blockquote><p>…</p>…</blockquote>
            # ——此前容器兜底折成 paragraph（顶层）或吸进 li.text（li 内），块型还原丢失
            parts = [plain_text(c) for c in node.children if plain_text(c)]
            self.emit({"id": self.block_id(node) or self.new_id(), "type": "quote",
                       "text": "\n".join(parts), "path": self.path_of(), "parent": parent_id})
            return
        if tag == "checkbox":
            # todo(17)：lark-cli XML = <checkbox done="bool">文本</checkbox>（裸 text 节点）
            # ——此前未知标签兜底 walk 不收裸 text，待办文本全丢
            self.emit({"id": self.block_id(node) or self.new_id(), "type": "todo",
                       "text": (node.text or "").strip(),
                       "done": str(node.attrs.get("done") or "").lower() == "true",
                       "path": self.path_of(), "parent": parent_id})
            return
        if tag == "sheet":
            # sheet(30)：lark-cli XML = <sheet sheet-id token/>（空标签，单元格内容在独立电子表格，
            # 不随文档下载）——此前未知标签兜底 walk 无 emit，块静默丢失且守恒两侧都不含 sheet
            # 恒真抓不到（唯一能暴露的是 blocks API 块计数三方比对）。不登记 media（无下载语义）
            self.emit({"id": self.block_id(node) or self.new_id(), "type": "sheet",
                       "token": node.attrs.get("token") or "",
                       "sheetId": node.attrs.get("sheet-id") or "",
                       "path": self.path_of(), "parent": parent_id})
            return
        if tag == "whiteboard":
            token = node.attrs.get("token") or ""
            # mermaid 型画板（type=mermaid）源码存于标签 text——守恒原文侧无条件收 text 节点，
            # 产物侧此前 whiteboard 块无 text 字段 → 双侧口径不对称，指纹必差（实锤样本：AI活动
            # 纪要技术设计，3 张 mermaid 画板 457 字符）。text 字段双侧（parse_doc/平台 block.py
            # doc_text_stream）均无条件收，对称；普通画板 text 空，行为不变
            self.emit({"id": self.block_id(node) or self.new_id(), "type": "whiteboard",
                       "token": token, "media": self.register_whiteboard(token),
                       "text": (node.text or "").strip(), "path": self.path_of()})
            return
        if tag in ("grid", "column", "div", "span", "body", "#root", "colgroup",
                   "col", "thead", "tbody", "tr", "td", "th", "li", "source", "b", "del", "i",
                   "code", "br", "cite"):
            # 容器/表格内部细节由专门逻辑处理；此处兜底递归
            if tag in ("td", "th", "tr", "li", "thead", "tbody"):
                return  # 已由 parse_table / walk_list 处理
            self.walk(node, parent_id=parent_id, marker_chain=marker_chain)
            return
        # 未知标签：递归兜底
        self.walk(node, parent_id=parent_id, marker_chain=marker_chain)

    # ---- lists
    @staticmethod
    def li_inline_text(li):
        """li 内联文本 = li 直接裸文本 + 非 KEEP 块级子树的内联内容，无缝拼接（与 inline_text
        处理 p 的方式同构，保留 b→** / del→~~ / cite→@ / br→\\n 规则）——飞书 li 的「前缀：」
        常是裸文本、说明在 span 里，拼接才不断句；KEEP 块级子元素（含 blockquote/pre/checkbox）
        由子块承载，此处跳过防双计"""
        out = [li.text or ""]

        def walk(n):
            for c in n.children:
                if c.tag in KEEP_IN_TABLE_CELL:
                    continue
                if c.tag == "cite":
                    out.append(_cite_name(c.attrs))
                elif c.tag == "b":
                    inner = _collect(c)
                    out.append(f"**{inner}**" if inner.strip() else inner)
                elif c.tag == "del":
                    inner = _collect(c)
                    out.append(f"~~{inner}~~" if inner.strip() else inner)
                elif c.tag == "br":
                    out.append("\n")
                else:
                    if c.text:
                        out.append(c.text)
                    walk(c)

        walk(li)
        return re.sub(r"[ \t]+", " ", "".join(out)).strip()

    def walk_list(self, container, parent_id=None, marker_chain=()):
        n = 0
        for li in container.children:
            if li.tag != "li":
                continue
            n += 1
            marker = (li.attrs.get("seq-marker") or "").strip() or f"{n}."
            chain = marker_chain + (re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", marker) or str(n),)
            ordinal = ".".join(chain)
            bid = self.block_id(li) or self.new_id()
            # li 裸文本直接收（旧行为只看子元素，前缀整段丢）；纯子列表 li 的 text 为空，
            # 仍发块保锚点；子列表内容只由子项块承载，不折进父 text（防双计）
            text = self.li_inline_text(li)
            self.emit({"id": bid, "type": "list-item", "marker": marker, "ordinal": ordinal,
                       "depth": len(chain), "text": text, "path": self.path_of(ordinal),
                       "parent": parent_id,
                       "comments": li.attrs.get("comment-refs") or None})
            for sub in li.children:
                # img/列表/引用/代码/待办等块级子元素由子块承载（ol/ul 经 dispatch 走 walk_list）
                if sub.tag in KEEP_IN_TABLE_CELL:
                    self.dispatch(sub, parent_id=bid)

    # ---- tables
    @staticmethod
    def cell_direct_text(td):
        """单元格直接文本 = td 裸文本 + 非 KEEP 子元素文本（\\n 连接，恢复段落边界）。
        KEEP 白名单子元素（list/img/figure/whiteboard/grid/column/嵌套 table）由子块承载，
        文本不进 cells——与 parse_table 的子块提取口径互斥，防双计。
        删旧行为「cell 含图即弃全部直接文本」（图旁零散文本是正文而非夹注）"""
        parts = [td.text] if td.text and td.text.strip() else []
        for c in td.children:
            if c.tag in KEEP_IN_TABLE_CELL:
                continue
            t = inline_text(c)
            if t:
                parts.append(t)
        return "\n".join(parts).strip()

    @staticmethod
    def _cell_subblocks(td):
        """单元格内嵌块级子元素：grid/column 递归展平（容器不自身成块，列内 p/hN/table 走通用
        dispatch）；KEEP 白名单成员由子块承载；其余（p/内联）文本走 cell_direct_text，不发块。
        parse_table 不再逐格分发，仅被 _is_scalar_cell 复用（展平后有无 KEEP 子块）"""
        for c in td.children:
            if c.tag in ("grid", "column"):
                yield from DocParser._cell_subblocks(c)
            elif c.tag in KEEP_IN_TABLE_CELL:
                yield c

    @staticmethod
    def _cell_children_flat(td):
        """单元格直接子元素视图：grid/column 递归展平（容器自身透明，不算子元素）"""
        for c in td.children:
            if c.tag in ("grid", "column"):
                yield from DocParser._cell_children_flat(c)
            else:
                yield c

    @staticmethod
    def _keep_descendants(node):
        """子树内顶层 KEEP 成员（不钻入 KEEP 子树——dispatch 已处理其内部，防双发）"""
        for c in node.children:
            if c.tag in KEEP_IN_TABLE_CELL:
                yield c
            else:
                yield from DocParser._keep_descendants(c)

    @staticmethod
    def _whole_bold(p):
        """整段粗体：唯一子元素是单个 <b>、b 前后无裸文本（HTMLParser 把裸文本聚合进
        p.text，存在性可判）、b 文本非空 → 该段是小标题"""
        if len(p.children) != 1 or p.children[0].tag != "b":
            return False
        if (p.text or "").strip():
            return False
        return bool(plain_text(p.children[0]))

    @staticmethod
    def _is_scalar_cell(td):
        """标量格：展平 grid/column 后无 KEEP 子块、有效子元素 ≤1（有效 = 非 KEEP 且
        inline_text 非空；空 p/span 计 0，与空段丢弃同口径——飞书 cell 惯有尾随空段
        `<td><p>P0</p><p/></td>` 不误判内容格）、直接文本 ≤120 字。
        标量 → 文本进 cells；否则内容格（cells 置空串，子块树承载）"""
        if next(DocParser._cell_subblocks(td), None) is not None:
            return False
        effective = sum(1 for c in DocParser._cell_children_flat(td) if inline_text(c))
        if effective > 1:
            return False
        return len(DocParser.cell_direct_text(td)) <= 120

    def _emit_cell_paragraph(self, p, row_id):
        """单元格内段落：空文本且无 KEEP 后代 → 丢弃；空文本但带 KEEP 后代 → 只承载
        KEEP 成员；非空 → paragraph 子块（原生 id 直用，整段粗体标 subheading）"""
        text = inline_text(p)
        if not text:
            for k in self._keep_descendants(p):
                self.dispatch(k, parent_id=row_id)
            return
        block = {"id": self.block_id(p) or self.new_id(), "type": "paragraph",
                 "text": text, "path": self.path_of(), "parent": row_id,
                 "comments": p.attrs.get("comment-refs")}
        if self._whole_bold(p):
            block["subheading"] = True
        self.emit(block)

    def _emit_cell_tree(self, td, row_id):
        """内容格子块树（仅内容格调用，与 cells 置空互斥防双计）：裸文本/段落逐个成块、
        ol/ul 与 KEEP 成员挂行块（li.parent = 行块 id——平台「行内子块紧随其行」约束所限，
        从属还原交前端渲染层）、空段丢弃；grid/column 容器透明展平；其余非 KEEP 子元素
        （b/blockquote/div 等）折为 paragraph。cell 列下标戳由 parse_table 统一补"""
        if td.text and td.text.strip():
            self.emit({"id": self.new_id(), "type": "paragraph",
                       "text": td.text.strip(), "path": self.path_of(),
                       "parent": row_id, "comments": None})
        for c in td.children:
            if c.tag in ("grid", "column"):
                self._emit_cell_tree(c, row_id)
            elif c.tag == "p":
                self._emit_cell_paragraph(c, row_id)
            elif c.tag in ("ol", "ul"):
                self.walk_list(c, parent_id=row_id)
            elif c.tag in KEEP_IN_TABLE_CELL:
                self.dispatch(c, parent_id=row_id)
            else:
                t = inline_text(c)
                if t:
                    self.emit({"id": self.block_id(c) or self.new_id(),
                               "type": "paragraph", "text": t, "path": self.path_of(),
                               "parent": row_id, "comments": c.attrs.get("comment-refs")})

    def parse_table(self, table, parent_id=None):
        table_head, header_tr = _table_header(table)
        if header_tr is not None:
            # 推断表头行：占位消耗一次 ID 计数但不发块——数据行 x-NNNN 与旧版逐行编号一致
            self.block_id(header_tr) or self.new_id()
        body = next((c for c in table.children if c.tag == "tbody"), table)
        data_rows = [c for c in body.children if c.tag == "tr" and c is not header_tr]
        for idx, tr in enumerate(data_rows, 1):
            tds = [c for c in tr.children if c.tag in ("td", "th")]
            cells, content_cols = [], []
            row_label = ""
            for ci, td in enumerate(tds):
                if self._is_scalar_cell(td):
                    cells.append(self.cell_direct_text(td))
                else:
                    cells.append("")  # 内容格置空串（非 null）：文本由行内子块承载
                    content_cols.append((ci, td))
                if ci == 0 and not row_label:
                    first = re.sub(r"\s+", "", plain_text(td))
                    row_label = (first or f"#{idx}")[:24]
            row_bid = self.block_id(tr) or self.new_id()
            path = self.path_of(row_label)
            self.emit({"id": row_bid, "type": "table-row", "head": table_head,
                       "cells": cells, "rowLabel": row_label, "path": path,
                       "parent": parent_id,
                       "comments": tr.attrs.get("comment-refs") or None})
            # 内容格子块树挂行块（标量格文本已进 cells 不再发块——互斥防双计）；
            # 切片内新块补 cell 列下标戳（前端按列分组；旧数据无戳归 -1 组）
            for ci, td in content_cols:
                mark = len(self.blocks)
                self._emit_cell_tree(td, row_bid)
                for b in self.blocks[mark:]:
                    b.setdefault("cell", ci)

    # ---- media
    def emit_image(self, node, parent_id=None):
        token = node.attrs.get("src") or node.attrs.get("id") or ""
        bid = self.block_id(node) or self.new_id()
        caption = (node.attrs.get("caption") or "").strip()  # DocxXML caption 尾部常带 &#xA;
        media_id = self.register_media(token, name=node.attrs.get("name") or "image",
                                       mime=node.attrs.get("mime") or "", kind="media")
        self.emit({"id": bid, "type": "image", "media": media_id,
                   "name": node.attrs.get("name") or "", "alt": node.attrs.get("alt") or "",
                   "caption": caption,
                   "width": node.attrs.get("width"), "height": node.attrs.get("height"),
                   "path": self.path_of(), "parent": parent_id})

    def emit_figure(self, node, parent_id=None):
        src = next((c for c in node.children if c.tag == "source"), None)
        if src is None:
            return
        self.emit_attachment(src, block_id=self.block_id(node) or self.new_id(),
                             parent_id=parent_id)

    def emit_attachment(self, src, block_id, parent_id=None):
        """附件块（figure>source 与 p 内裸 source 共用；media 由 token 登记）"""
        token = src.attrs.get("token") or ""
        media_id = self.register_media(token, name=src.attrs.get("name") or "attachment",
                                       mime=src.attrs.get("mime") or "", kind="media")
        self.emit({"id": block_id, "type": "attachment", "media": media_id,
                   "name": src.attrs.get("name") or "",
                   "mime": src.attrs.get("mime") or "",
                   "bytes": int(src.attrs.get("size") or 0), "path": self.path_of(),
                   "parent": parent_id})

    def register_media(self, token, name, mime, kind):
        if not token:
            return None
        if token not in self.media:
            mid = "m-" + hashlib.sha256(token.encode()).hexdigest()[:12]
            self.media[token] = {"id": mid, "token": token, "kind": kind, "name": name,
                                 "mime": mime, "file": None, "bytes": 0, "sha256": None,
                                 "status": "pending"}
        return self.media[token]["id"]

    def register_whiteboard(self, token):
        if not token:
            return None
        if token not in self.media:
            mid = "m-" + hashlib.sha256(("wb:" + token).encode()).hexdigest()[:12]
            self.media[token] = {"id": mid, "token": token, "kind": "whiteboard",
                                 "name": "whiteboard", "mime": "image/jpeg", "file": None,
                                 "bytes": 0, "sha256": None, "status": "pending"}
        return self.media[token]["id"]

    # ---- comments
    def emit_comments(self):
        for ref in sorted((k for k in self.refmap if re.fullmatch(r"c\d+", k)), key=_ref_key):
            data = (self.refmap[ref] or {}).get("data") or ""
            if not data:
                continue
            root = parse_tree(data)
            cm = next((c for c in root.children if c.tag == "comment"), None)
            if cm is None:
                continue
            thread = []
            for m in cm.children:
                if m.tag == "msg":
                    thread.append({"user": m.attrs.get("user") or "", "text": inline_text(m)})
                elif m.tag == "quote":
                    pass
            quote = next((inline_text(m) for m in cm.children if m.tag == "quote"), "")
            reactions = []
            for m in cm.children:
                if m.tag == "reaction":
                    reactions.append({"key": m.attrs.get("key"), "users": m.attrs.get("users")})
            self.emit({"id": cm.attrs.get("comment-id") or self.new_id(), "type": "comment",
                       "ref": ref, "anchorBlockId": cm.attrs.get("block-id")
                       or cm.attrs.get("start-block-id") or "",
                       "quote": quote, "thread": thread, "reactions": reactions or None,
                       "path": "评论区"})

    # ---- markdown fallback mode
    def parse_markdown(self, md_text):
        lines = md_text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            m = re.match(r"^(#{1,9})\s+(.*)$", line)
            if m:
                level, text = len(m.group(1)), m.group(2).strip()
                while self.headings and self.headings[-1][0] >= level:
                    self.headings.pop()
                self.headings.append((level, text))
                self.emit({"id": self.new_id(), "type": "heading", "level": level,
                           "text": text, "path": self.heading_path()})
                i += 1
                continue
            if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|?$", lines[i + 1] or ""):
                head = [c.strip() for c in line.strip("|").split("|")]
                i += 2
                n = 0
                while i < len(lines) and lines[i].startswith("|"):
                    n += 1
                    cells = [c.strip() for c in lines[i].strip("|").split("|")]
                    row_label = (re.sub(r"\s+", "", cells[0]) if cells else "") or f"#{n}"
                    self.emit({"id": self.new_id(), "type": "table-row", "head": head,
                               "cells": cells, "rowLabel": row_label,
                               "path": self.path_of(row_label), "parent": None})
                    i += 1
                continue
            m = re.match(r"^(\s*)([-*+]|\d+[.、)])\s+(.*)$", line)
            if m:
                depth = len(m.group(1)) // 2 + 1
                marker = m.group(2).strip()
                text = m.group(3).strip()
                self.emit({"id": self.new_id(), "type": "list-item", "marker": marker,
                           "ordinal": marker, "depth": depth, "text": text,
                           "path": self.path_of(marker), "parent": None})
                i += 1
                continue
            mimg = re.match(r"^!\[[^\]]*\]\(([^)]+)\)", line.strip())
            if mimg:
                self.emit({"id": self.new_id(), "type": "image",
                           "media": self.register_media(mimg.group(1), "image", "", "media"),
                           "name": "", "alt": "", "caption": "",
                           "path": self.path_of(), "parent": None})
                i += 1
                continue
            if line.strip():
                self.emit({"id": self.new_id(), "type": "paragraph", "text": line.strip(),
                           "path": self.path_of(), "comments": None})
            i += 1


# ---------------------------------------------------------------- media download
def download_media(media_list, media_dir, manifest=None):
    """媒体回填三态：manifest 命中（本地文件/skipped 豁免）优先，miss 项才走 lark-cli——
    纯 Python 飞书链路（platform_sdlc media.py 产 manifest）无 lark-cli 依赖；miss 且无
    lark-cli 时显式失败（fail-closed 不静默降级）。lark-cli 路径保留（过渡期 runner 兼容）。"""
    os.makedirs(media_dir, exist_ok=True)
    manifest = manifest or {}
    pending = []
    for m in media_list:
        ent = manifest.get(m["token"])
        if ent is None:
            pending.append(m)  # manifest 未认领 → lark-cli 原逻辑
            continue
        skipped = ent.get("skipped")
        if skipped:
            m["status"] = f"skipped:{skipped}"  # 大附件豁免（size-exceeded），不阻断
            m["bytes"] = int(ent.get("bytes") or 0)
            continue
        p = ent.get("path")
        if p and os.path.isfile(p):
            data = open(p, "rb").read()
            m["bytes"] = len(data)
            m["sha256"] = ent.get("sha256") or hashlib.sha256(data).hexdigest()
            m["file"] = os.path.relpath(p, os.path.dirname(media_dir.rstrip("/")))
            m["status"] = "ok"
        else:
            m["status"] = "failed: manifest file missing"
    if not pending:
        return
    lark = _find_lark_cli()
    if not lark:
        toks = ", ".join(str(m.get("token"))[:14] for m in pending[:5])
        print(f"错误: manifest 不完整且未找到 lark-cli（未认领 {len(pending)} 项: {toks}…）"
              "——媒体回填失败", file=sys.stderr)
        for m in pending:
            m["status"] = "failed: manifest incomplete"
        return
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(lark) + os.pathsep + env.get("PATH", "")
    for m in pending:
        out = os.path.join(media_dir, m["id"])
        cmd = [lark, "docs", "+media-download", "--token", m["token"],
               "--output", out, "--overwrite"]
        if m["kind"] == "whiteboard":
            cmd += ["--type", "whiteboard"]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
            # lark-cli 会给 output 自动追加扩展名，且版本提示可能带非零退出码：glob 实际产物
            hits = [p for p in glob.glob(glob.escape(out) + ".*") if os.path.isfile(p)]
            if not hits and os.path.exists(out):
                hits = [out]
            if not hits:
                m["status"] = f"failed: {(r.stderr or r.stdout)[-160:]}"
                continue
            final = hits[0]
            data = open(final, "rb").read()
            m["bytes"] = len(data)
            m["sha256"] = hashlib.sha256(data).hexdigest()
            m["file"] = os.path.relpath(final, os.path.dirname(media_dir.rstrip("/")))
            m["status"] = "ok"
        except Exception as e:  # noqa: BLE001 —— 单个媒体失败不阻断整体
            m["status"] = f"failed: {e}"


# lark-cli 常见默认安装路径(npm 非 nvm 全局装 / Homebrew node 全局装的默认 bin 前缀)
LARK_CLI_DEFAULTS = ("/usr/local/bin/lark-cli", "/opt/homebrew/bin/lark-cli")


def _find_lark_cli():
    """解析顺序:① PATH(which) ② nvm glob ③ 常见默认安装路径;全 miss 返回 None。"""
    p = shutil.which("lark-cli")
    if p:
        return p
    for pat in (os.path.expanduser("~/.nvm/versions/node/*/bin/lark-cli"),):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    for p in LARK_CLI_DEFAULTS:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None


# ---------------------------------------------------------------- self-test
# 固定测试向量（双仓一致性锁：平台仓 tests/test_v4_import.py 用同输入同期望值各自断言）。
# 输入 blocks JSON 原文：
#   [{"type":"paragraph","text":"活动链接：必填"},
#    {"type":"list-item","text":"生效范围"},
#    {"type":"image","caption":"PC端原型图"}]
# 期望：产物侧归一化 = 三段 text/caption 拼接「活动链接：必填生效范围PC端原型图」剔除 * ~ 与
# 空白后排序 → sha256 = 61be48ea05d60cc30664afae48879306f5504495306cadaf48ec0d324c4716d9
FIXED_VECTOR_INPUT = ('[{"type":"paragraph","text":"活动链接：必填"},'
                      '{"type":"list-item","text":"生效范围"},'
                      '{"type":"image","caption":"PC端原型图"}]')
FIXED_VECTOR_SHA = "61be48ea05d60cc30664afae48879306f5504495306cadaf48ec0d324c4716d9"

# 脱敏 mini fixture（虚构内容；真实文档不入仓）。覆盖面 = 四项解析修复 + 表格升级 + 守恒对称口径：
# thead 表格（表头不进指纹、行文本进）/ grid 两 column 各含一图（图成块挂行块 + media + caption）/
# li 裸文本+span 混排（前缀不丢）/ li 内只有子列表（父 text 空、子项不双计）/ 含图 cell 正文保留 /
# caption 进块 / cite 展开（含 cite 子树不收）/
# 无 thead 表·表头命中（首行短文本进 head 不成块、占位计数保数据行 ID、原文侧对称排除）/
# 表头不命中四反例（单行表/首行长文本/首行含 ol/首行纯数字）/ 内容格拆段（cells 空串 + paragraph
# 子块带 cell 戳与原生 id）/ 整段粗体 subheading / 行内列表挂行块 / 空段丢弃 / 尾随空段标量格
_SELF_TEST_XML = """<?xml version="1.0" encoding="UTF-8"?>
<body>
<h1>需求标题</h1>
<p id="p1">正文段落<cite user-name="张三" user-id="u1">内部忽略</cite>结尾</p>
<ol>
<li id="li1">裸文本前缀<span>后续说明</span></li>
<li id="li2"><ul><li id="li2a">子项甲</li><li id="li2b">子项乙</li></ul></li>
<li id="li3"><b>加粗项</b></li>
</ol>
<table>
<thead><tr><th>列一</th><th>列二</th></tr></thead>
<tbody>
<tr id="tr1"><td><p>单元格A1</p><p>单元格A2</p></td><td>纯文本B1</td></tr>
<tr id="tr2"><td><p>含图单元格局部说明</p><img id="im1" name="i.png" caption="图一说明&#xA;" src="tok1"/></td><td><grid id="g1"><column id="c1"><img id="im2" name="j.png" caption="图二说明&#xA;" src="tok2"/></column><column id="c2"><img id="im3" name="k.png" caption="图三说明" src="tok3"/></column></grid></td></tr>
</tbody>
</table>
<table>
<tbody>
<tr><td>版本</td><td>日期</td></tr>
<tr><td><p><b>小标题</b></p><p>正文段一</p><p/><p>  </p><ol><li>行内列表项</li></ol></td><td><p>P0</p><p/></td></tr>
</tbody>
</table>
<table><tbody><tr id="b1"><td>单行表内容</td></tr></tbody></table>
<table><tbody>
<tr id="b2"><td>这一格的文本长度明显超过三十个字符的上限因此不符合表头格判定条件</td><td>次格</td></tr>
<tr id="b3"><td>d一</td><td>d二</td></tr>
</tbody></table>
<table><tbody>
<tr id="b4"><td>标题甲<ol><li id="bn1">嵌套列表项</li></ol></td><td>次格二</td></tr>
<tr id="b5"><td>数据一</td><td>数据二</td></tr>
</tbody></table>
<table><tbody>
<tr id="b6"><td>1</td><td>2</td></tr>
<tr id="b7"><td>aa</td><td>bb</td></tr>
</tbody></table>
</body>
"""


def self_test():
    import copy
    root = parse_tree(_SELF_TEST_XML)
    p = DocParser()
    p.walk(root)
    p.emit_comments()
    blocks = p.blocks
    by_id = {b["id"]: b for b in blocks}
    media_list = list(p.media.values())

    # ---- 修复行为逐项断言
    # cite 展开进产物；顺序上 cite 后置（HTMLParser 把 cite 前后 data 聚合进 p.text，
    # 内联顺序不可恢复）——守恒指纹按字符多重集合比对，对顺序免疫
    assert by_id["p1"]["text"] == "正文段落结尾@张三", by_id["p1"]["text"]
    assert by_id["li1"]["text"] == "裸文本前缀后续说明", by_id["li1"]["text"]  # li 裸文本前缀不丢
    li2 = by_id["li2"]
    assert li2["text"] == "" and li2["type"] == "list-item"  # 纯子列表：父 li 空块保锚点
    assert by_id["li2a"]["text"] == "子项甲" and by_id["li2a"]["parent"] == "li2"
    assert by_id["li2b"]["text"] == "子项乙" and by_id["li2b"]["parent"] == "li2"  # 不折进父块
    assert by_id["li3"]["text"] == "**加粗项**", by_id["li3"]["text"]  # b→** 规则保留

    # ---- 表格：thead 表（既有 case 按新语义改写）
    tr1, tr2 = by_id["tr1"], by_id["tr2"]
    assert tr1["head"] == ["列一", "列二"]  # thead 进 head（展示层），不进指纹
    assert tr1["cells"] == ["", "纯文本B1"], tr1["cells"]  # 多段格=内容格置空；裸文本格仍标量
    kids = [b for b in blocks if b.get("parent") == "tr1"]
    assert [b["text"] for b in kids] == ["单元格A1", "单元格A2"]  # 拆段：两段各成 paragraph 子块
    assert all(b["type"] == "paragraph" and b["cell"] == 0 for b in kids)
    assert kids[0]["id"] == "x-0002" and kids[1]["id"] == "x-0003"  # 无原生 id 的 p 用 new_id
    assert tr2["cells"] == ["", ""], tr2["cells"]  # 含图格与 grid 格均为内容格
    assert by_id["x-0004"]["text"] == "含图单元格局部说明"  # 含图 cell 文本不弃：成段落子块
    assert by_id["x-0004"]["cell"] == 0 and by_id["x-0004"]["parent"] == "tr2"
    assert by_id["im1"]["caption"] == "图一说明", by_id["im1"]["caption"]  # caption 进块去尾换行
    assert by_id["im2"]["caption"] == "图二说明" and by_id["im3"]["caption"] == "图三说明"
    assert by_id["im2"]["parent"] == "tr2" and by_id["im3"]["parent"] == "tr2"  # grid 内图挂行块
    assert by_id["im1"]["cell"] == 0 and by_id["im2"]["cell"] == 1 and by_id["im3"]["cell"] == 1
    assert {b["id"] for b in blocks if b["type"] == "image"} == {"im1", "im2", "im3"}
    assert set(p.media) == {"tok1", "tok2", "tok3"}  # grid 两图成为 media

    # ---- 表格：无 thead 表·表头命中（a）
    hdr = by_id["x-0006"]  # 推断表头行占位计数（x-0005）后首个数据行 = 与旧版逐行编号一致
    assert hdr["type"] == "table-row" and hdr["head"] == ["版本", "日期"], hdr["head"]
    assert hdr["cells"] == ["", "P0"], hdr["cells"]  # 内容格空串 + 尾随空段标量格（g）
    assert hdr["rowLabel"].startswith("小标题")
    # 表头行不成块：无 rowLabel 为「版本」的行块；表头文本不进原文侧指纹（与 head 不收对称）
    assert not [b for b in blocks if b["type"] == "table-row" and b["rowLabel"] == "版本"]
    assert "版本" not in re.sub(r"\s", "", source_text_stream(root))

    # 内容格拆段（c）：cells 空、paragraph 子块带 cell 戳；粗体整段 subheading（d）
    sub1 = by_id["x-0007"]
    assert sub1["type"] == "paragraph" and sub1["parent"] == "x-0006" and sub1["cell"] == 0
    assert sub1["subheading"] is True and sub1["text"] == "**小标题**"
    assert by_id["x-0008"]["text"] == "正文段一" and "subheading" not in by_id["x-0008"]
    # 行内列表挂行块（e）：li.parent = 行块 id（平台「行内子块紧随其行」约束），不挂段落
    assert by_id["x-0009"]["type"] == "list-item" and by_id["x-0009"]["parent"] == "x-0006"
    assert by_id["x-0009"]["cell"] == 0
    # 空段丢弃（f）：<p/> 与 <p>  </p> 不产块——行内子块恰为 段落×2 + li×1
    kids6 = [b for b in blocks if b.get("parent") == "x-0006"]
    assert [b["id"] for b in kids6] == ["x-0007", "x-0008", "x-0009"], kids6

    # ---- 表格：无 thead 表·表头不命中四反例（b）：单行/首行长文本/首行含 ol/首行纯数字
    for bid in ("b1", "b2", "b3", "b4", "b5", "b6", "b7"):
        assert by_id[bid]["type"] == "table-row" and by_id[bid]["head"] == [], bid
    assert by_id["b6"]["cells"] == ["1", "2"]  # 首行纯数字 → 全部行为数据行
    assert by_id["b4"]["cells"] == ["", "次格二"]  # 首行含 ol → 数据行；td 裸文本成段
    assert by_id["x-0010"]["text"] == "标题甲" and by_id["x-0010"]["cell"] == 0
    assert by_id["bn1"]["parent"] == "b4" and by_id["bn1"]["cell"] == 0

    # ---- 守恒通过 + thead 对称排除直接锁定
    guard, problems = verify_conservation(root, blocks, media_list)
    assert not problems, problems
    assert guard["algo"] == CONSERVATION_ALGO and guard["source"] == "xml"
    assert guard["mediaTokens"] == ["tok1", "tok2", "tok3"], guard["mediaTokens"]
    assert "列一" not in re.sub(r"\s", "", source_text_stream(root))  # 表头文本不进原文侧指纹

    # ---- 变异测试：对内存产物动手脚后守恒必须失败
    m_del = [b for b in copy.deepcopy(blocks) if b["id"] != "li2a"]  # 删一个块
    _, probs = verify_conservation(root, m_del, media_list)
    assert probs, "删块变异必须守恒失败"
    m_edit = copy.deepcopy(blocks)
    for b in m_edit:
        if b["id"] == "p1":
            b["text"] += "被篡改"
    _, probs = verify_conservation(root, m_edit, media_list)
    assert probs, "改文本变异必须守恒失败"
    m_media = [m for m in copy.deepcopy(media_list) if m["token"] != "tok2"]  # 少一个媒体条目
    _, probs = verify_conservation(root, blocks, m_media)
    assert probs, "媒体缺失变异必须守恒失败"

    # ---- 固定测试向量（双仓一致性锁）
    assert conservation_sha(doc_text_stream(json.loads(FIXED_VECTOR_INPUT))) == FIXED_VECTOR_SHA

    # ---- main 路径端到端（mkdtemp 隔离，参照 scan_refs.py 先例防并发互踩）
    tmp = tempfile.mkdtemp(prefix="_pd_test_")
    try:
        xml_p = os.path.join(tmp, "content.xml")
        with open(xml_p, "w", encoding="utf-8") as f:
            f.write(_SELF_TEST_XML)
        out_p = os.path.join(tmp, "doc.json")
        argv_backup = sys.argv
        sys.argv = ["parse_doc.py", "--xml", xml_p, "--out", out_p,
                    "--media-dir", os.path.join(tmp, "media")]
        try:
            rc = main()
        finally:
            sys.argv = argv_backup
        assert rc == 0, rc
        with open(out_p, encoding="utf-8") as f:
            doc = json.load(f)
        assert doc["guard"]["algo"] == CONSERVATION_ALGO
        assert doc["guard"]["textSha"] == guard["textSha"]
        assert doc["generator"].startswith("sdlc-intent/parse_doc.py 0.5")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"self-test 全部通过（blocks={len(blocks)} media={len(media_list)} "
          f"textSha={guard['textSha'][:16]}…）")
    return 0


# ---------------------------------------------------------------- main
class _ArgParser(argparse.ArgumentParser):
    """用法错误 exit 3——argparse 默认 error() 同样 exit 2，与守恒自检失败（exit 2）撞码，
    消费方按码路由会把用法错误误分类为守恒失败。退出码约定见文件头：
    0 成功 / 1 媒体下载失败 / 2 守恒失败 / 3 用法错误。"""

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(3, f"{self.prog}: error: {message}\n"
                    "（exit 3 = 用法错误；退出码约定 0 成功/1 媒体下载失败/2 守恒失败/3 用法错误）\n")


def main():
    ap = _ArgParser()  # 用法错误 exit 3（与守恒失败 exit 2 分离，码表见文件头）
    ap.add_argument("--xml", help="DocxXML content（jq -r '.data.document.content' 的产物）")
    ap.add_argument("--refmap", help="reference_map.comments JSON 文件")
    ap.add_argument("--md", help="纯 markdown 回退模式")
    ap.add_argument("--out", default="doc.json")
    ap.add_argument("--media-dir", default="media")
    ap.add_argument("--download", action="store_true", help="调用 lark-cli 下载媒体")
    ap.add_argument("--media-manifest", default=None,
                    help="媒体清单 JSON（token→{path,sha256,skipped}；命中免 lark-cli——"
                         "platform_sdlc 纯 Python 链路产物）")
    ap.add_argument("--url", default="")
    ap.add_argument("--document-id", default="")
    ap.add_argument("--revision-id", default="")
    ap.add_argument("--self-test", action="store_true",
                    help="内嵌脱敏 fixture 自检（不读外部文件，CI 用）")
    args = ap.parse_args()
    if args.self_test:
        return self_test()

    refmap = {}
    if args.refmap:
        raw = json.load(open(args.refmap, encoding="utf-8"))
        refmap = raw.get("comments", raw) if isinstance(raw, dict) else {}

    p = DocParser(refmap=refmap, url=args.url, document_id=args.document_id,
                  revision_id=args.revision_id)
    md_mode = False
    root = None
    if args.xml:
        content = open(args.xml, encoding="utf-8").read()
        root = parse_tree(content)
        p.walk(root)
    elif args.md:
        p.parse_markdown(open(args.md, encoding="utf-8").read())
        md_mode = True
        print("警告: markdown 回退模式：产物无块级 ordinal/parent 结构，resolve_anchors 条款级解析与"
              "list_clauses 全量列表不可用（doc-pipeline.md：仅调试/补位）", file=sys.stderr)
    else:
        ap.error("--xml 或 --md 必填其一")
    p.emit_comments()

    media_list = list(p.media.values())

    # 守恒自检（第一道门）：失败 exit 2 且不写 --out（退出码约定：0 成功 / 1 媒体下载失败——
    # 产物照常落盘 / 2 守恒失败——不落盘 / 3 用法错误——_ArgParser，与守恒失败撞码已分离）
    if md_mode:
        guard = {"algo": "markdown-fallback"}
    else:
        guard, problems = verify_conservation(root, p.blocks, media_list)
        if problems:
            print("守恒自检失败（conservation-v1）——解析产物与原文内容不一致，产物未落盘：",
                  file=sys.stderr)
            for line in problems:
                print(f"  - {line}", file=sys.stderr)
            print("  处置：不落盘、不回传平台。请人工 diff content.xml 与既有 doc.json 定位丢失点"
                  "（高发区：表格分栏内块、含图单元格夹注文本、li 裸文本前缀），修复后重跑本解析器。",
                  file=sys.stderr)
            return 2

    if args.download and media_list:
        manifest = None
        if args.media_manifest:
            raw = json.load(open(args.media_manifest, encoding="utf-8"))
            manifest = raw if isinstance(raw, dict) else {}
        download_media(media_list, args.media_dir, manifest=manifest)

    doc = {
        "generator": (GENERATOR + " markdown-fallback") if md_mode else GENERATOR,
        "source": {"url": args.url, "documentId": args.document_id,
                   "revisionId": args.revision_id},
        "blocks": p.blocks,
        "media": media_list,
        "guard": guard,
    }
    json.dump(doc, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    kinds = {}
    for b in p.blocks:
        kinds[b["type"]] = kinds.get(b["type"], 0) + 1
    ok = sum(1 for m in media_list if m["status"] == "ok")
    print(f"blocks={len(p.blocks)} {kinds}")
    print(f"media={len(media_list)} ok={ok} pending/failed={len(media_list) - ok}")
    if md_mode:
        print("conservation fallback（markdown 模式不做文本守恒）")
    else:
        print(f"conservation ok algo={guard['algo']} textSha={guard['textSha']} "
              f"mediaTokens={len(guard['mediaTokens'])}")
    anchored = sum(1 for b in p.blocks if not str(b["id"]).startswith("x-"))
    print(f"native-anchors={anchored}/{len(p.blocks)}")
    failed = sum(1 for m in media_list if str(m["status"]).startswith("failed"))
    if failed:  # 媒体下载失败不以 exit 0 收场(产物照常落盘,统计照常输出,调用方可感知)
        print(f"注意：{failed} 个媒体下载失败（见 media 状态），exit 1")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

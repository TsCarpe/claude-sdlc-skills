#!/usr/bin/env python3
"""parse_doc.py — 需求原文预处理：DocxXML/Markdown → 标准块模型 doc.json

格式无关的通用块模型（不绑定任何需求文档模板）：
  heading / paragraph / list-item / table-row / image / attachment / whiteboard / comment

设计要点：
  - 锚点 = 飞书原生块 ID（DocxXML 每个元素自带 id），重推稳定，无需自造 ID 体系
  - 结构切分纯确定性（html.parser），无 LLM 参与
  - 媒体（图片/附件/画板缩略图）经 lark-cli docs +media-download 落盘，mediaId=内容哈希
  - 评论：宿主块 comment-refs="cN" + reference_map.comments[cN].data 完整评论串 → comment 块
  - 内容守恒自检（conservation-v1，v0.4）：解析产物与原文字符流对账，失败 exit 2 不落盘

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

GENERATOR = "sdlc-intent/parse_doc.py 0.4"
VOID_TAGS = {"img", "source", "col", "br", "hr", "colgroup"}
# 单元格内由子块承载的结构（文本不进 cells，防双计）：list/图/附件/画板 + 分栏容器 + 嵌套表
KEEP_IN_TABLE_CELL = {"ol", "ul", "img", "figure", "whiteboard", "grid", "column", "table"}


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
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, dict(attrs))
        self.stack[-1].children.append(node)

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


def inline_text(node):
    """元素内联内容 → markdown 风格文本（cite→@用户，b→**，del→~~，br→换行）"""
    out = []

    def walk(n):
        if n.text:
            out.append(n.text)
        for c in n.children:
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
#            whiteboard 无 caption 不收）+ 排除 thead 子树
#   产物侧 = 全部块 text、cells 全列、image 块 caption；comment 块（来自 refmap，原文无正文）与
#            table-row 的 head（每行重复挂载，收则多重计数）不收；path/rowLabel/ordinal/marker/
#            media name/alt 不收
#   agent 门 = textSha 相等 + mediaTokens 与产物 media[].token 双向相等；不查 media status
#   （离线免 --download 跑时 status 恒 pending）；media status 全 ok 由平台落库终检把关
#   守恒盲区（双侧恒 0 或对称排除，声明而非缺陷）：评论内容（thread/quote 来自 refmap）、
#   字面 * ~ 字符、thead/head 文本、media name/alt
CONSERVATION_ALGO = "conservation-v1"


def source_text_stream(root):
    """原文侧字符流（见上方契约注释）"""
    buf = []

    def walk(n):
        if n.tag == "thead":
            return  # 与产物侧不收 head 对称排除
        if n.tag == "cite":
            buf.append(_cite_name(n.attrs))
            return  # 名字来自属性；cite 子树不收（与 inline_text 同款）
        if n.tag == "img":
            buf.append((n.attrs.get("caption") or "").strip())
            return  # img 无子内容；figure/source/whiteboard 无 caption 不收
        if n.text:
            buf.append(n.text)
        for c in n.children:
            walk(c)

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
    def walk(self, node, parent_id=None, in_table_cell=False, marker_chain=()):
        for c in node.children:
            self.dispatch(c, parent_id=parent_id, in_table_cell=in_table_cell,
                          marker_chain=marker_chain)

    def dispatch(self, node, parent_id=None, in_table_cell=False, marker_chain=()):
        tag = node.tag
        if tag in ("title",):
            self.emit({"id": self.block_id(node) or self.new_id(), "type": "title",
                       "text": plain_text(node), "path": plain_text(node)})
            return
        m = re.fullmatch(r"h([1-9])", tag)
        if m:
            level = int(m.group(1))
            text = plain_text(node)
            while self.headings and self.headings[-1][0] >= level:
                self.headings.pop()
            self.headings.append((level, text))
            self.emit({"id": self.block_id(node) or self.new_id(), "type": "heading",
                       "level": level, "text": text, "path": self.heading_path()})
            return
        if tag == "p":
            text = inline_text(node)
            if text:
                self.emit({"id": self.block_id(node) or self.new_id(), "type": "paragraph",
                           "text": text, "path": self.path_of(),
                           "comments": node.attrs.get("comment-refs")})
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
        if tag == "whiteboard":
            token = node.attrs.get("token") or ""
            self.emit({"id": self.block_id(node) or self.new_id(), "type": "whiteboard",
                       "token": token, "media": self.register_whiteboard(token),
                       "path": self.path_of()})
            return
        if tag in ("grid", "column", "div", "span", "blockquote", "body", "#root", "colgroup",
                   "col", "thead", "tbody", "tr", "td", "th", "li", "source", "b", "del", "i",
                   "code", "br", "cite"):
            # 容器/表格内部细节由专门逻辑处理；此处兜底递归
            if tag in ("td", "th", "tr", "li", "thead", "tbody"):
                return  # 已由 parse_table / walk_list 处理
            self.walk(node, parent_id=parent_id, in_table_cell=in_table_cell,
                      marker_chain=marker_chain)
            return
        # 未知标签：递归兜底
        self.walk(node, parent_id=parent_id, in_table_cell=in_table_cell,
                  marker_chain=marker_chain)

    # ---- lists
    @staticmethod
    def li_inline_text(li):
        """li 内联文本 = li 直接裸文本 + 非 ol/ul/img 子树的内联内容，无缝拼接（与 inline_text
        处理 p 的方式同构，保留 b→** / del→~~ / cite→@ / br→\\n 规则）——飞书 li 的「前缀：」
        常是裸文本、说明在 span 里，拼接才不断句"""
        out = [li.text or ""]

        def walk(n):
            for c in n.children:
                if c.tag in ("ol", "ul", "img"):
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
            # v0.4：li 裸文本直接收（旧行为只看子元素，前缀整段丢）；纯子列表 li 的 text 为空，
            # 仍发块保锚点；子列表内容只由子项块承载，不折进父 text（防双计）
            text = self.li_inline_text(li)
            self.emit({"id": bid, "type": "list-item", "marker": marker, "ordinal": ordinal,
                       "depth": len(chain), "text": text, "path": self.path_of(ordinal),
                       "parent": parent_id,
                       "comments": li.attrs.get("comment-refs") or None})
            for sub in li.children:
                if sub.tag == "img":
                    self.emit_image(sub, parent_id=bid)
                elif sub.tag in ("ol", "ul"):
                    self.walk_list(sub, parent_id=bid, marker_chain=chain)

    # ---- tables
    @staticmethod
    def cell_direct_text(td):
        """单元格直接文本 = td 裸文本 + 非 KEEP 子元素文本（\\n 连接，恢复段落边界）。
        KEEP 白名单子元素（list/img/figure/whiteboard/grid/column/嵌套 table）由子块承载，
        文本不进 cells——与 parse_table 的子块提取口径互斥，防双计。
        v0.4：删旧行为「cell 含图即弃全部直接文本」（图旁零散文本是正文而非夹注）"""
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
        dispatch）；KEEP 白名单成员由子块承载；其余（p/内联）文本走 cell_direct_text，不发块"""
        for c in td.children:
            if c.tag in ("grid", "column"):
                yield from DocParser._cell_subblocks(c)
            elif c.tag in KEEP_IN_TABLE_CELL:
                yield c

    def parse_table(self, table, parent_id=None):
        table_head = []
        thead = next((c for c in table.children if c.tag == "thead"), None)
        if thead is not None:
            tr = next((c for c in thead.children if c.tag == "tr"), None)
            if tr is not None:
                table_head = [plain_text(th) for th in tr.children if th.tag in ("th", "td")]
        body = next((c for c in table.children if c.tag == "tbody"), table)
        for idx, tr in enumerate([c for c in body.children if c.tag == "tr"], 1):
            tds = [c for c in tr.children if c.tag in ("td", "th")]
            cells = []
            row_label = ""
            for ci, td in enumerate(tds):
                cells.append(self.cell_direct_text(td))
                if ci == 0 and not row_label:
                    first = re.sub(r"\s+", "", plain_text(td))
                    row_label = (first or f"#{idx}")[:24]
            row_bid = self.block_id(tr) or self.new_id()
            path = self.path_of(row_label)
            self.emit({"id": row_bid, "type": "table-row", "head": table_head,
                       "cells": cells, "rowLabel": row_label, "path": path,
                       "parent": parent_id,
                       "comments": tr.attrs.get("comment-refs") or None})
            # 单元格内嵌块（list/img/figure/whiteboard/嵌套 table + 分栏内任意块级元素）挂行块
            for td in tds:
                for sub in self._cell_subblocks(td):
                    self.dispatch(sub, parent_id=row_bid)

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
        token = src.attrs.get("token") or ""
        media_id = self.register_media(token, name=src.attrs.get("name") or "attachment",
                                       mime=src.attrs.get("mime") or "", kind="media")
        self.emit({"id": self.block_id(node) or self.new_id(), "type": "attachment",
                   "media": media_id, "name": src.attrs.get("name") or "",
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
def download_media(media_list, media_dir):
    os.makedirs(media_dir, exist_ok=True)
    lark = _find_lark_cli()
    if not lark:
        print("错误: 未找到 lark-cli(查找顺序:PATH → ~/.nvm/versions/node/*/bin → "
              "/usr/local/bin、/opt/homebrew/bin)——媒体下载全部失败", file=sys.stderr)
        for m in media_list:
            m["status"] = "failed: lark-cli not found"
        return
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(lark) + os.pathsep + env.get("PATH", "")
    for m in media_list:
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

# 脱敏 mini fixture（虚构内容；真实文档不入仓）。覆盖面 = v0.4 四修复 + 守恒对称口径：
# thead 表格（表头不进指纹、行文本进）/ grid 两 column 各含一图（图成块挂行块 + media + caption）/
# li 裸文本+span 混排（前缀不丢）/ li 内只有子列表（父 text 空、子项不双计）/ 含图 cell 正文保留 /
# caption 进块 / cite 展开（含 cite 子树不收）
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
    tr1, tr2 = by_id["tr1"], by_id["tr2"]
    assert tr1["cells"] == ["单元格A1\n单元格A2", "纯文本B1"], tr1["cells"]  # 段落 \n 连接 + td 裸文本
    assert tr1["head"] == ["列一", "列二"]  # thead 进 head（展示层），不进指纹
    assert tr2["cells"][0] == "含图单元格局部说明", tr2["cells"]  # 含图 cell 文本不弃
    assert tr2["cells"][1] == "", tr2["cells"]  # grid cell 直接文本为空（内容由子块承载）
    assert by_id["im1"]["caption"] == "图一说明", by_id["im1"]["caption"]  # caption 进块去尾换行
    assert by_id["im2"]["caption"] == "图二说明" and by_id["im3"]["caption"] == "图三说明"
    assert by_id["im2"]["parent"] == "tr2" and by_id["im3"]["parent"] == "tr2"  # grid 内图挂行块
    assert {b["id"] for b in blocks if b["type"] == "image"} == {"im1", "im2", "im3"}
    assert set(p.media) == {"tok1", "tok2", "tok3"}  # grid 两图成为 media

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
        assert doc["generator"].startswith("sdlc-intent/parse_doc.py 0.4")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"self-test 全部通过（blocks={len(blocks)} media={len(media_list)} "
          f"textSha={guard['textSha'][:16]}…）")
    return 0


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml", help="DocxXML content（jq -r '.data.document.content' 的产物）")
    ap.add_argument("--refmap", help="reference_map.comments JSON 文件")
    ap.add_argument("--md", help="纯 markdown 回退模式")
    ap.add_argument("--out", default="doc.json")
    ap.add_argument("--media-dir", default="media")
    ap.add_argument("--download", action="store_true", help="调用 lark-cli 下载媒体")
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

    # 守恒自检（第一道门）：失败 exit 2 且不写 --out（与媒体下载失败 exit 1 产物照常落盘区分）
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
        download_media(media_list, args.media_dir)

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

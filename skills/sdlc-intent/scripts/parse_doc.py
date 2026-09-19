#!/usr/bin/env python3
"""parse_doc.py — 需求原文预处理：DocxXML/Markdown → 标准块模型 doc.json

格式无关的通用块模型（不绑定任何需求文档模板）：
  heading / paragraph / list-item / table-row / image / attachment / whiteboard / comment

设计要点：
  - 锚点 = 飞书原生块 ID（DocxXML 每个元素自带 id），重推稳定，无需自造 ID 体系
  - 结构切分纯确定性（html.parser），无 LLM 参与
  - 媒体（图片/附件/画板缩略图）经 lark-cli docs +media-download 落盘，mediaId=内容哈希
  - 评论：宿主块 comment-refs="cN" + reference_map.comments[cN].data 完整评论串 → comment 块

用法：
  parse_doc.py --xml content.xml --refmap refmap.json --out doc.json \
               --media-dir media/ [--download] [--url <来源URL>] [--md fallback.md]
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
from html import unescape
from html.parser import HTMLParser

GENERATOR = "sdlc-intent/parse_doc.py 0.3"
VOID_TAGS = {"img", "source", "col", "br", "hr", "colgroup"}
KEEP_IN_TABLE_CELL = {"ol", "ul", "img", "figure", "whiteboard"}


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
def inline_text(node):
    """元素内联内容 → markdown 风格文本（cite→@用户，b→**，del→~~，br→换行）"""
    out = []

    def walk(n):
        if n.text:
            out.append(n.text)
        for c in n.children:
            if c.tag == "cite":
                name = c.attrs.get("user-name") or c.attrs.get("user-id") or ""
                out.append(f"@{name}".strip())
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
            buf.append(f"@{c.attrs.get('user-name') or ''}")
        else:
            buf.append(_collect(c))
    return "".join(buf)


def plain_text(node):
    buf = [node.text]
    for c in node.children:
        if c.tag == "cite":
            buf.append(f"@{c.attrs.get('user-name') or ''}")
        else:
            buf.append(plain_text(c))
    return re.sub(r"\s+", " ", "".join(buf)).strip()


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
            text = ""
            child_lists = []
            images = []
            for sub in li.children:
                if sub.tag in ("ol", "ul"):
                    child_lists.append(sub)
                elif sub.tag == "img":
                    images.append(sub)
                else:
                    t = inline_text(sub) if sub.tag != "p" else inline_text(sub)
                    if t:
                        text = (text + "\n" + t).strip() if text else t
            if not text:
                text = inline_text(li)
            self.emit({"id": bid, "type": "list-item", "marker": marker, "ordinal": ordinal,
                       "depth": len(chain), "text": text, "path": self.path_of(ordinal),
                       "parent": parent_id,
                       "comments": li.attrs.get("comment-refs") or None})
            for img in images:
                self.emit_image(img, parent_id=bid)
            for sub in child_lists:
                self.walk_list(sub, parent_id=bid, marker_chain=chain)

    # ---- tables
    @staticmethod
    def cell_direct_text(td):
        """单元格直接文本：块级子元素（ol/ul/img/figure/whiteboard）由子块承载，避免重复平铺；
        含图/附件的单元格其零散直接文本是图片夹注，一并丢弃（alt 自带说明）"""
        stack = list(td.children)
        while stack:
            n = stack.pop()
            if n.tag in ("img", "figure", "whiteboard"):
                return ""
            stack.extend(n.children)
        parts = []
        for c in td.children:
            if c.tag in KEEP_IN_TABLE_CELL:
                continue
            t = inline_text(c)
            if t:
                parts.append(t)
        return " ".join(parts).strip()

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
            # 单元格内嵌块（list/img/figure/whiteboard）挂在 row 上
            for td in tds:
                for sub in td.children:
                    if sub.tag in ("ol", "ul"):
                        self.walk_list(sub, parent_id=row_bid, marker_chain=())
                    elif sub.tag == "img":
                        self.emit_image(sub, parent_id=row_bid)
                    elif sub.tag == "figure":
                        self.emit_figure(sub, parent_id=row_bid)
                    elif sub.tag == "whiteboard":
                        self.dispatch(sub, parent_id=row_bid)

    # ---- media
    def emit_image(self, node, parent_id=None):
        token = node.attrs.get("src") or node.attrs.get("id") or ""
        bid = self.block_id(node) or self.new_id()
        media_id = self.register_media(token, name=node.attrs.get("name") or "image",
                                       mime=node.attrs.get("mime") or "", kind="media")
        self.emit({"id": bid, "type": "image", "media": media_id,
                   "name": node.attrs.get("name") or "", "alt": node.attrs.get("alt") or "",
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
                           "name": "", "alt": "", "path": self.path_of(), "parent": None})
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
        for m in media_list:
            m["status"] = "failed: lark-cli not on PATH"
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


def _find_lark_cli():
    p = shutil.which("lark-cli")
    if p:
        return p
    for pat in (os.path.expanduser("~/.nvm/versions/node/*/bin/lark-cli"),):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    return None


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
    args = ap.parse_args()

    refmap = {}
    if args.refmap:
        raw = json.load(open(args.refmap, encoding="utf-8"))
        refmap = raw.get("comments", raw) if isinstance(raw, dict) else {}

    p = DocParser(refmap=refmap, url=args.url, document_id=args.document_id,
                  revision_id=args.revision_id)
    if args.xml:
        content = open(args.xml, encoding="utf-8").read()
        root = parse_tree(content)
        p.walk(root)
    elif args.md:
        p.parse_markdown(open(args.md, encoding="utf-8").read())
    else:
        ap.error("--xml 或 --md 必填其一")
    p.emit_comments()

    media_list = list(p.media.values())
    if args.download and media_list:
        download_media(media_list, args.media_dir)

    doc = {
        "generator": GENERATOR,
        "source": {"url": args.url, "documentId": args.document_id,
                   "revisionId": args.revision_id},
        "blocks": p.blocks,
        "media": media_list,
    }
    json.dump(doc, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    kinds = {}
    for b in p.blocks:
        kinds[b["type"]] = kinds.get(b["type"], 0) + 1
    ok = sum(1 for m in media_list if m["status"] == "ok")
    print(f"blocks={len(p.blocks)} {kinds}")
    print(f"media={len(media_list)} ok={ok} pending/failed={len(media_list) - ok}")
    anchored = sum(1 for b in p.blocks if not str(b["id"]).startswith("x-"))
    print(f"native-anchors={anchored}/{len(p.blocks)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""resolve_anchors.py — 把质检 payload 中的人读出处/引文解析为原文块锚点（v1.2）

策略（确定性，按序尝试）：
  1. 出处含「详述N」：定位表行块（rowLabel==N），若带「·<小节名>」则在行后代中找文本命中的条款块
  2. 出处/引文含「评论区#序号」：按评论列表序号映射到 comment 块
  3. quote「」摘引文本在整个文档块中子串匹配（≥6 字符，取首个命中）
  4. 全部失败 → 不加 anchor（前端回退 needle 定位，行为同 v1.1）

用法：
  resolve_anchors.py --doc doc.json [--comments comments.json] --payload payload.json --out payload-anchored.json
payload 需含 digest.fr_points / digest.features / audit.items / items 四类条目。
"""
import argparse
import json
import re


def _ref_key(s):
    """评论引用键自然排序 key：c2 < c10（纯字典序在 N≥10 时错乱）"""
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


def build_lookup(doc):
    blocks = doc.get("blocks", [])
    by_id = {b.get("id"): b for b in blocks}
    rows = {}                      # rowLabel -> block（同 label 取最后，详述表唯一）
    parent_of = {}
    children = {}
    for b in blocks:
        p = b.get("parent") or ""
        parent_of[b.get("id")] = p
        children.setdefault(p, []).append(b)
        if b.get("type") == "table-row":
            rows[b.get("rowLabel")] = b
    comments_by_id = {b.get("id"): b for b in blocks if b.get("type") == "comment"}
    comment_by_ref = {b.get("ref"): b for b in blocks if b.get("type") == "comment"}
    return blocks, by_id, rows, parent_of, children, comments_by_id, comment_by_ref


def descendants(children, rid):
    out, stack = [], [rid]
    while stack:
        cur = stack.pop()
        for c in children.get(cur, []):
            out.append(c)
            stack.append(c["id"])
    return out


def resolve_source(src, doc_lookups, comments_index):
    """出处字符串 → block 或 None"""
    blocks, by_id, rows, parent_of, children, comments_by_id, comment_by_ref = doc_lookups
    s = str(src or "")
    m = re.search(r"详述(\d+)", s)
    if m:
        row = rows.get(m.group(1))
        if row is None:
            for b in blocks:  # 兜底：rowLabel 可能带前缀
                if b.get("type") == "table-row" and str(b.get("rowLabel", "")).endswith(m.group(1)):
                    row = b
                    break
        if row is None:
            return None
        # 「详述N·<小节片段>」：在行后代中找文本命中
        tail = s.split("·", 1)[1] if "·" in s else ""
        tail = re.split(r"[；;+（(]", tail)[0].strip()
        if tail:
            # ① 序数匹配（出处写作 详述6·1.a.i / 详述6·2.3.1 时精确到条款）
            for d in descendants(children, row["id"]):
                od = d.get("ordinal") or ""
                if od == tail or (tail and od.endswith("." + tail)):
                    return d
            # ② 文本匹配：小节名（步骤一：设置比赛信息）
            for d in descendants(children, row["id"]):
                t = d.get("text") or ""
                if tail[:10] and tail[:10] in t:  # 小节名取前 10 字子串命中（原名常带「：说明」尾巴，全等匹配会漏）
                    return d
            # ③ 短文本回退
            for d in descendants(children, row["id"]):
                t = d.get("text") or ""
                if tail[:4] and tail[:4] in t:  # 再放宽到前 4 字宽匹配兜底（②级仍漏时接受少量误配）
                    return d
        return row
    mc = re.search(r"评论区#(\d+)", s)
    if mc:
        cid = comments_index.get(int(mc.group(1)))
        if cid:
            return comments_by_id.get(cid)
    return None


def resolve_quote(quote, blocks):
    q = str(quote or "")
    for seg in re.findall(r"「([^」]{6,})」", q):
        for b in blocks:
            t = b.get("text") or b.get("quote") or ""
            if t and seg in t:
                return b
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", required=True)
    ap.add_argument("--comments", help="list-comments JSON（用于评论区#序号 → comment-id 映射）")
    ap.add_argument("--refmap", help="reference_map JSON（cN → comment-id）")
    ap.add_argument("--payload", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    doc = json.load(open(args.doc, encoding="utf-8"))
    payload = json.load(open(args.payload, encoding="utf-8"))
    lookups = build_lookup(doc)

    # 评论区#序号 → comment-id：优先 list-comments 顺序，回退 refmap 中 cN 自然序
    comments_index = {}
    if args.comments:
        items = json.load(open(args.comments, encoding="utf-8"))
        items = items.get("data", {}).get("items", []) if isinstance(items, dict) else items
        for i, it in enumerate(items, 1):
            comments_index[i] = str(it.get("comment_id") or "")
    if args.refmap:
        raw = json.load(open(args.refmap, encoding="utf-8"))
        refs = raw.get("comments", raw)
        refs = {k: v for k, v in refs.items() if re.fullmatch(r"c\d+", k)}  # 滤掉 tips 等保留键
        for i, (k, v) in enumerate(sorted(refs.items(), key=lambda kv: _ref_key(kv[0])), 1):
            mm = re.search(r'comment-id=\\"(\d+)\\"', v.get("data", "")) or re.search(r'comment-id="(\d+)"', v.get("data", ""))
            comments_index.setdefault(i, mm.group(1) if mm else "")

    stats = {"fr": 0, "feature": 0, "audit": 0, "item": 0, "miss": 0}

    def attach(entry, source_text, quote_text, kind):
        blk = resolve_source(source_text, lookups, comments_index)
        if blk is None:
            blk = resolve_quote(quote_text, lookups[0])
        if blk is not None:
            entry["anchor"] = blk["id"]
            stats[kind] += 1
        else:
            stats["miss"] += 1

    for f in (payload.get("digest", {}).get("fr_points") or []):
        attach(f, f.get("source", ""), f.get("name", ""), "fr")
    for f in (payload.get("digest", {}).get("features") or []):
        attach(f, f.get("src", ""), f.get("func", ""), "feature")
    for it in (payload.get("audit", {}).get("items") or []):
        attach(it, it.get("where", ""), it.get("quote", ""), "audit")
    for it in (payload.get("items") or []):
        attach(it, it.get("ctx", ""), it.get("quote", ""), "item")

    json.dump(payload, open(args.out, "w", encoding="utf-8"), ensure_ascii=False)
    print("anchors:", stats)


if __name__ == "__main__":
    main()

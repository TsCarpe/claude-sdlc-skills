#!/usr/bin/env python3
"""list_clauses.py — 列出原文块结构中的条款清单，供 sdlc-intent 梳理时精确引用出处（v1.2）

梳理纪律：当 intake/doc-*.json 存在时，出处尽量写到条款级（人读格式「详述N·<小节名>」或
「详述N·<序数>」，如 详述6·步骤一 / 详述6·2.3.1），resolve_anchors.py 据此解析到具体条款块。

用法：
  list_clauses.py --doc doc.json                 # 列出全部顶层分组的条款树（截断文本）
  list_clauses.py --doc doc.json --row 6         # 只列 详述6 行内条款
  list_clauses.py --doc doc.json --depth 2       # 限制层级
"""
import argparse
import json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", required=True)
    ap.add_argument("--row", help="只列出某表格行（如 6）内的条款")
    ap.add_argument("--depth", type=int, default=4, help="最大层级（默认 4）")
    ap.add_argument("--width", type=int, default=60, help="文本截断宽度")
    args = ap.parse_args()

    doc = json.load(open(args.doc, encoding="utf-8"))
    blocks = doc.get("blocks", [])
    children = {}
    rows = []
    for b in blocks:
        children.setdefault(b.get("parent") or "", []).append(b)
        if b.get("type") == "table-row":
            rows.append(b)

    def walk(pid, depth, prefix):
        for c in children.get(pid, []):
            if c.get("type") != "list-item":
                continue
            if depth > args.depth:
                return
            text = (c.get("text") or "").replace("\n", " ")
            if len(text) > args.width:
                text = text[:args.width] + "…"
            cm = c.get("comments")
            mark = f" 💬{len(cm.split())}" if cm else ""
            print(f"{'  ' * depth}{c.get('marker', '').strip() or '-'} {text}{mark}"
                  f"    [详述{args.row}·{c.get('ordinal', '')}]"
                  if args.row else
                  f"{'  ' * depth}{c.get('marker', '').strip() or '-'} {text}{mark}    [{c.get('ordinal', '')}]")
            walk(c["id"], depth + 1, prefix)

    if args.row:
        matched = [r for r in rows if str(r.get("rowLabel", "")) == args.row]
        if not matched:
            import sys
            print(f"未找到行 {args.row}", file=sys.stderr)
            raise SystemExit(1)
        row = matched[-1]
        head = row.get("head") or []
        cells = row.get("cells") or []
        meta = " ｜ ".join(f"{head[i]}: {cells[i]}" for i in range(min(len(cells), len(head)))
                          if cells[i]) or "（无直接单元格文本）"
        print(f"== 详述{args.row}  {meta}")
        walk(row["id"], 0, args.row)
    else:
        for b in blocks:
            if b.get("type") == "heading":
                print(f"\n## {b.get('text')}")
            elif b.get("type") == "table-row" and not b.get("parent"):
                label = b.get("rowLabel", "")
                cells = b.get("cells") or []
                head = b.get("head") or []
                meta = " ｜ ".join(f"{head[i]}: {cells[i]}" for i in range(min(len(cells), len(head)))
                                  if cells[i])
                print(f"\n== 行[{label}]  {meta[:80]}")
                walk(b["id"], 0, label)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""sdlc-intent 参照表机械扫描器——把缺失类检测中可机械复现的部分从 LLM 手里拿走。

两种模式 + 自测：

  seeds   构表前供料：扫原文产两类 seed（断链候选/并列章节候选），LLM 构表时消费
  verify  构表后校验：扫 refs-*.md 参照表产三类机械结果，LLM 判定时消费
          ①字段出现位置清单（有录无消的证据义务）
          ②空格/⚠️冲突/依赖待裁决 机械候选行
          ③候选清单计数一致性核对

用法：
  scan_refs.py --mode seeds  --doc <原文.md | doc.json> [--out seeds.json]
  scan_refs.py --mode verify --doc <原文.md | doc.json> --refs <refs.md> [--out verify.json]
  scan_refs.py --self-test

设计约束（对齐 parse_doc.py / guardrails check.py 先例）：纯标准库；只做确定性检测，
不做语义判定——输出是「候选/证据」，缺陷判定永远在第 7 层由 LLM 完成。
"""

import argparse
import json
import re
import sys
from pathlib import Path

GENERATOR = "sdlc-intent/scan_refs.py 0.1"

# 引用语句指示词（断链 seed 用；命中即报，落点解析交给 LLM）
REF_PATTERNS = re.compile(r"(另行说明|另行规定|如上所述|上文提到|下文.{0,4}说明|详见|参见|见第[一二三四五六七八九十百\d]+[章节])")

# 常见并列章节后缀（对称维度 seed 用；仅提示性，识别定义以 ref-tables.md 通用定义为准）
PARALLEL_TAILS = ("设置", "分析", "管理", "列表", "报告", "评价", "详情", "对比", "说明")

EMPTY_CELL_MARKS = ("—", "🤔")


def load_doc(path):
    """返回 (texts, headings, is_docjson)：texts=全文片段列表[(idx, text)]，headings=[(idx, level, text)]。"""
    p = Path(path)
    if not p.exists():
        sys.exit(f"[scan_refs] 文件不存在: {path}")
    raw = p.read_text(encoding="utf-8")
    if p.suffix == ".json":
        try:
            doc = json.loads(raw)
        except json.JSONDecodeError as e:
            sys.exit(f"[scan_refs] doc.json 解析失败: {e}")
        texts, headings = [], []
        for i, b in enumerate(doc.get("blocks", [])):
            t = b.get("text") or ""
            if not t:
                continue
            texts.append((i, t))
            if b.get("type") == "heading":
                headings.append((i, b.get("level", 0), t))
        return texts, headings, True
    lines = raw.splitlines()
    texts = [(i, ln.strip()) for i, ln in enumerate(lines) if ln.strip()]
    headings = [(i, _md_heading_level(ln), ln.strip().lstrip("#").strip())
                for i, ln in enumerate(lines) if _md_heading_level(ln)]
    return texts, headings, False


def _md_heading_level(line):
    m = re.match(r"^(#{1,6})\s", line.strip())
    return len(m.group(1)) if m else 0


def parse_md_tables(md_text):
    """解析 refs.md 全部 markdown 表：返回 [(表名(最近标题), [行单元格列表])]。"""
    lines = md_text.splitlines()
    tables, cur_title, i = [], "", 0
    while i < len(lines):
        ln = lines[i]
        if _md_heading_level(ln):
            cur_title = ln.strip().lstrip("#").strip()
        elif ln.strip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not re.match(r"^:?-{2,}:?$", cells[0] or ""):  # 跳过分隔行
                    rows.append(cells)
                i += 1
            tables.append((cur_title, rows))
            continue
        i += 1
    return tables


def seeds_mode(doc_path):
    texts, headings, is_docjson = load_doc(doc_path)
    out = {"generator": GENERATOR, "mode": "seeds", "ref_statements": [], "parallel_chapter_groups": []}
    for idx, t in texts:
        m = REF_PATTERNS.search(t)
        if m:
            # doc.json 用块 idx；markdown 是 0-based 行号，人读从 1 起（「行0」不可读）
            out["ref_statements"].append({
                "where": f"块{idx}" if is_docjson else f"行{idx + 1}",
                "text": t[:120],
                "matched": m.group(0),
                "note": "落点是否存在于标题集，交 LLM 判定；标题集见 parallel_chapter_groups 与原文",
            })
    # 并列章节：同层标题、公共后缀 ∈ 常见表尾，≥2 个成组
    by_level = {}
    for _, lvl, h in headings:
        by_level.setdefault(lvl, []).append(h)
    for lvl, hs in by_level.items():
        for tail in PARALLEL_TAILS:
            group = [h for h in hs if h.endswith(tail) and len(h) > len(tail)]
            if len(group) >= 2:
                out["parallel_chapter_groups"].append({"level": lvl, "tail": tail, "headings": group})
    out["parallel_chapter_groups"].sort(key=lambda g: -len(g["headings"]))
    return out


def is_empty_cell(cell):
    c = (cell or "").strip()
    return (not c) or c.startswith(EMPTY_CELL_MARKS) or "未见" in c


def verify_mode(doc_path, refs_path):
    texts, headings, is_docjson = load_doc(doc_path)
    refs_md = Path(refs_path).read_text(encoding="utf-8")
    tables = parse_md_tables(refs_md)
    out = {"generator": GENERATOR, "mode": "verify",
           "field_occurrences": [], "mechanical_candidates": [], "conflicts": [],
           "pending_rows": [], "count_check": {}}

    mechanical = 0
    for title, rows in tables:
        if not rows or "候选清单" in title:
            continue
        header, body = rows[0], rows[1:]
        if any(k in title for k in ("数据字典", "指标字典", "平行结构", "引用图")):
            for r in body:
                cells = r + [""] * (len(header) - len(r))
                joined = "｜".join(cells)
                if "⚠️冲突" in joined:
                    out["conflicts"].append({"table": title, "row": r[:2]})
                if "依赖待裁决" in joined:
                    out["pending_rows"].append({"table": title, "row": r[:2]})
                empties = [header[j] for j in range(min(len(cells), len(header)))
                           if is_empty_cell(cells[j])]
                if empties and "数据字典" not in title:
                    out["mechanical_candidates"].append(
                        {"table": title, "key": cells[0], "empty_cols": empties})
                    mechanical += 1
        # 字段出现位置清单（数据字典第一列 → 全文计数）
        if "数据字典" in title:
            for r in body:
                if not r:
                    continue
                field = r[0]
                short = field.split(".")[-1].split("（")[0].strip()
                if not short or len(short) < 2:
                    continue
                # 位置标签与 seeds_mode 同口径：doc.json 块 idx / markdown 行号（1 起）
                hits = [f"{('块' + str(i)) if is_docjson else ('行' + str(i + 1))}:"
                        f"{t[max(0, t.find(short) - 10):t.find(short) + len(short) + 10]}"
                        for i, t in texts if short in t]
                # 截断至 12 条：证据用途只需覆盖 count<=1 的低频场景，超长清单徒耗判定层 token
                out["field_occurrences"].append(
                    {"field": field, "count": len(hits), "occurrences": hits[:12],
                     "hint": "count<=1 且唯一出现处是录入定义本身 → 有录无消证据成立"})

    # 候选清单计数一致性
    cand_rows = 0
    for title, rows in tables:
        if "候选清单" in title:
            cand_rows += max(0, len(rows) - 1)
    mechanical_total = mechanical + len(out["conflicts"])
    out["count_check"] = {
        "candidate_list_rows": cand_rows,
        "mechanical_hits": mechanical_total,
        "note": "不一致≠错误（机械扫描与 LLM 归并口径不同），但差额行需 LLM 复核是否漏登记",
    }
    return out


def self_test():
    import shutil
    import tempfile

    md = """# 测试需求
## 一、甲组设置
达标线划线，口径见下文说明
## 二、乙组设置
选择往届活动
## 三、统计报告
1. 达标率 = 达标数 / 总数
"""
    refs = """# 参照表
## 1. 数据字典（必建）
| 字段（实体.字段） | 录入处 | 消费处 | 来源 |
|---|---|---|---|
| 活动.机构类型 | 一.1 | —（未见消费） | 本系统录入 |
| 活动.所属赛区 | 一.1 | 二.2 报名 | 本系统录入 |
## 2. 指标字典
| 指标 | 公式 | 输入 | 输入的配置入口 | 精度 | 报告落点 |
|---|---|---|---|---|---|
| 贡献度指数 | — | — | — | — | 三.3 |
| 达标率 | 达标数/总数 | 达标数 | ⚠️冲突[三.1\\|三.4]（依赖待裁决） | — | 三.1 |
## 候选清单
| # | 表名 | 命中规则 | 定位 | 说明 |
|---|---|---|---|---|
| C1 | 数据字典 | 有录无消 | 一.1 | 机构类型 |
| C2 | 指标字典 | 空列 | 三.3 | 贡献度指数 |
"""
    # tempfile 隔离目录：/tmp 固定路径在并发 self-test（CI 矩阵/多 agent）下互踩
    tmp = tempfile.mkdtemp(prefix="_sr_test_")
    doc_p, refs_p = Path(tmp) / "doc.md", Path(tmp) / "refs.md"
    try:
        doc_p.write_text(md, encoding="utf-8")
        refs_p.write_text(refs, encoding="utf-8")

        s = seeds_mode(str(doc_p))
        assert any("下文" in r["matched"] or "说明" in r["text"] for r in s["ref_statements"]), s
        assert any(g["tail"] == "设置" and len(g["headings"]) == 2 for g in s["parallel_chapter_groups"]), s
        # markdown 输入的引用语句位置标签应为「行N」（1 起）
        assert s["ref_statements"] and s["ref_statements"][0]["where"].startswith("行"), s

        v = verify_mode(str(doc_p), str(refs_p))
        fields = {f["field"]: f for f in v["field_occurrences"]}
        assert fields["活动.所属赛区"]["count"] == 0  # 正文未出现「所属赛区」→ count==0 即有消无录证据
        assert len(v["conflicts"]) == 1 and "达标率" in v["conflicts"][0]["row"][0]
        assert len(v["pending_rows"]) == 1
        mech = [c for c in v["mechanical_candidates"]]
        assert any(c["key"] == "贡献度指数" and len(c["empty_cols"]) == 4 for c in mech), mech
        assert v["count_check"]["candidate_list_rows"] == 2
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("[scan_refs] self-test OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=["seeds", "verify"])
    ap.add_argument("--doc", help="原文 markdown 或 doc.json")
    ap.add_argument("--refs", help="refs-<日期>.md（verify 模式必填）")
    ap.add_argument("--out", help="结果写入文件（缺省 stdout）")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return
    if not args.mode or not args.doc:
        ap.error("--mode 与 --doc 必填（或用 --self-test）")
    if args.mode == "verify" and not args.refs:
        ap.error("verify 模式需要 --refs")
    result = seeds_mode(args.doc) if args.mode == "seeds" else verify_mode(args.doc, args.refs)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
        print(f"[scan_refs] 写入 {args.out}")
    else:
        print(payload)


if __name__ == "__main__":
    main()

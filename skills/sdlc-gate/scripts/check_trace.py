#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sdlc-gate 产物链追溯校验（issues 生成后 / 放行前的入口守卫）。

下沉自 issue-template「速览必填／落点-状态」与 docs/design/sdlc-id-linkage-plan.md
的三条约定（引用可达 / 计数同源 / 落改闭环）——判定由脚本完成，不依赖模型自觉。
形态对齐官方 best-practices「计划-验证-执行」：issues 文件=计划，本脚本=验证器，
生成后运行、exit≠0 修复重跑（反馈循环），全绿才进入人工裁决/放行。

用法：
    python3 check_trace.py <项目根> <需求名> [--release]

扫描（各取文件名日期最大一份；文件缺失/解析失败跳过并注明，存量不回改）：
    sdlc/<需求名>/intake/digest-*.md        需求.FR-xx / 需求.A-xx 定义源
    sdlc/<需求名>/intake/audit-*.md         体检.P-xx 定义源
    sdlc/<需求名>/test/cases.md             用例.TC-xx / 缺陷.BUG-xx 定义源
    sdlc/<需求名>/test/reports/*/static.md  静态.0x 定义源（best-effort）
    sdlc/<需求名>/review/*.md               评审.[DAST]-xx 定义源（被校验主体）

检查项（违规 exit 1，逐条给出 文件:行号 与可修复上下文）：
  1. 引用可达——产物中每个命名空间引用须在定义源一跳定位
  2. 计数同源——issues 速览统计表 vs 明细行逐表计数（前缀 × 高/中/低 + 备案；
     权衡列在裁决期才回填，生成时不校验）
  3. 落改闭环（--release）——裁决=落改的行，落点/状态须非空且=已执行
  4. FR 覆盖（best-effort）——digest 每个 FR 在 cases 双向追踪表有覆盖用例或非空原因

登记不校验（定义源在任务系统，位置不可知，输出注明）：
  设计.D-xx / 功能.F-xx / 确认.Q-xx / ER.X
已知边界（v1）：裸编号引用（如「设计 D6」）不检测——语境歧义大；仅 regex 解析
markdown 表格，列结构偏离模板时该检查跳过并注明。零第三方依赖（python3 标准库）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

OK, NG = "✅", "🔴"
SEV = ("高", "中", "低")
BUCKETS = ("分歧", "架构", "数据", "可测性")

# ---------- 命名空间注册表（来源：docs/design/sdlc-id-linkage-plan.md §2.1，增删须先改该文档） ----------

# 引用形态：正则 + 定义源 key + 规范 ID 构造（编号统一去前导零，如 FR-03 → FR-3）
REF_SPECS = [
    (re.compile(r"需求\.FR-(\d+)"), "digest", lambda m: f"FR-{int(m.group(1))}"),
    (re.compile(r"需求\.A(\d+)"), "digest", lambda m: f"A-{int(m.group(1))}"),
    (re.compile(r"体检\.P(\d+)"), "audit", lambda m: f"P-{int(m.group(1))}"),
    (re.compile(r"评审\.([DAST])-(\d+)"), "issues", lambda m: f"{m.group(1)}-{int(m.group(2))}"),
    (re.compile(r"用例\.TC-(\d+)"), "cases", lambda m: f"TC-{int(m.group(1))}"),
    (re.compile(r"缺陷\.BUG-(\d+)"), "cases", lambda m: f"BUG-{int(m.group(1))}"),
    (re.compile(r"静态\.0*(\d+)"), "static", lambda m: f"静态-{int(m.group(1))}"),
]
# 定义形态：源产物表格行首单元格（cases 另含 TC 明细小节标题）
DEF_SPECS: dict[str, list[tuple[re.Pattern, object]]] = {
    "digest": [
        (re.compile(r"^\|\s*FR-(\d+)\s*\|"), lambda m: f"FR-{int(m.group(1))}"),
        (re.compile(r"^\|\s*A(\d+)\s*\|"), lambda m: f"A-{int(m.group(1))}"),
    ],
    "audit": [
        (re.compile(r"^\|\s*P(\d+)\s*\|"), lambda m: f"P-{int(m.group(1))}"),
    ],
    "cases": [
        (re.compile(r"^\|\s*TC-(\d+)\s*\|"), lambda m: f"TC-{int(m.group(1))}"),
        (re.compile(r"^\|\s*BUG-(\d+)\s*\|"), lambda m: f"BUG-{int(m.group(1))}"),
        (re.compile(r"^#{2,4}\s*TC-(\d+)\b"), lambda m: f"TC-{int(m.group(1))}"),
    ],
    "issues": [
        (re.compile(r"^\|\s*([DAST])-(\d+)\s*\|"), lambda m: f"{m.group(1)}-{int(m.group(2))}"),
    ],
    "static": [
        (re.compile(r"^\|\s*静态-0*(\d+)\s*\|"), lambda m: f"静态-{int(m.group(1))}"),
    ],
}
REGISTERED_ONLY = re.compile(r"设计\.D\d+|功能\.F\d+|确认\.Q\d+|ER\.[A-Z]")
DETAIL_ROW_ID = re.compile(r"^([DAST])-(\d+)$")
FR_DEF = re.compile(r"^\|\s*FR-(\d+)\s*\|")
TRACE_ROW = re.compile(r"^需求\.FR-(\d+)")


def latest_by_name(paths: list[Path]) -> Path | None:
    """按文件名中的日期/rN 序号取最新一份（digest-20260910.md、issues-20260910-r2.md）。"""
    def key(p: Path):
        d = re.search(r"(\d{8})", p.name)
        r = re.search(r"-r(\d+)", p.name)
        return (d.group(1) if d else "0", int(r.group(1)) if r else 0)
    return max(paths, key=key) if paths else None


def read_lines(path: Path | None) -> list[str]:
    if path is None:
        return []
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def collect_defs(key: str, lines: list[str]) -> set[str]:
    out: set[str] = set()
    for ln in lines:
        for pat, build in DEF_SPECS[key]:
            m = pat.match(ln)
            if m:
                out.add(build(m))
    return out


def cells_of(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def is_table_row(line: str) -> bool:
    return line.lstrip().startswith("|") and not set(line.strip()) <= {"|", "-", " ", ":"}


def prefix_of(ident: str) -> str:
    return ident.rsplit("-", 1)[0]


def fmt_available(defs: set[str], prefix: str, src_name: str) -> str:
    """错误消息附「可修复上下文」：定义源文件 + 该命名空间现有编号范围与末 5 个。"""
    nums = sorted(int(d.rsplit("-", 1)[1]) for d in defs if prefix_of(d) == prefix)
    if not nums:
        return f"{src_name} 中该命名空间零定义"
    tail = "、".join(f"{prefix}-{n:0>2d}" for n in nums[-5:])
    return f"{src_name} 现有 {prefix}-{nums[0]:0>2d}…{prefix}-{nums[-1]:0>2d}（末 5 个：{tail}）"


def check_refs(files: dict[str, Path], defs: dict[str, set[str]]) -> tuple[list[str], int]:
    """检查 1：引用可达。ID/编号体系声明行内的示例引用跳过。"""
    msgs, checked = [], 0
    for key, path in files.items():
        for i, ln in enumerate(read_lines(path), 1):
            if "体系" in ln:
                continue
            for pat, src, build in REF_SPECS:
                for m in pat.finditer(ln):
                    checked += 1
                    ident = build(m)
                    if ident not in defs.get(src, set()):
                        src_name = files[src].name if src in files else f"{src}（缺失）"
                        msgs.append(f"引用不可达：{path.name}:{i} 引用 {m.group(0)} —— "
                                    f"{fmt_available(defs.get(src, set()), prefix_of(ident), src_name)}")
    return msgs, checked


def section_marks(lines: list[str]):
    """逐行标注所属章节号（〇速览/一分歧/二角色/三备案/四裁决汇总），供计数与闭环用。"""
    sec = ""
    for i, ln in enumerate(lines):
        m = re.match(r"^##\s*([〇一二三四])", ln)
        if m:
            sec = m.group(1)
        yield i, ln, sec


def check_counts(lines: list[str], issues_name: str) -> list[str]:
    """检查 2：速览统计表（〇节）vs 明细行（一/二节）逐表计数 + 备案行 vs 三节行数。"""
    declared: dict[str, dict[str, int]] = {}
    actual: dict[str, dict[str, int]] = {b: {s: 0 for s in SEV} for b in BUCKETS}
    backup = 0
    bucket_of = {"D": "分歧", "A": "架构", "S": "数据", "T": "可测性"}

    for _, ln, sec in section_marks(lines):
        if not is_table_row(ln):
            continue
        cs = cells_of(ln)
        head = cs[0].strip("*")
        if sec == "〇":
            if head.startswith(BUCKETS) and len(cs) >= 4:
                try:
                    declared[head[:2]] = {s: int(cs[1 + j].strip("*") or 0) for j, s in enumerate(SEV)}
                except ValueError:
                    return [f"计数检查跳过：{issues_name} 速览统计表含非数字单元格（结构偏离模板）"]
            elif head.startswith("备案") and len(cs) >= 6:
                try:
                    declared.setdefault("备案", {})["备案"] = int(cs[5].strip("*") or 0)
                except ValueError:
                    pass
        elif sec in ("一", "二") and DETAIL_ROW_ID.match(head):
            sev = None
            for c in cs[1:5]:  # 严重度可能在第 3/4 列（D 表·分类列、T 表·对象列后移）
                v = c.strip("*").split("·")[-1].strip()
                if v in SEV:
                    sev = v
                    break
            if sev:
                actual[bucket_of[head[0]]][sev] += 1
        elif sec == "三" and DETAIL_ROW_ID.match(head):
            backup += 1

    if not declared:
        return [f"计数检查跳过：{issues_name} 未找到速览统计表"]
    msgs = []
    for b in BUCKETS:
        for s in SEV:
            d, a = declared.get(b, {}).get(s), actual[b][s]
            if d is not None and d != a:
                msgs.append(f"计数不同源：{issues_name} 速览统计「{b}·{s}」声明 {d}，明细行为 {a}"
                            f"——明细行是唯一权威，请重数后改统计表")
    dn = declared.get("备案", {}).get("备案")
    if dn is not None and dn != backup:
        msgs.append(f"计数不同源：{issues_name} 备案声明 {dn}，备案区明细行为 {backup}")
    return msgs


def check_release(lines: list[str], issues_name: str) -> list[str]:
    """检查 3（--release）：裁决=落改的行，落点/状态列须=已执行。"""
    msgs = []
    for i, ln, sec in section_marks(lines):
        if sec not in ("一", "二", "四") or not is_table_row(ln):
            continue
        cs = cells_of(ln)
        head = cs[0].strip("*")
        if not re.match(r"^[DAST]-\d+", head):
            continue
        verdict_idx = 1 if sec == "四" else -2  # 汇总表列序：编号|裁决|摘要|落点/状态
        verdict, dest = cs[verdict_idx], cs[-1]
        if "落改" in verdict and "已执行" not in dest:
            msgs.append(f"落改未闭环：{issues_name}:{i + 1} {head} 裁决=落改，"
                        f"落点/状态=「{dest or '（空）'}」——须为 已执行 才可放行")
    return msgs


def check_fr_coverage(digest_lines: list[str], cases_lines: list[str],
                      digest_name: str, cases_name: str) -> tuple[list[str], bool]:
    """检查 4（best-effort）：digest 每个 FR 在 cases 双向追踪表有覆盖用例或非空原因。"""
    frs = sorted({int(m.group(1)) for ln in digest_lines if (m := FR_DEF.match(ln))})
    if not frs or not cases_lines:
        return [], False

    covered: set[int] = set()
    inside = False
    for ln in cases_lines:
        if re.match(r"^#{1,3}\s", ln):
            inside = "双向追踪表" in ln
            continue
        if not inside or not is_table_row(ln):
            continue
        cs = cells_of(ln)
        if len(cs) >= 4 and (m := TRACE_ROW.match(cs[0])):
            has_tc = bool(re.search(r"TC-", cs[2]))
            has_reason = cs[3] not in ("", "—", "（空）")
            if has_tc or has_reason:
                covered.add(int(m.group(1)))
    missing = [n for n in frs if n not in covered]
    if missing:
        refs = "、".join(f"需求.FR-{n:0>2d}" for n in missing)
        return [f"FR 覆盖缺口：{cases_name} 双向追踪表未覆盖 {refs}（定义于 {digest_name}）"], True
    return [], True


def main() -> int:
    argv = sys.argv[1:]
    release = "--release" in argv
    argv = [a for a in argv if not a.startswith("--")]
    if len(argv) != 2:
        print(__doc__)
        return 2
    root, req = Path(argv[0]).resolve(), argv[1]
    base = root / "sdlc" / req
    if not base.is_dir():
        print(f"{NG} 需求目录不存在：{base}")
        return 1

    intake, test, review = base / "intake", base / "test", base / "review"
    sources: dict[str, list[Path]] = {
        "digest": sorted(intake.glob("digest-*.md")),
        "audit": sorted(intake.glob("audit-*.md")),
        "cases": [test / "cases.md"] if (test / "cases.md").is_file() else [],
        "issues": sorted(review.glob("*.md")),
        "static": sorted(test.glob("reports/*/static.md")),
    }
    files = {k: latest_by_name(v) for k, v in sources.items()}
    files = {k: p for k, p in files.items() if p}
    skipped = [k for k in sources if k not in files]
    if "issues" not in files:
        print(f"{NG} review/ 下无 issues 文件——先完成 sdlc-gate Step 1-3 生成")
        return 1

    lines = {k: read_lines(p) for k, p in files.items()}
    defs = {k: collect_defs(k, v) for k, v in lines.items()}

    msgs, ref_count = check_refs(files, defs)
    msgs += check_counts(lines["issues"], files["issues"].name)
    if release:
        msgs += check_release(lines["issues"], files["issues"].name)
    fr_msgs, fr_ran = check_fr_coverage(lines.get("digest", []), lines.get("cases", []),
                                        files.get("digest", Path("?")).name,
                                        files.get("cases", Path("?")).name)
    msgs += fr_msgs

    ro = len(REGISTERED_ONLY.findall("\n".join("\n".join(v) for v in lines.values())))
    notes = []
    if skipped:
        notes.append("缺失跳过：" + "、".join(skipped))
    notes.append(f"登记不校验 {ro} 处（设计.D/功能.F/确认.Q/ER——定义源在任务系统）")
    if not fr_ran:
        notes.append("FR 覆盖检查跳过（digest 或 cases 缺失/无 FR）")

    if msgs:
        print(f"{NG} 追溯校验未通过（{len(msgs)} 项），逐条修复后重跑：")
        for m in msgs:
            print("  - " + m)
        print("；".join(notes))
        return 1
    print(f"{OK} 追溯校验通过：引用 {ref_count} 处可达；计数同源；"
          f"{'落改闭环；' if release else ''}FR 覆盖{'已核' if fr_ran else '跳过'}")
    for n in notes:
        print("  注：" + n)
    return 0


if __name__ == "__main__":
    sys.exit(main())

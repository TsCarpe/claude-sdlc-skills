#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sdlc-gate 产物链追溯校验（issues 生成后 / 放行前的入口守卫）。

下沉自 issue-template「速览必填／落点-状态」与 docs/design/sdlc-id-linkage-plan.md
的三条约定（引用可达 / 计数同源 / 落改闭环）——判定由脚本完成，不依赖模型自觉。
形态对齐官方 best-practices「计划-验证-执行」：issues 文件=计划，本脚本=验证器，
生成后运行、exit≠0 修复重跑（反馈循环），全绿才进入人工裁决/放行。

用法：
    python3 check_trace.py <项目根> <需求名> [--release]
    python3 check_trace.py --self-test        # 内置 fixture 回归（CI 用，exit 0 = 过）

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
GROUP_ROW_ID = re.compile(r"^[DAST]-\d+\s*[~–-]\s*[DAST]-\d+$")  # 分组裁决行（T-14~T-23）：状态以明细行为准
FR_DEF = re.compile(r"^\|\s*FR-(\d+)\s*\|")
TRACE_ROW = re.compile(r"^需求\.FR-(\d+)")
FR_DIALECT = re.compile(r"^([^.|\s]+)\.FR-(\d+)")  # 命名空间≠需求 的追踪行（如 示范.FR-01）：项目名误作命名空间


def latest_by_name(paths: list[Path]) -> Path | None:
    """按文件名中的日期/rN 序号取最新一份（digest-20260910.md、issues-20260910-r2.md）。

    三处复刻互相点名（跨 skill 不 import，单独安装互相不可见），改口径须三处同步：
    同目录内 check_trace.py 与 guard_dev.py 两处 + sdlc-test 侧 scripts/_shared.py。"""
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
    """检查 1：引用可达。头部 kv 区「| 编号体系 |」声明行的示例引用跳过。"""
    msgs, checked = [], 0
    for key, path in files.items():
        in_header = True  # 头部 kv 区 = 首个 ## 标题之前（编号体系声明行只在此区豁免）
        for i, ln in enumerate(read_lines(path), 1):
            if ln.startswith("##"):
                in_header = False
            if in_header and re.match(r"^\|\s*编号体系\s*\|", ln):
                continue  # issue-template 头部声明行：ID 体系说明非实际引用
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
    unparsed: list[str] = []  # 严重度列解析不出的明细行——静默跳过会把问题伪装成下游「计数不同源·请重数」
    bucket_of = {"D": "分歧", "A": "架构", "S": "数据", "T": "可测性"}

    for i, ln, sec in section_marks(lines):
        if not is_table_row(ln):
            continue
        cs = cells_of(ln)
        head = cs[0].strip("*")
        if sec == "〇":
            if head.startswith(BUCKETS) and len(cs) >= 4:
                bucket = next(b for b in BUCKETS if head.startswith(b))  # 完整桶名作 key（「可测性」截 2 字成「可测」会导致比较时永不命中）
                try:
                    declared[bucket] = {s: int(cs[1 + j].strip("*") or 0) for j, s in enumerate(SEV)}
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
                # 星号两态都剥：整格包裹 **三·高** 与只裹严重度的 三·**高**（模板红线只要求「高」加粗，两态皆合法）
                v = c.strip("*").split("·")[-1].strip("*").strip()
                if v in SEV:
                    sev = v
                    break
            if sev:
                actual[bucket_of[head[0]]][sev] += 1
            else:
                unparsed.append(f"严重度无法解析：{issues_name}:{i + 1} {head}"
                                f"（前四列「{'｜'.join(cs[:4])}」——严重度须为 高/中/低，如 分歧·高）")
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
    return msgs + unparsed


def check_release(lines: list[str], issues_name: str) -> list[str]:
    """检查 3（--release）：裁决=落改的行，落点/状态列须=已执行。

    分组裁决行（编号列含范围分隔符，模板约定「分组内逐条各有落点；状态见明细行」）
    跳过本身——分组内每条的闭环由一/二节明细行逐条校验，拦分组行只会误伤按模板字面填写者。"""
    msgs = []
    for i, ln, sec in section_marks(lines):
        if sec not in ("一", "二", "四") or not is_table_row(ln):
            continue
        cs = cells_of(ln)
        head = cs[0].strip("*")
        if GROUP_ROW_ID.match(head):
            continue
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
    dialect: list[str] = []  # 命名空间写成项目名等方言——不报会伪装成下游「覆盖缺口」，指因才能一次改对
    inside = False
    for i, ln in enumerate(cases_lines):
        if re.match(r"^#{1,3}\s", ln):
            inside = "双向追踪表" in ln
            continue
        if not inside or not is_table_row(ln):
            continue
        cs = cells_of(ln)
        if len(cs) < 4:
            continue
        if m := TRACE_ROW.match(cs[0]):
            has_tc = bool(re.search(r"TC-", cs[2]))
            has_reason = cs[3] not in ("", "—", "（空）")
            if has_tc or has_reason:
                covered.add(int(m.group(1)))
        elif m := FR_DIALECT.match(cs[0]):
            dialect.append(f"FR 前缀方言：{cases_name}:{i + 1} 首列「{cs[0].strip()}」"
                           f"应为「需求.FR-{int(m.group(2)):0>2d}」——全局 ID 约定：跨产物引用统一 "
                           f"命名空间.编号，命名空间是产物名「需求」而非项目名")
    missing = [n for n in frs if n not in covered]
    msgs = list(dialect)
    if missing:
        refs = "、".join(f"需求.FR-{n:0>2d}" for n in missing)
        msgs.append(f"FR 覆盖缺口：{cases_name} 双向追踪表未覆盖 {refs}（定义于 {digest_name}）")
    return msgs, True


# ---------- self-test（--self-test：内置 fixture 回归锚，供 CI 与本地改动后快验） ----------

_DIGEST_MD = """# selftest digest

| FR 编号 | 功能点 |
|---|---|
| FR-01 | 商品下单 |
| FR-02 | 订单退改 |
"""

_CASES_MD = """# selftest cases

## 双向追踪表

| FR | 功能 | 用例 | 原因 |
|---|---|---|---|
| 需求.FR-01 | 商品下单 | TC-01、TC-02 | |
| 需求.FR-02 | 订单退改 | TC-02 | |

## 用例明细

### TC-01 下单成功

| 用例 | 步骤 |
|---|---|
| TC-01 | 下单 |

### TC-02 退改成功

| 用例 | 步骤 |
|---|---|
| TC-02 | 退改 |
"""

_T14_ROW = "| T-14 | 用例 | 快照口径 | 高 | cases.md | 「x」 | y | 落改 | 落改（批量） | cases.md ｜ 已执行 |"
_T15_ROW = "| T-15 | 用例 | 快照口径 | 高 | cases.md | 「x」 | y | 落改 | 落改（批量） | cases.md ｜ 已执行 |"
_GROUP_ROW = "| T-14~T-15 | 落改（批量） | 快照口径统一 | 分组内逐条各有落点；状态见明细行 |"

_ISSUES_OK = f"""# selftest 评审 issue 清单（20260901 r1）

| 项 | 值 |
|---|---|
| 评审状态 | 待裁决 |
| 编号体系 | 分歧 D-xx / 架构 A-xx / 数据 S-xx / 可测性 T-xx；他产物引用本清单须带命名空间（评审.D-02 等） |

## 〇、速览与裁决焦点

### 统计

| 区块 | 高 | 中 | 低 | 权衡 | 小计 |
|---|---|---|---|---|---|
| 分歧 | 1 | 0 | 0 | — | 1 |
| 架构 | 1 | 0 | 0 | — | 1 |
| 数据 | 1 | 0 | 0 | — | 1 |
| 可测性 | 3 | 0 | 0 | — | 3 |
| **合计** | **6** | **0** | **0** | — | **6** |
| 备案（不进裁决） | — | — | — | — | 1 |

### 裁决焦点

| 编号 | 标题 | 建议动作 |
|---|---|---|
| D-01 | 覆盖 需求.FR-01 | 落改 |

## 一、分歧清单

| 编号 | 问题标题 | 分类·严重度 | 设计说 | 用例说 | 分歧点/后果 | 建议 | 裁决｜理由 | 落点/状态 |
|---|---|---|---|---|---|---|---|---|
| D-01 | 覆盖缺口 | 分歧·高 | a | b | 需求.FR-01 覆盖口径不一 | 落改（用例.TC-01） | 落改（补用例） | cases.md TC-01 ｜ 已执行 |

## 二、角色 issue

### 架构一致性

| 编号 | 问题标题 | 严重度 | 位置 | 原文摘引 | 问题 | 建议 | 裁决｜理由 | 落点/状态 |
|---|---|---|---|---|---|---|---|---|
| A-01 | 分层越界 | 高 | design.md | 「x」 | y | 落改 | 落改（调整） | design.md ｜ 已执行 |

### 数据模型与 SQL

| 编号 | 问题标题 | 严重度 | 位置 | 原文摘引 | 问题 | 建议 | 裁决｜理由 | 落点/状态 |
|---|---|---|---|---|---|---|---|---|
| S-01 | 字段口径 | 高 | design.md | 「x」 | y | 落改 | 落改（补口径） | design.md ｜ 已执行 |

### 测试可测性

| 编号 | 对象 | 问题标题 | 严重度 | 位置 | 原文摘引 | 问题 | 建议 | 裁决｜理由 | 落点/状态 |
|---|---|---|---|---|---|---|---|---|
| T-01 | 设计 | 断言缺口 | 高 | cases.md | 「x」 | y | 落改 | 落改（补断言） | cases.md ｜ 已执行 |
{_T14_ROW}
{_T15_ROW}

## 三、备案区

| 编号 | 来源角色 | 观察项 | 依据 | 处置 |
|---|---|---|---|---|
| T-09 | 可测性 | 观察 | 「x」 | 备案 |

## 四、裁决记录汇总

| 编号 | 裁决 | 摘要/理由 | 落点/状态 |
|---|---|---|---|
| D-01 | 落改（补用例） |  | cases.md ｜ 已执行 |
| A-01 | 落改（调整） |  | design.md ｜ 已执行 |
| S-01 | 落改（补口径） |  | design.md ｜ 已执行 |
| T-01 | 落改（补断言） |  | cases.md ｜ 已执行 |
{_GROUP_ROW}
"""

# 反例派生：计数反例（可测性速览 9 vs 明细 1，删 T-14/T-15 明细与分组行保持其余桶不误报）
_ISSUES_COUNT = (_ISSUES_OK
                 .replace("| 可测性 | 3 | 0 | 0 | — | 3 |", "| 可测性 | 9 | 0 | 0 | — | 9 |")
                 .replace(_T14_ROW + "\n", "")
                 .replace(_T15_ROW + "\n", "")
                 .replace(_GROUP_ROW + "\n", ""))
# 引用反例：含「体系」的明细行引用未定义 FR-98（修复前整行被「体系」子串豁免吞掉）
_ISSUES_REF = _ISSUES_OK.replace(
    "需求.FR-01 覆盖口径不一", "权限体系设计未覆盖 需求.FR-98（关联 需求.FR-01）")
# 落改反例：分组行全按模板填写，但 T-15 明细行未执行——应拦明细行而非分组行
_ISSUES_REL = _ISSUES_OK.replace(_T15_ROW, _T15_ROW.replace("已执行", "待执行"))
# 宽容正例：分类·严重度只局部加粗（分歧·**高**，模板红线「高必须加粗」的合法变体）——计数仍须同源
_ISSUES_BOLD = _ISSUES_OK.replace("分歧·高 | a |", "分歧·**高** | a |")
# 方言反例：追踪行命名空间误用项目名（示范.FR-01）——须指因报错而非伪装成覆盖缺口
_CASES_MD_DIALECT = _CASES_MD.replace("| 需求.FR-01 |", "| 示范.FR-01 |")


def self_test() -> int:
    """/tmp 构造产物 fixture，断言关键行为（桶计数 / 编号体系豁免 / 分组裁决行 / 未知 flag）。"""
    import io
    import shutil
    import tempfile
    from contextlib import redirect_stdout

    tmp = Path(tempfile.mkdtemp(prefix="check_trace_st_"))
    try:
        for name, issues, cases in (("ok", _ISSUES_OK, _CASES_MD),
                                     ("count", _ISSUES_COUNT, _CASES_MD),
                                     ("ref", _ISSUES_REF, _CASES_MD),
                                     ("rel", _ISSUES_REL, _CASES_MD),
                                     ("bold", _ISSUES_BOLD, _CASES_MD),
                                     ("dialect", _ISSUES_OK, _CASES_MD_DIALECT)):
            base = tmp / "sdlc" / name
            (base / "intake").mkdir(parents=True)
            (base / "test").mkdir(parents=True)
            (base / "review").mkdir(parents=True)
            (base / "intake" / "digest-20260901.md").write_text(_DIGEST_MD, encoding="utf-8")
            (base / "test" / "cases.md").write_text(cases, encoding="utf-8")
            (base / "review" / "issues-20260901.md").write_text(issues, encoding="utf-8")

        def run(args: list[str]) -> tuple[int, str]:
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(args)
            return rc, buf.getvalue()

        # 正例：健康产物全绿（四桶计数同源 + 分组行 + 头部编号体系行豁免 + --release 全流程）
        rc, out = run([str(tmp), "ok", "--release"])
        assert rc == 0 and "追溯校验通过" in out, f"健康 fixture 应全绿，实际 {rc}：\n{out}"

        # A1 反例：可测性桶速览 9 vs 明细 1 → 报计数不同源；其余桶不误报
        rc, out = run([str(tmp), "count"])
        assert rc == 1 and "「可测性·高」声明 9，明细行为 1" in out, out
        assert not any(f"「{b}·" in out for b in ("分歧", "架构", "数据")), out

        # A2 反例：含「体系」明细行的 需求.FR-98 未定义须被抓；头部编号体系行的 评审.D-02 仍豁免
        rc, out = run([str(tmp), "ref"])
        assert rc == 1 and "引用不可达" in out and "需求.FR-98" in out, out
        assert "评审.D-02" not in out, f"头部编号体系声明行应豁免：\n{out}"

        # A9 反例：分组行本身不拦（按模板字面填写），未执行的 T-15 明细行被拦且指向该行
        rc, out = run([str(tmp), "rel", "--release"])
        assert rc == 1 and "落改未闭环" in out and "T-15 裁决=落改" in out, out
        assert "T-14~T-15" not in out, f"分组裁决行不应被拦：\n{out}"

        # 宽容正例：严重度局部加粗（分歧·**高**）是模板红线合法变体——计数仍同源、全绿
        rc, out = run([str(tmp), "bold", "--release"])
        assert rc == 0 and "追溯校验通过" in out, f"局部加粗不应误报：\n{out}"

        # 方言反例：追踪行首列 示范.FR-01（项目名误作命名空间）→ 指因报错含正确形式，覆盖缺口并列
        rc, out = run([str(tmp), "dialect"])
        assert rc == 1 and "FR 前缀方言" in out and "应为「需求.FR-01」" in out, out
        assert "FR 覆盖缺口" in out, out

        # A7：拼错 flag 显式报错，不静默丢弃对应检查
        rc, out = run(["--relese", str(tmp), "ok"])
        assert rc == 2 and "未知参数" in out, out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("[check_trace] self-test OK")
    return 0


FLAGS = ("--release", "--self-test")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if "--self-test" in argv:
        return self_test()
    unknown = [a for a in argv if a.startswith("--") and a not in FLAGS]
    if unknown:  # 拼错 flag（如 --relese）若静默丢弃，对应检查会无声消失全绿——显式报错
        print(f"{NG} 未知参数：{'、'.join(unknown)}（合法 flag：{'、'.join(FLAGS)}）")
        return 2
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

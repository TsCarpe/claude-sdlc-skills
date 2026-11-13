#!/usr/bin/env python3
"""标准需求文档机检脚本(standard-doc-spec §4 机检档)。

用法:
  python3 scripts/check_standard_doc.py --doc <标准文档.md> [--answers <answers.json>] [--json]

answers.json 兼容两种形态:平台数组([{seq,answerText,status,...}])或 {"items":[...]}。
取数路径:publish 时 `GET /api/requirements/<reqId>/answers` 落盘的临时 json。
缺 --answers 时跳过依赖项(qa-compare / p-semantic / deferred-link)并提示。
status=deferred 的项参与 deferred-link(挂起→遗留假设投影)检查。

--json: stdout 只输出机器可读 JSON(人读文本一律走 stderr),契约:
  {"summary":{"fail","warn","skip","pass"},
   "checks":[{"name","level","details","data"?}],
   "fr":{"used":[两位号],"missing":[],"gaps":[]},        # missing 预留,当前未实现
   "assumptions":{"declared","used","noUse","ghost"}}
  四个顶级键恒定存在(SKIP/早退分支亦给空结构),便于平台直接消费。

退出码:0=无 FAIL;1=存在 FAIL(必须处理后重跑);2=用法/输入错误。
WARN 不影响退出码,需人工裁决后可选择忽略。

纯标准库,无第三方依赖。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}

# ---- 阈值/容差/窗口及其依据(调整前先跑真实文档回归) ----
P_SEMANTIC_OVERLAP_MIN = 0.25
# 实测真实文档:正确挂载的条款与 answerText 字符重叠率主体 >=25%;反向表述(结论换措辞复述)
# 等低重叠的正确挂载残余约个位数,由 WARN 级人工裁决兜住,不用 PASS/FAIL 硬判。
STRIKE_TOLERANCE = 2
# 多处 ~~标记~~ 对应废弃条款登记章一条登记属正常;实测正常偏差落在 ±2 内,>2 视为疑似漏登记。
SCAN_WINDOW = 2500
# 计数/矩阵断言后的目标表体通常在 1~2 屏内;窗口过大会数到下一个无关表格。
LIST_WINDOW = 1500
# 列表判定窗口,与 SCAN_WINDOW 同理。
SCOPE_RATIO_MAX = 0.05
# 「本期不做/⛔」正文章节字符占比上限:范围外内容应整章移出,仅在 1.2 边界表留一行。
SCOPE_HEADING = re.compile(r"^#{2,4}\s*.*(?:本期不做|⛔)")
# 判范围外章节标题;不含「明确不做」(那是 1.2 边界节,不该被计量)。

# #7 自包含:声明「自包含/不依赖外部」后,正文不得出现外部依赖表述(白名单放行「原型…报废/废弃」反向语境)
SELF_CONTAINED_CLAIM = re.compile(r"自包含|不依赖任何外部")
EXTERNAL_DEP_PAT = re.compile(r"以原型为准|以页面示例为基准|详见附件|见飞书原文|以原文随附.{0,12}为基准")
DEP_WHITELIST = re.compile(r"(?:原型|页面示例).{0,6}(?:报废|废弃)")
# #10 失败触发(2026-11-13 分档重构):失败态边按可判定性双档——
# FAIL(确定性档):mermaid 状态图边描述与目标态同名或为空(同义反复=没写进入条件,纯字符串判定不误报);
# WARN(语义档):其余边(有描述但充分性需理解/行文提及)出全量清单 data.edges,生成侧 AI 裁决补写。
# 关键词枚举判定(超时|错误码|…)退役:真实条件形态永远追不上(050 实测「少于 10 秒」「完全无声音」3/5 误报)。
FAIL_EDGE = re.compile(r"[→>＞]\s*([^\s，。；、|｜]{0,8}失败)")
MERMAID_EDGE = re.compile(r"^\s*(\S[^\n:]*?)\s*-+>\s*(\S+?)(?:\s*:\s*(.*))?$")

# 「数字+量词」的自然语言虚指用法(如"过了一段时间""在一处补充说明"),非计数断言。
# 仅收录计数正则量词集(段|项|类|条|处)实际可命中的组合;量词集扩展时同步补此处。
VAGUE_QUANTIFIERS = {"一段", "一处"}

# 元信息头模板键(spec §2:两列表格固定 5 行不增删,逐字照抄形态)
META_KEYS = ["需求编号", "风险分级", "版本依据", "澄清进度", "废弃条款"]
# 值内统计类括注(块数/媒体数等细节不进头部——2026-11 前旧文档高频缺陷,044 实测漏网)
STAT_BRACKET = re.compile(r"\d+\s*[块件]|块表|媒体\s*\d+|\d+\s*条评论|评论\s*\d+\s*条")
# 记号语义说明(spec §2:头部止于表格,符号/引用记号语义由平台 UI 承载,不写入文档任何位置)。
# 支四负向断言豁免「无/未记号…说明」否定语境——附录 D 质量自查表声明自身合规(「…无记号语义说明」)不算违例。
MARK_LEGEND_PAT = re.compile(r"^##.*阅读.*约定|固定记号|引用记号四类|(?<![无未])记号(语义)?说明", re.M)


def norm(s: str) -> str:
    """宽松归一:去空白与常见标点,用于文本一致性比对。

    全半角同形标点一并剥离(／= /、＝= =、：= :、；= ;)——合成器排版转写(半角→全角)
    不构成语义差异,qa-compare 不得因符号宽度判不一致。
    """
    return re.sub(r"[\s:=,，。:;；、()（）「」\[\]/／·～~\-—*`=＝]", "", s)


def strip_audit_refs(d: str) -> str:
    """剥离「体检.Pxx」引用段(含区间/顿号续列)与裸 Pxx~Pxx 区间,避免体检编号误当澄清裸 P 号。

    已知限制:裸区间 P21~P25 也会被剥(仅体检段应剥);由 evals/eval-l 的区间用例锁定预期,勿外推。
    """
    d = re.sub(r"体检\.P\d+(?:\s*[、,，/]?\s*[~-]\s*P?\d+)?(?:\s*[、,，/]\s*P?\d+)*", "", d)
    return re.sub(r"(?<![.．A-Za-z0-9])P\d+\s*[~-]\s*P?\d+", "", d)


def _num_both_sides(window: str, sep: str) -> bool:
    """window 中分隔符两侧是否都含数字/中文数字(用于判定「3 类/5 类」式并列枚举)。"""
    if sep not in window:
        return False
    left, right = window.split(sep, 1)
    pat = r"[一二三四五六七八九十\d]"
    return bool(re.search(pat, left)) and bool(re.search(pat, right))


def _in_quotes(line: str, pos: int) -> bool:
    """pos 是否落在真正配对的「」/（）/() 内(最近开括号到 pos 之间无闭括号)。"""
    for o, c in (("「", "」"), ("（", "）"), ("(", ")")):
        st = line.rfind(o, 0, pos)
        if st != -1 and line.find(c, st) >= pos:
            return True
    return False


def find_range_sections(doc: str) -> list[tuple[int, int]]:
    """「本期范围/明确不做」章节 [start,end)。不含泛词「边界」,避免吞噬整章。"""
    spans = []
    for m in re.finditer(r"^#{2,4}\s*.*(?:本期范围|明确不做).*$", doc, re.M):
        lvl = len(m.group(0)) - len(m.group(0).lstrip("#"))
        rest = doc[m.end():]
        mm = re.search(rf"^#{{1,{lvl}}}\s", rest, re.M)
        spans.append((m.start(), m.end() + (mm.start() if mm else len(rest))))
    return spans


def parse_answers(path: Path) -> tuple[dict[str, str], list[str]]:
    """返回 (seq→answerText 映射, 挂起项 seq 列表——status=deferred)。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"answers 解析失败({path}):{e};期望形态:平台数组 [{{seq,answerText,...}}] 或 {{\"items\":[...]}}") from e
    items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise ValueError(f"answers 形态不符({path}):既非数组也无 items 列表;期望平台数组 [{{seq,answerText,...}}] 或 {{\"items\":[...]}}")
    out = {}
    deferred: list[str] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        seq = str(it.get("seq") or "").strip()
        if seq:
            key = seq if seq.startswith("P") else f"P{seq}"
            out[key] = (it.get("answerText") or "").strip()
            if str(it.get("status") or "").strip() == "deferred":
                deferred.append(key)
    return out, deferred


def split_sections(doc: str) -> tuple[str, str]:
    """返回 (正文, 附录A段)。正文=附录A之前;附录段含自身标题行。

    章标题匹配容错:「附录 A」「附录A」均可(`附录\\s*A`);仅写「附录:澄清结论表」
    而无 A 字样时不匹配——由各检查项的"0 行必报 WARN"兜住,不得静默通过。
    """
    m = re.search(r"^## .*附录\s*A.*$", doc, re.M)
    body = doc[: m.start()] if m else doc
    seg_a = ""
    if m:
        rest = doc[m.start():]
        m2 = re.search(r"^## (?!.*附录\s*A).*$", rest, re.M)
        seg_a = rest[: m2.start()] if m2 else rest
    return body, seg_a


def locate_deprecated(doc: str) -> tuple[str, str]:
    """废弃条款登记段定位(返回 (段, 章名);未认返回 ('', ''))。

    标题须同含「附录」与「废弃/删除」:当前合成模板「附录 B　废弃条款清单(| B-1 | 序号)」
    与老模板「附录 C 废弃条款登记(| 1 | 序号)」均命中;正文章「## 7.3 废弃与替代策略」类
    因无「附录」不误命中。不再按「附录 C」字母盲定位——附录 C 可能是规则索引/术语表,
    其数字行被当登记数会造成假比对(2026-11 REQ-2026-050 实测:废弃清单在 B,字母定位
    数到 C 的 0 行,误报「登记 0 条」)。
    """
    m = re.search(r"^## .*附录.*(?:废弃|删除).*$", doc, re.M)
    if not m:
        return "", ""
    m2 = re.search(r"^## .*$", doc[m.end():], re.M)
    seg = doc[m.start(): m.end() + m2.start()] if m2 else doc[m.start():]
    return seg, m.group(0).lstrip("# ").strip()


def table_rows(seg: str, row_pat: str) -> list[list[str]]:
    rows = []
    for line in seg.splitlines():
        if re.match(row_pat, line.strip()):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows


def conclusion_col(seg: str) -> int | None:
    """附录 A 表头「结论」列号(0 基)。只扫首个 | Pxx | 数据行之前的表行,命中含「结论」的
    单元格即返回;分隔行(|---|)不含汉字自然跳过。列位不猜——找不到返回 None 由调用方降级。

    教训:曾硬编码取第 5 列,而现契约表头为 | seq | 级别 | 问题 | 结论 | 正文落点 |——第 5 列
    是正文落点,37/37 全部误判(2026-11 REQ-2026-050 实测)。表头定位对列序变化免疫。
    """
    for line in seg.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        if re.match(r"^\|\s*P\d+", s):
            break  # 已到数据行,表头不存在
        for i, c in enumerate(cell.strip() for cell in s.strip("|").split("|")):
            if "结论" in c:
                return i
    return None


def find_assumptions_section(doc: str) -> str:
    m = re.search(r"^## .*遗留假设.*$", doc, re.M)
    if not m:
        return ""
    rest = doc[m.start():]
    m2 = re.search(r"^## (?!.*遗留假设).*$", rest, re.M)
    return rest[: m2.start()] if m2 else rest


def count_table_body(seg: str) -> int:
    """数 seg 内第一个表体的数据行数(表头+分隔行之后的行);无表返回 0。"""
    m = re.search(r"(\|.*\|\s*\n\|[-| :]+\|\s*\n)((?:\|.*\|\s*\n?)+)", seg)
    return len([l for l in m.group(2).strip().splitlines() if l.strip()]) if m else 0


def cn_or_digit(m1: str) -> int | None:
    """中文数字/阿拉伯数字 -> int;解析不了返回 None。"""
    try:
        return int(m1) if m1.isdigit() else CN_NUM[m1]
    except (KeyError, ValueError):
        return None


class Checker:
    def __init__(self, doc: str, answers: dict[str, str] | None, deferred: list[str] | None = None):
        self.doc = doc
        self.answers = answers or {}
        self.deferred = list(deferred or [])
        self.body, self.seg_a = split_sections(doc)
        self.range_spans = find_range_sections(self.body)
        self.results: list[tuple[str, str, list[str], dict | None]] = []  # (级别, 项名, 明细, 结构化数据)

    def add(self, level: str, name: str, details: list[str], data: dict | None = None):
        self.results.append((level, name, details, data))

    # ---- 机检项 ----

    def check_qa_compare(self):
        if not self.answers:
            self.add("SKIP", "qa-compare(附录A vs answerText)", ["缺可用 --answers,转人工抽查附录 ≥5 条"])
            return
        rows = table_rows(self.seg_a, r"^\|\s*P\d+")
        if not rows:
            self.add("WARN", "qa-compare(附录A vs answerText)",
                     ["附录 A 段未数到表体行——确认附录标题含「附录 A」字样、表体行以 | Pxx | 开头;澄清结论表为必须附录,0 行不得按通过处理"])
            return
        col = conclusion_col(self.seg_a)
        if col is None:
            self.add("WARN", "qa-compare",
                     ["附录 A 表头未定位到「结论」列(在首个 | Pxx | 数据行之前的表头行中找含「结论」的列)——列位不猜,转人工核对结论列与 answerText"])
            return
        diffs = []
        for cells in rows:
            if len(cells) <= col:
                continue
            seq = cells[0]
            at = self.answers.get(seq)
            if at is None:
                diffs.append(f"{seq}: 附录有而 answers 无")
                continue
            if not at:
                continue  # 挂起项,answerText 为空属正常,由附录状态列表达
            cv = cells[col]
            if norm(at) != norm(cv) and norm(cv) not in norm(at) and norm(at) not in norm(cv):
                diffs.append(f"{seq}: 结论列与 answerText 不一致 | 附录={cv[:60]} | answers={at[:60]}")
        self.add("FAIL" if diffs else "PASS", "qa-compare", diffs or [f"{len(rows)} 条逐条一致(结论列=表头第 {col + 1} 列)"])

    def check_fr(self):
        used = sorted(set(re.findall(r"需求\.FR-(\d{2})", self.doc)), key=int)
        data = {"used": used, "missing": [], "gaps": []}
        if not used:
            self.add("WARN", "fr-continuity", ["全文无 FR 编号(若该文档不用 FR 体系可忽略)"], data)
            return
        nums = [int(x) for x in used]
        gaps = [f"{n:02d}" for n in range(min(nums), max(nums) + 1) if n not in nums]
        data["gaps"] = gaps
        dups_note = ""
        defines = re.findall(r"—\s*`?需求\.FR-(\d{2})", self.doc)
        dups = sorted({f"FR-{d}" for d in defines if defines.count(d) > 1}, key=lambda s: int(s[3:]))
        if dups:
            dups_note = f";重复定义(复用):{','.join(dups[:10])}"
        details = []
        if gaps:
            details.append(f"断号:{','.join('FR-' + g for g in gaps)}")
        if details:
            self.add("FAIL", "fr-continuity", details, data)
        else:
            self.add("PASS", "fr-continuity", [f"FR-{min(nums):02d}~{max(nums):02d} 连续无断号{dups_note}"], data)

    def check_p_coverage(self):
        declared = [c[0] for c in table_rows(self.seg_a, r"^\|\s*P\d+")]
        if not declared:
            self.add("WARN", "p-coverage",
                     ["未数到附录 A 澄清结论表表体——确认附录标题含「附录 A」字样、表体行以 | Pxx | 开头;0 行不得按通过处理"],
                     {"declared": [], "missing": [], "ghosts": []})
            return
        body_tags = set(re.findall(r"(?<![.．A-Za-z0-9])(?:〔)?P(\d{1,3})", strip_audit_refs(self.body)))
        missing = [p for p in declared if p[1:] not in body_tags]
        declared_n = {int(p[1:]) for p in declared}
        ghosts = sorted({f"P{n:02d}" for n in (int(x) for x in body_tags) if n not in declared_n}, key=lambda s: int(s[1:]))
        data = {"declared": declared, "missing": missing, "ghosts": ghosts}
        details = []
        if missing:
            details.append(f"附录有但正文无落点:{','.join(missing)}")
        if ghosts:
            details.append(f"正文幽灵 P 号(附录未登记):{','.join(ghosts)}")
        self.add("FAIL" if details else "PASS", "p-coverage", details or [f"{len(declared)} 项全部正文有落点,无幽灵号"], data)

    def check_a_registry(self):
        empty = {"declared": [], "used": [], "noUse": [], "ghost": []}
        sec = find_assumptions_section(self.doc)
        if not sec:
            self.add("WARN", "a-registry", ["未找到遗留假设章,跳过(确认该文档是否确无遗留假设)"], empty)
            return
        declared = sorted(set(re.findall(r"需求\.A(\d{2})", sec)), key=int)
        # 正文引用集排除声明章自身:声明章内的 A 号(含导语、来源列自引用)是登记不是使用,
        # 混入会把「声明但正文未引用」的漏报吃掉。
        body_wo_sec = self.body.replace(sec, "") if sec in self.body else self.body
        used = sorted(set(re.findall(r"需求\.A(\d{2})", body_wo_sec)), key=int)
        no_use = [f"A{n:02d}" for n in (int(x) for x in declared) if n not in {int(u) for u in used}]
        ghost = [f"A{n:02d}" for n in (int(x) for x in used) if n not in {int(d) for d in declared}]
        data = {"declared": declared, "used": used, "noUse": no_use, "ghost": ghost}
        details = []
        if ghost:
            details.append(f"正文引用但未声明:{','.join(ghost)}")
        if no_use:
            details.append(f"声明但正文未引用(逐条确认是否「不进正文」类故意):{','.join(no_use)}")
        self.add("FAIL" if ghost else ("WARN" if no_use else "PASS"), "a-registry",
                 details or [f"A{declared[0]}~A{declared[-1]} 声明与引用双向一致"], data)

    def check_strikes(self):
        seg, title = locate_deprecated(self.doc)
        # 序号兼容 | 1 |(老模板纯数字)与 | B-1 |(当前模板字母-数字)
        rows = [r for r in table_rows(seg, r"^\|\s*(?:[A-Z]-)?\d+\s*\|") if len(r) >= 2]
        strikes = re.findall(r"~~[^~]{2,80}~~", self.body)
        # 去除「阅读约定」里的记号说明行
        real = [s for s in strikes if "删除线" not in s or len(s) > 20]
        n_c, n_s = len(rows), len(real)
        where = title or "废弃条款登记章"
        if n_c == 0 and n_s == 0:
            if seg:
                self.add("WARN", "strike-vs-appendixc",
                         [f"「{where}」章存在但未数到表体行——确认表体格式(| 序 | / | B-1 | … 开头)或该章是否应有内容;0 行不得按通过处理"])
            else:
                self.add("PASS", "strike-vs-appendixc", ["正文无删除线、无废弃条款登记章——该文档无废弃条款"])
            return
        if n_s > 0 and n_c == 0:
            why = f"「{where}」章在但表体 0 行" if seg else "未找到废弃条款登记章(标题须同含「附录」与「废弃/删除」)"
            self.add("WARN", "strike-vs-appendixc", [f"正文删除线 {n_s} 处,而废弃条款登记 0 条({why})——疑似漏登记,人工排查"])
            return
        level = "PASS" if abs(n_c - n_s) <= STRIKE_TOLERANCE else "WARN"
        note = "数量吻合" if n_c == n_s else f"数量偏差(正文删除线 {n_s} 处 vs {where} {n_c} 条)——多处标记对应一条登记属正常,偏差>{STRIKE_TOLERANCE} 需排查漏登记"
        self.add(level, "strike-vs-appendixc", [note])

    def check_count_assert(self):
        hits: list[str] = []
        skipped = {"泛词": 0, "合计/分项语境": 0, "区间引用": 0, "引述语": 0, "并列枚举": 0, "元描述": 0, "无可数结构": 0}
        for m in re.finditer(r"([一二三四五六七八九十]|\d+)\s*(段|项|类|条|处)", self.doc):
            phrase = re.sub(r"\s+", "", m.group(0))
            if phrase in VAGUE_QUANTIFIERS:
                skipped["泛词"] += 1
                continue
            # 「第 4~6 项」类编号区间引用不是计数断言(- 置尾避免构成字符范围)
            if m.start() > 0 and self.doc[m.start() - 1] in "~-—－至":
                skipped["区间引用"] += 1
                continue
            # 只查"展示/共/分 N 段"类断言语境
            ctx = self.doc[max(0, m.start() - 25): m.end() + 6]
            ls = max(0, self.doc.rfind("\n", 0, m.start()))
            le = self.doc.find("\n", m.end())
            line = self.doc[ls: le if le != -1 else len(self.doc)]
            # 引述原文缺陷描述(「」/（）/() 内)不是本文档的计数断言
            if _in_quotes(line, m.start() - ls):
                skipped["引述语"] += 1
                continue
            # vs / 或 / 并列枚举:仅当分隔符两侧都出现数量时才视为并列,避免吞掉真计数错误
            w = self.doc[max(0, m.start() - 12): m.end() + 12]
            if any(_num_both_sides(w, sep) for sep in ("vs", "或", "/")):
                skipped["并列枚举"] += 1
                continue
            # 元描述词(紧邻 ±15 字)是口径对比/原文引述,不是计数断言
            if re.search(r"不一致|口径不一致|原文写法", self.doc[max(0, m.start() - 15): m.end() + 15]):
                skipped["元描述"] += 1
                continue
            if "合计" in ctx or re.search(r"[一二三四五六七八九十\d]+\s*类\s*[一二三四五六七八九十\d]+\s*项", ctx):
                # 「N 类 M 项」双计数语境:总数按类分摊,其后结构往往按类分组,直数条目会错位
                skipped["合计/分项语境"] += 1
                continue
            if re.search(r"\d\s*项\s*[+＋和及与]", self.doc[max(0, m.start() - 30): m.start()]) or (
                    re.match(r"\s*[+＋]", self.doc[m.end():]) if self.doc[m.end():] else False):
                # 「3 项 + 4 项」分项语境:分项数字各自不对应完整清单,总数才对应
                # (前置窗口存在并列分项、或断言后紧接并列加号,均属分项)
                skipped["合计/分项语境"] += 1
                continue
            if not re.search(r"展示|共|分|含|列出|如下", ctx):
                continue
            n = cn_or_digit(m.group(1))
            if n is None:
                continue
            # 找后续最近的列表/表体
            after = self.doc[m.end():]
            list_n = len(re.findall(r"^\s*(?:[-*]|\d+[.).])\s+", after[:LIST_WINDOW].split("\n\n")[0], re.M))
            tab_n = count_table_body(after[:SCAN_WINDOW])
            best = max(list_n, tab_n)
            if not best:
                skipped["无可数结构"] += 1
                continue
            if best != n:
                flat_ctx = " ".join(line.split())
                hits.append(f"计数断言「{m.group(0)}」(位置:{flat_ctx[:44]}…) 与后续列表/表体条目数({best})不符")
        n_skip = sum(skipped.values())
        details = hits or ["显式计数断言与所列条目数相符(启发式,未覆盖处仍靠人工)"]
        if n_skip:
            parts = [f"{k} {v}" for k, v in skipped.items() if v]
            details.append(f"滤噪跳过 {n_skip} 处({'; '.join(parts)})——跳过非放行,人工档留意")
        self.add("WARN" if hits else "PASS", "count-assert", details)

    def check_matrix_assert(self):
        hits: list[str] = []
        no_table = 0
        for m in re.finditer(r"([一二三四五六七八九十]|\d+)\s*类动作", self.doc):
            n = cn_or_digit(m.group(1))
            if n is None:
                continue
            rows = count_table_body(self.doc[m.end(): m.end() + SCAN_WINDOW])
            if not rows:
                no_table += 1
                continue
            if rows != n:
                hits.append(f"自称「{m.group(0)}」而矩阵实际 {rows} 行")
        if hits:
            self.add("FAIL", "matrix-assert", hits)
        elif no_table:
            self.add("WARN", "matrix-assert",
                     [f"发现 {no_table} 处「N 类动作」断言但其后 {SCAN_WINDOW} 字符窗口内未数到表体——确认矩阵位置/格式,不得按通过处理"])
        else:
            self.add("PASS", "matrix-assert", ["矩阵自称动作数与行数一致(未发现该类断言时视为通过)"])

    def check_raw_json(self):
        n = self.doc.count('{"kind":')
        self.add("FAIL" if n else "PASS", "raw-json", [f"出现 {n} 处裸 JSON"] if n else ["零裸 JSON"])

    def check_meta_header(self):
        """元信息头按模板(spec §2):紧跟 h1 两列表格固定 5 行、键序一致、值内无统计类括注、
        全文无记号语义说明。旧格式(11 行头/blockquote 头/阅读约定章)在此 FAIL,合成侧重跑修复。
        「版本依据」缺时间锚降为 WARN(原文/快照/合成三时间齐备——快照时间是依据版本的锚)。"""
        details, warn = [], []
        lines = self.doc.splitlines()
        h1 = next((k for k, l in enumerate(lines) if l.startswith("# ")), None)
        if h1 is None:
            self.add("FAIL", "meta-header", ["未找到 h1 主标题,无法定位元信息头"], {"ok": False})
            return
        k = h1 + 1
        while k < len(lines) and not lines[k].strip():
            k += 1
        tbl: list[list[str]] = []
        while k < len(lines) and lines[k].lstrip().startswith("|"):
            tbl.append([c.strip() for c in lines[k].strip().strip("|").split("|")])
            k += 1
        if not tbl or not all(len(r) == 2 for r in tbl):
            details.append("h1 后首个块不是两列表格(模板:| 项 | 内容 | + 固定 5 数据行)")
        else:
            if tbl[0] != ["项", "内容"]:
                details.append(f"表头非「项|内容」:{'|'.join(tbl[0])}")
            # 跳过分隔行(|---|---|)后即数据行
            rows = tbl[2:] if len(tbl) >= 2 and set(tbl[1][0] or "-") <= set("-: ") else tbl[1:]
            if len(rows) != len(META_KEYS):
                details.append(f"数据行 {len(rows)} 行 ≠ 模板固定 {len(META_KEYS)} 行:"
                               f"现有键({'、'.join(r[0] for r in rows) or '无'})")
            for got, want in zip(rows, META_KEYS):
                if got[0] != want:
                    details.append(f"行键「{got[0]}」≠ 模板「{want}」(键序固定,不增删不改名;迭代/统计不进头部)")
            for r in rows:
                if STAT_BRACKET.search(r[1] if len(r) > 1 else ""):
                    details.append(f"值内含统计类括注(块数/媒体数等细节不进头部):{r[0]}={r[1][:40]}")
            vb = next((r[1] for r in rows if r[0] == "版本依据"), "")
            miss_t = [t for t in ("原文", "快照", "合成") if t not in vb]
            if miss_t:
                warn.append(f"「版本依据」缺时间锚({'/'.join(miss_t)};应:原文 vX.Y.Z(date) · 质检快照 date · 合成 date)")
        legend = [m.group(0) for m in MARK_LEGEND_PAT.finditer(self.doc)]
        if legend:
            details.append(f"含记号语义说明 {len(legend)} 处(如「{legend[0][:20]}」)——通用约定由平台 UI 承载,不写入文档")
        data = {"ok": not details}
        if details:
            self.add("FAIL", "meta-header", details, data)
        elif warn:
            self.add("WARN", "meta-header", warn, data)
        else:
            self.add("PASS", "meta-header", ["两列表格 5 行,键序与模板一致,无统计括注,无记号语义说明"], data)

    def check_p_semantic(self):
        if not self.answers:
            self.add("SKIP", "p-semantic(〔Pxx〕记号语义)", ["缺可用 --answers,转人工抽查"])
            return
        hits = []
        for m in re.finditer(r"〔P(\d{1,3})[·]?[^〕]*〕", self.body):
            seq = f"P{m.group(1)}"
            at = self.answers.get(seq)
            if not at:
                continue
            line_start = self.body.rfind("\n", 0, m.start())
            line_end = self.body.find("\n", m.end())
            line = self.body[line_start: line_end if line_end != -1 else len(self.body)]
            s = line.strip()
            # 减噪:标题/表头/短行的记号是落点标注而非条款语义,天然低重叠,不参与抽查
            if s.startswith("#") or s.startswith("|") or len(s) < 15:
                continue
            # 多对多登记行(同行 ≥2 个 P 标记)不参与条款语义抽查
            if len(re.findall(r"〔P\d{1,3}", line)) >= 2:
                continue
            # 1.2 本期范围/不做/边界清单是「影响章节」登记,非条款本身
            if any(s <= m.start() < e for s, e in self.range_spans):
                continue
            overlap = len(set(norm(at)) & set(norm(line))) / max(1, len(set(norm(at))))
            if overlap < P_SEMANTIC_OVERLAP_MIN:
                hits.append(f"{seq} 标注处与 answerText 字符重叠率 {overlap:.0%}(阈值 {P_SEMANTIC_OVERLAP_MIN:.0%}),疑似按主题相近错挂:条款={line.strip()[:50]}")
        self.add("WARN" if hits else "PASS", "p-semantic", hits or ["抽查全部〔Pxx〕标注处与答案语义对应(字符重叠启发式;反向表述类低重叠由人工裁决)"])

    def check_scope_discipline(self):
        """「本期不做/⛔」正文章节字符占比 > 5% 即 WARN(范围外内容不应整章留档)。"""
        lines = self.body.splitlines(keepends=True)
        allh = [(i, len(l) - len(l.lstrip("#")), l) for i, l in enumerate(lines) if re.match(r"^#{1,6}\s", l)]
        spans = []
        for idx, (i, lvl, l) in enumerate(allh):
            if not SCOPE_HEADING.match(l):
                continue
            end = next((allh[j][0] for j in range(idx + 1, len(allh)) if allh[j][1] <= lvl), len(lines))
            seg = "".join(lines[i:end])
            spans.append((re.sub(r"^#+\s*", "", l.strip())[:40], len(seg)))
        total = sum(len(l) for l in lines) or 1
        over = [(t, n / total) for t, n in spans if n / total > SCOPE_RATIO_MAX]
        if over:
            self.add("WARN", "scope-discipline",
                     [f"「本期不做」章「{t}」占正文 {r:.1%} > {SCOPE_RATIO_MAX:.0%}——范围外内容宜整章移出,仅在 1.2 边界表留一行"
                      for t, r in over])
        elif spans:
            self.add("PASS", "scope-discipline",
                     [f"本期不做章占比 {sum(n for _, n in spans) / total:.1%} ≤ {SCOPE_RATIO_MAX:.0%}"])
        else:
            self.add("PASS", "scope-discipline", ["正文无「本期不做/⛔」章节"])

    def check_self_contained(self):
        """#7:声明「自包含/不依赖任何外部」后,正文不得出现外部依赖表述,否则声明与正文矛盾(FAIL)。
        白名单:「原型/页面示例…报废/废弃」属反向语境(说明不依赖),不算矛盾。未声明自包含时不检查。"""
        if not SELF_CONTAINED_CLAIM.search(self.doc):
            self.add("PASS", "self-contained", ["未声明自包含,不检查外部依赖表述"])
            return
        hits = []
        for m in EXTERNAL_DEP_PAT.finditer(self.doc):
            if DEP_WHITELIST.search(self.doc[max(0, m.start() - 10): m.end() + 10]):
                continue
            line_no = self.doc.count("\n", 0, m.start()) + 1
            hits.append(f"第 {line_no} 行「{m.group(0)}」与自包含声明矛盾——版式/依赖表述要么文本化进正文,要么改写自查断言")
        self.add("FAIL" if hits else "PASS", "self-contained",
                 hits or ["自包含声明与正文一致,无外部依赖表述"])

    def check_failure_trigger(self):
        """#10 分档(2026-11-13 重构):失败态边按可判定性双档。
        FAIL(确定性档):mermaid 状态图边描述与目标态同名或为空——同义反复即没写进入条件,
          纯字符串判定不误报(050 实测 2 处真问题即此形态);
        WARN(语义档):其余边出全量清单 data.edges({line,from,to,desc,kind}),由生成侧 AI
          裁决补写触发条件(发布不拦)——「少于 10 秒」「完全无声音」等条件形态的关键词枚举
          永远追不上(050 实测 3/5 误报),语义判定交还语义侧。"""
        lines = self.doc.splitlines()
        # mermaid 园栏行集合(```mermaid … ```;容错行首缩进)
        fence, mermaid_lines = False, set()
        for i, l in enumerate(lines):
            t = l.strip()
            if t.startswith("```"):
                if not fence and "mermaid" in t:
                    fence = True
                elif fence:
                    fence = False
                continue
            if fence:
                mermaid_lines.add(i)
        fails, edges = [], []
        for i, l in enumerate(lines):
            for m in FAIL_EDGE.finditer(l):
                to = m.group(1)
                if i in mermaid_lines:
                    em = MERMAID_EDGE.match(l)
                    desc = (em.group(3) or "").strip() if em else ""
                    desc_n = desc.rstrip("。，；,;：: ")
                    edges.append({"line": i + 1,
                                  "from": em.group(1).strip() if em else "",
                                  "to": to, "desc": desc, "kind": "state-diagram"})
                    if not desc_n or desc_n == to:
                        fails.append(f"第 {i + 1} 行「{to}」边触发条件未写明"
                                     f"(描述{'为空' if not desc_n else '与目标态同名'})——失败态不可测,"
                                     f"须补写进入条件(超时/错误场景/判定依据)")
                else:
                    edges.append({"line": i + 1, "from": "", "to": to,
                                  "desc": l.strip()[:60], "kind": "inline"})
        if fails:
            self.add("FAIL", "failure-trigger", fails, {"edges": edges})
        elif edges:
            self.add("WARN", "failure-trigger",
                     [f"{len(edges)} 条失败态边待语义裁决(生成侧闭环补写触发条件,发布不拦;"
                      f"关键词枚举判定已退役)"]
                     + [f"第 {e['line']} 行 [{e['kind']}] {e['to']}: {e['desc'] or '(无描述)'}"
                        for e in edges],
                     {"edges": edges})
        else:
            self.add("PASS", "failure-trigger", ["无「→ X失败」状态机边,不检查"])

    def check_deferred_link(self):
        """挂起项落点(P1-7):status=deferred 的澄清项须在正文有〔Pxx…挂起〕标注或遗留假设章登记,
        否则「挂起→遗留假设」只停留在发布记录层,文档层无投影(WARN)。缺 answers 转人工。"""
        if not self.answers:
            self.add("SKIP", "deferred-link(挂起→假设投影)", ["缺可用 --answers,转人工核对挂起项落点"])
            return
        if not self.deferred:
            self.add("PASS", "deferred-link", ["answers 无挂起项,无需投影"])
            return
        assumption_sec = find_assumptions_section(self.doc)
        hits = []
        for seq in self.deferred:
            in_body = re.search(rf"〔\s*{seq}[·][^〕]*挂起[^〕]*〕", self.doc)
            in_assumptions = seq in assumption_sec
            if not in_body and not in_assumptions:
                hits.append(f"{seq}: 挂起项在正文无〔{seq}·挂起〕标注、遗留假设章亦未登记——挂起结论未投影进定稿")
        self.add("WARN" if hits else "PASS", "deferred-link",
                 hits or [f"挂起项 {','.join(self.deferred)} 均有正文/遗留假设落点"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="check_standard_doc.py",
        description="标准需求文档机检(standard-doc-spec §4 机检档)",
        epilog="示例: python3 scripts/check_standard_doc.py --doc 标准文档.md --answers answers.json [--json]",
    )
    ap.add_argument("--doc", required=True, help="标准需求文档 markdown 路径")
    ap.add_argument("--answers", help="澄清答复 json 路径(publish 时 GET /api/requirements/<reqId>/answers 落盘;缺省时 qa-compare/p-semantic 转人工)")
    ap.add_argument("--json", dest="json_out", action="store_true",
                    help="stdout 只输出机器可读 JSON(人读文本走 stderr),供平台消费")
    a = ap.parse_args(argv)

    doc_path = Path(a.doc)
    if not doc_path.is_file():
        print(f"错误:文档不存在或不是文件:{doc_path}", file=sys.stderr)
        return 2
    answers: dict[str, str] | None = None
    deferred_seqs: list[str] = []
    if a.answers is not None:
        answers_path = Path(a.answers)
        if not answers_path.is_file():
            print(f"错误:answers 文件不存在或不是文件:{answers_path}", file=sys.stderr)
            return 2
        try:
            answers, deferred_seqs = parse_answers(answers_path)
        except ValueError as e:
            print(f"错误:{e}", file=sys.stderr)
            return 2
        if not answers:
            print(f"提示:{answers_path} 解析出 0 条(检查 seq 字段),qa-compare/p-semantic 按缺输入跳过", file=sys.stderr)
            answers = None

    doc = doc_path.read_text(encoding="utf-8")
    c = Checker(doc, answers, deferred_seqs)
    c.check_meta_header()
    c.check_qa_compare()
    c.check_fr()
    c.check_p_coverage()
    c.check_a_registry()
    c.check_strikes()
    c.check_scope_discipline()
    c.check_self_contained()
    c.check_failure_trigger()
    c.check_count_assert()
    c.check_matrix_assert()
    c.check_raw_json()
    c.check_p_semantic()
    c.check_deferred_link()
    order = {"FAIL": 0, "WARN": 1, "SKIP": 2, "PASS": 3}
    c.results.sort(key=lambda r: order[r[0]])

    fails = sum(1 for level, *_ in c.results if level == "FAIL")
    warns = sum(1 for level, *_ in c.results if level == "WARN")
    skips = sum(1 for level, *_ in c.results if level == "SKIP")

    if a.json_out:
        checks = []
        for level, name, details, data in c.results:
            item = {"name": name, "level": level, "details": details}
            if data is not None:
                item["data"] = data
            checks.append(item)
        fr_data = next((d for lv, n, _, d in c.results if n == "fr-continuity" and d), {"used": [], "missing": [], "gaps": []})
        as_data = next((d for lv, n, _, d in c.results if n == "a-registry" and d),
                       {"declared": [], "used": [], "noUse": [], "ghost": []})
        payload = {
            "summary": {"fail": fails, "warn": warns, "skip": skips, "pass": len(c.results) - fails - warns - skips},
            "checks": checks,
            "fr": fr_data,
            "assumptions": as_data,
        }
        sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return 1 if fails else 0

    print(f"== 标准需求文档机检 · {doc_path.name} ==", file=sys.stderr)
    for level, name, details, _ in c.results:
        mark = {"FAIL": "✗ FAIL", "WARN": "! WARN", "PASS": "✓ PASS", "SKIP": "- SKIP"}[level]
        print(f"\n[{mark}] {name}", file=sys.stderr)
        for d in details:
            print(f"  - {d}", file=sys.stderr)
    print(f"\n== 汇总:FAIL {fails} · WARN {warns} · SKIP {skips} ==", file=sys.stderr)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

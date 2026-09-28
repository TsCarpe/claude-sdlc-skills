#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sdlc-test 脚本共享件(guard_exec.py / verify_dev.py 内部 import,非 CLI)。

集中会各自演进的口径,防脚本级漂移:
  latest_by_name —— 按文件名日期/rN 取最新一份。三处复刻互相点名(跨 skill 不
    import,单独安装互相不可见):sdlc-gate 侧 scripts/check_trace.py 与
    scripts/guard_dev.py、sdlc-test 侧本文件——改口径须三处同步。
  header_kv —— 头部区块(首个 ## 标题前)表格行取值,防正文插行伪造状态。两处
    复刻互相点名:sdlc-test 侧本文件、sdlc-gate 侧 guard_dev.py 内联同款——
    改口径须两侧同步。
  SM_HEAD —— 冒烟条目标题(guard_exec 检查 5 计数与 verify_dev 解析同源)。
  tier_three_ways —— 风险分级三口径(原 guard_exec 检查 2.5 下沉,三头取值一律
    限头部取值域 tier_head_text/header_kv——正文独立净行「风险分级:C」不识别,
    防正文插行降级):
    cases.md 头为主源;整行缺失 → tier=None(调用方提示「按 A 级继续」不拦,存量兼容);
    存在但空/坏值/未分级 → 拦;digest 头与 cases 头均有值且不一致 → 拦,
    digest 头坏值/未分级同拦(digest 模板合法形态仅 A|B|C),digest 缺失记 note;
    review 最新 issues 头(表格行)有值但坏值或与 cases 头不一致 → 拦,
    目录无文件/无该字段/「未分级(按 A)」→ note 不拦
    (tier 只升不降,升级后须同步 cases/issues 头)。
"""
from __future__ import annotations

import re
from pathlib import Path

TIER_RE = re.compile(r"风险分级[：:]\s*([^\n（(]{1,20})")
# 冒烟条目标题:SM- 编号后至少一个空白,名称可空。guard_exec 检查 5 计数与
# verify_dev.parse_smoke 解析共用本定义——改口径须两侧同步(re.M 对逐行 match 无影响)。
# 空白只认同行 [ \t]:若用 \s,guard_exec 侧全文 findall 的空白可跨行吞下一行污染名称,
# 而裸标题 `## SM-01`(编号后无空白)在 verify_dev 侧逐行 match 不命中——两侧计数分叉
SM_HEAD = re.compile(r"^##[ \t]+(SM-\d+)[ \t]+(.*)$", re.M)


def latest_by_name(paths: list[Path]) -> Path | None:
    """按文件名中的日期/rN 序号取最新一份(verify-20260928.md、verify-20260928-r2.md)。

    三处复刻互相点名(跨 skill 不 import,单独安装互相不可见):sdlc-gate 侧
    check_trace.py 与 guard_dev.py、sdlc-test 侧本文件——改口径须三处同步。"""
    def key(p: Path):
        d = re.search(r"(\d{8})", p.name)
        r = re.search(r"-r(\d+)", p.name)
        return (d.group(1) if d else "0", int(r.group(1)) if r else 0)
    return max(paths, key=key) if paths else None


def header_text(text: str) -> str:
    """头部区块:首个 ##(含更深 ###/####)标题行之前的文本;无 ## 标题则全文件均为头部。

    单井号 # 标题不算分节(与 markdown 语义对齐——头部 kv 表常位于 # 主标题之下)。"""
    lines = text.splitlines(keepends=True)
    for i, ln in enumerate(lines):
        if ln.startswith("##"):
            return "".join(lines[:i])
    return text


def header_kv(text: str, field: str) -> str | None:
    """头部区块内找 `| 字段 | 值 |` 表格行取值;正文同名行不识别(防正文插行伪造状态)。

    两处复刻互相点名:sdlc-test 侧本文件、sdlc-gate 侧 guard_dev.py 内联同款
    (跨 skill 不 import,单独安装互相不可见)——行为须逐字一致,改口径须两侧同步。"""
    m = re.search(rf"\|\s*{re.escape(field)}\s*\|\s*([^\|]+)", header_text(text))
    return m.group(1).strip() if m else None


def tier_head_text(text: str) -> str:
    """风险分级取值文本域:头部区块(首 ## 前)+「## 头部元数据」节(存在时)。

    digest/issues 的取值行在首 ## 之前的引用头/表格头(header_text 即可覆盖);
    cases 按 case-template 把「- 风险分级:…」放在「## 头部元数据」小节下
    (首 ## 之后)——单用 header_text 会切掉合法分级行、全员误判「未标注按 A」。
    两处之外的正文明行(讨论文字/插行降级)不参与取值。"""
    head = header_text(text)
    m = re.search(r"^##\s*头部元数据\s*$", text, re.M)
    if m is None:
        return head
    rest = text[m.end():]
    nxt = re.search(r"^##\s", rest, re.M)
    return head + "\n" + (rest[:nxt.start()] if nxt else rest)


def latest_digest(root: Path, req: str) -> Path | None:
    intake = root / "sdlc" / req / "intake"
    digests = sorted(intake.glob("digest-*.md")) if intake.is_dir() else []
    return latest_by_name(digests)


def git_head(root: Path) -> str:
    """当前 HEAD 短哈希;无 git / 失败时返回「未知(无 git,降级)」。"""
    import subprocess
    try:
        p = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root,
                           capture_output=True, timeout=15)
        if p.returncode == 0:
            return p.stdout.decode("utf-8", "replace").strip()
    except Exception:
        pass
    return "未知(无 git,降级)"


def parse_tier_value(raw: str) -> str | None:
    """风险分级值解析(全串校验,不做首字符截断):截括号注释/破折号注释、剥尖括号后,
    须精确为 A/B/C(允许「A 级」单字后缀);「未分级」前缀单列(issue 模板合法写法,
    由调用方按场景处理);AB / C+ / A|B|C 等多字符杂值 → None(坏值)。"""
    v = re.split(r"[（(]", raw.strip(), 1)[0]
    v = re.split(r"[—\-]{2,}", v, 1)[0].strip().strip("<>").strip()
    if v.startswith("未分级"):
        return "未分级"
    m = re.fullmatch(r"([ABC])\s*级?", v)
    return m.group(1) if m else None


def tier_three_ways(cases_text: str, digest_path: Path | None,
                    review_dir: Path | None = None) -> tuple[str | None, list[str], list[str]]:
    """风险分级三口径:cases 头(主源)+ digest 头 + review 最新 issues 头(表格行)。

    返回 (tier, notes, errors):tier=None 表示未标注或坏值(调用方按场景处理)。
      cases 头:整行缺失 → note 按A级继续;空/坏值/未分级 → error;
      digest 头:文件缺失 → note 不参与比对;有值但坏值/未分级 → error(与 cases/review
      头坏值口径统一,digest 模板合法形态仅 A|B|C);合法但与 cases 头不一致 → error;
      review 最新 issues 头:目录无文件/无该字段/「未分级(按 A)」→ note 不拦;
      有值但坏值、或与 cases 头不一致 → error(tier 只升不降,升级后须同步三头)。
    三头取值一律限头部取值域(cases/digest 经 tier_head_text——首 ## 前的头部区块
    加「## 头部元数据」节;review 经 header_kv 限首 ## 前)——正文独立净行
    「风险分级:C」不识别,防正文插行降级。"""
    notes: list[str] = []
    errors: list[str] = []
    m = TIER_RE.search(tier_head_text(cases_text))
    if not m:
        return None, ["cases.md 头部未标注风险分级——按 A 级继续(存量兼容;建议补标)"], errors
    tier = parse_tier_value(m.group(1))
    if tier is None or tier == "未分级":
        errors.append(f"cases.md 头部「风险分级」值非法:{m.group(1).strip()!r}(合法:A | B | C,单值)")
        return None, notes, errors
    if digest_path is not None and digest_path.is_file():
        dtext = digest_path.read_text(encoding="utf-8", errors="replace")
        md = TIER_RE.search(tier_head_text(dtext))
        if md:
            td = parse_tier_value(md.group(1))
            if td is None or td == "未分级":
                errors.append(f"digest 头「风险分级」值非法:{md.group(1).strip()!r}(合法:A | B | C,单值)")
            elif td != tier:
                errors.append(f"digest 头「风险分级」= {td} 与 cases 头 = {tier} 不一致——"
                              f"tier 只升不降,升级后须同步 cases/issues 头(以 digest 为准修正后重跑)")
    else:
        notes.append("digest 缺失，未参与三头比对")
    if review_dir is not None:
        rfiles = sorted(review_dir.glob("*.md")) if review_dir.is_dir() else []
        latest = latest_by_name(rfiles) if rfiles else None
        if latest is None:
            notes.append("review/ 无 issues 文件——风险分级第三口径跳过(不拦)")
        else:
            raw = header_kv(latest.read_text(encoding="utf-8", errors="replace"), "风险分级")
            if raw is None:
                notes.append(f"review 最新一份({latest.name})头部无「风险分级」行——第三口径跳过(不拦)")
            else:
                rt = parse_tier_value(raw)
                if rt is None:
                    errors.append(f"issues 头「风险分级」值非法:{raw!r}(合法:A | B | C,单值;"
                                  f"未分级写「未分级(按 A)」不拦)")
                elif rt == "未分级":
                    notes.append(f"issues 头「风险分级」= 未分级(按 A)——cases 头为 {tier},"
                                 f"建议评审后同步定级(不拦)")
                elif rt != tier:
                    errors.append(f"issues 头「风险分级」= {rt} 与 cases 头 = {tier} 不一致——"
                                  f"tier 只升不降,升级后须同步 cases/issues 头(修正后重跑)")
    return tier, notes, errors

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sdlc-gate 开发放行守卫(开发入口拦截)。

下沉自 SKILL.md Step 5「放行后才允许进入开发」——任务框架或协作文档对设计的
人工 ack(确认点③、飞书技术文档确认等)是流程性定稿信号,不构成质量放行;
质量放行唯一口径 = sdlc-gate issues 头部「评审状态 = 已放行」。本脚本把该
口径机械化为开发入口拦截,防止 ack 被当成放行信号直接开码。

用法:
    python3 guard_dev.py <项目根> <需求名>

检查项(不通过 exit 1,缺失清单直出):
  1. sdlc/<需求名>/review/ 存在且含 .md;无 issues 时允许走显式豁免(见 4)
  2. 最新一份 issues(latest_by_name 三处复刻互相点名:同目录内 check_trace.py
     与本文件两处、sdlc-test 侧 scripts/_shared.py——跨 skill
     不 import,单独安装互相不可见,改口径须三处同步)头部「评审状态」= 已放行;
     待裁决 / 字段缺失均拒。状态行仅认头部区块(首个 ## 标题前,header_kv),
     正文插「已放行」行不识别——该函数与 _shared.header_kv 两处复刻,改口径须两侧同步
  3. P1-9:A/B 级头部 reviewMode=degraded(降级单会话)拒放行——该档位必须外置
     runner 全新上下文扇出;未标注 reviewMode 的存量产物按旧格式放行
  4. 用户显式豁免: review/exemptions/exemption-<日期>.md 七字段齐全,
     且「基线」= 最新 issues 文件名(无 issues 时写「无」)。基线不匹配 =
     旧豁免已失效。豁免只解锁开发;sdlc-test static/exec 仍需关卡1
  5. A/B 级 degraded 即使有豁免也不放行(豁免不能绕过该档位)

降级边界:脚本不可得(无 python3)时人工核对最新 issues 头部「评审状态」;
review/ 下非模板产出的手写文件若恰为最新份,按「评审状态字段缺失」如实拒绝。
存量兼容:r1 已放行后因实质变更开了 r2(待裁决)时本守卫拦截——完成 r2
裁决放行,或 r2 误开时将其移出 review/ 后重跑(见拒绝文案)。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

OK, NG, WARN = "✅", "🔴", "⚠️"

# 豁免头部七字段(与 references/exemption-template.md 逐字对应;改口径须两侧同步)
EXEMPTION_FIELDS = ("豁免类型", "基线", "范围", "理由", "确认人", "确认日期", "风险自担")


def latest_by_name(paths: list[Path]) -> Path | None:
    """按文件名中的日期/rN 序号取最新一份(三处复刻互相点名,改口径须三处同步:
    同目录内 check_trace.py 与本文件两处 + sdlc-test 侧 scripts/_shared.py)。"""
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

    两处复刻互相点名:sdlc-test 侧 scripts/_shared.py、sdlc-gate 侧本文件内联同款
    (跨 skill 不 import,单独安装互相不可见)——行为须逐字一致,改口径须两侧同步。"""
    m = re.search(rf"\|\s*{re.escape(field)}\s*\|\s*([^\|]+)", header_text(text))
    return m.group(1).strip() if m else None


def tier_and_mode(text: str) -> tuple[str, str | None]:
    """读 issues 头部风险分级与 reviewMode;无风险分级按 A 级(存量保守口径)。"""
    tier_raw = (header_kv(text, "风险分级") or "").strip()
    tier = tier_raw[:1].upper() if tier_raw[:1].upper() in ("A", "B", "C") else "A"
    return tier, header_kv(text, "reviewMode")


def exemption_fail(msgs: list[str]) -> int:
    print(NG + " 开发放行守卫拒绝进入开发(豁免校验未通过):")
    for m in msgs:
        print("  - " + m)
    print("(补救:按 sdlc/<需求名>/review/exemptions/exemption-<YYYYMMDD>.md 模板"
          "(七字段见 references/exemption-template.md)补齐后重跑;豁免只解锁开发,"
          "sdlc-test static/exec 仍需关卡1人工确认 cases 或 gate 放行)")
    return 1


def fail(msgs: list[str], hint_exemption: bool = True) -> int:
    print(NG + " 开发放行守卫拒绝进入开发,先处理以下问题:")
    for m in msgs:
        print("  - " + m)
    tail = ("若已获人工豁免,写 review/exemptions/exemption-<YYYYMMDD>.md"
            "(七字段见 references/exemption-template.md)后重跑"
            if hint_exemption else
            "A/B 级 degraded 不接受豁免绕过,须重跑外置 runner 扇出;处理后重跑本命令")
    print("(补救:完成 sdlc-gate Step 4 逐条裁决并过 --release 闭环校验后,"
          "将最新 issues 头部「评审状态」置「已放行(日期)」;若因实质变更开了新一轮"
          "(r2 待裁决),完成该轮裁决放行,或确认误开后将其移出 review/ 目录;"
          "设计的人工 ack 只是定稿信号,不替代评审放行。" + tail + ")")
    return 1


def check_exemption(path: Path, latest_issues_name: str) -> tuple[bool, str, list[str]]:
    """校验豁免文件;返回 (是否通过, 摘要, 问题清单)。"""
    text = path.read_text(encoding="utf-8", errors="replace")
    missing = [f for f in EXEMPTION_FIELDS if not (header_kv(text, f) or "").strip()]
    if missing:
        return False, "", [f"豁免字段缺失:{path.name} 缺 {', '.join(missing)}——"
                           f"按 references/exemption-template.md 补齐七字段"]
    typ = (header_kv(text, "豁免类型") or "").strip()
    if not typ.startswith("开发放行"):
        return False, "", [f"豁免类型非法:{path.name}「豁免类型」= {typ!r}——须以「开发放行」开头"]
    risk = (header_kv(text, "风险自担") or "").strip()
    if not risk.startswith("是"):
        return False, "", [f"风险自担未确认:{path.name}「风险自担」= {risk!r}——须以「是」开头"]
    baseline = (header_kv(text, "基线") or "").strip()
    if baseline != latest_issues_name:
        return False, "", [f"豁免基线不匹配:{path.name}「基线」= {baseline!r},"
                           f"最新 issues = {latest_issues_name!r}——旧豁免已失效,"
                           f"按最新产物重新确认并写新豁免"]
    scope = (header_kv(text, "范围") or "").strip()
    who = (header_kv(text, "确认人") or "").strip()
    return True, f"{path.name}(类型={typ},范围={scope},确认人={who})", []


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    root, req = Path(sys.argv[1]).resolve(), sys.argv[2]
    review_dir = root / "sdlc" / req / "review"
    # 只扫 review/*.md(issues);exemptions/ 是子目录,不参与 issues 最新份判定
    files = sorted(review_dir.glob("*.md")) if review_dir.is_dir() else []
    latest = latest_by_name(files)
    latest_name = latest.name if latest else "无"
    latest_val = None

    if latest is not None:
        text = latest.read_text(encoding="utf-8", errors="replace")
        latest_val = header_kv(text, "评审状态")
        tier, mode = tier_and_mode(text)
        # A/B 级 degraded 不构成质量放行,且不允许豁免绕过(先于放行/豁免判定)
        if tier in ("A", "B") and mode == "degraded":
            return fail([f"{tier} 级评审为降级单会话:{latest.name} 头部 reviewMode=degraded——"
                         f"A/B 必须由外置 runner 的全新上下文子代理扇出(A=4/B=2);"
                         f"用外置 runner 重跑评审并重新生成 issues 后再放行"
                         f"(该档位不接受豁免绕过)"], hint_exemption=False)
        if latest_val is not None and latest_val.startswith("已放行"):
            print(f"{OK} 开发放行守卫通过:{latest.name} 评审状态={latest_val}")
            return 0

    # 走到这里:无 issues / 未放行 / 状态字段缺失——查最新一份显式豁免
    ex_dir = review_dir / "exemptions"
    ex_files = sorted(ex_dir.glob("exemption-*.md")) if ex_dir.is_dir() else []
    ex = latest_by_name(ex_files)
    if ex is None:
        if latest is None:
            rel = f"sdlc/{req}/review"
            return fail([f"未做评审关口:{rel} 不存在或为空——先完成 sdlc-gate Step 1-3 生成 issues,"
                         f"走完裁决与放行后再启动开发"])
        if latest_val is None:
            return fail([f"评审状态字段缺失:{latest.name} 头部无「评审状态」行——"
                         f"非 issues 模板产物;按 issue-template 重产,或修正 review/ 目录文件命名"])
        return fail([f"评审关口未放行:{latest.name} 头部「评审状态」= {latest_val!r}——"
                     f"先完成 sdlc-gate 逐条裁决(Step 4)与放行闭环(Step 5);"
                     f"设计的人工 ack(确认点③/协作文档确认)只是定稿信号,不构成放行"])

    ok, summary, msgs = check_exemption(ex, latest_name)
    if not ok:
        return exemption_fail(msgs)
    print(f"{WARN} 开发放行守卫以显式豁免放行:{summary}")
    print(f"{WARN} 豁免只解锁开发;sdlc-test static/exec 仍需关卡1(人工确认 cases 或 gate 已放行)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

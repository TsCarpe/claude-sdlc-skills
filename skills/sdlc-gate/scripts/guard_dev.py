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
  1. sdlc/<需求名>/review/ 存在且含 .md——否则视为未做评审关口
  2. 最新一份 issues(latest_by_name 三处复刻互相点名:同目录内 check_trace.py
     与本文件两处、sdlc-test 侧 scripts/_shared.py——跨 skill
     不 import,单独安装互相不可见,改口径须三处同步)头部「评审状态」= 已放行;
     待裁决 / 字段缺失均拒。状态行仅认头部区块(首个 ## 标题前,header_kv),
     正文插「已放行」行不识别——该函数与 _shared.header_kv 两处复刻,改口径须两侧同步

降级边界:脚本不可得(无 python3)时人工核对最新 issues 头部「评审状态」;
review/ 下非模板产出的手写文件若恰为最新份,按「评审状态字段缺失」如实拒绝。
存量兼容:r1 已放行后因实质变更开了 r2(待裁决)时本守卫拦截——完成 r2
裁决放行,或 r2 误开时将其移出 review/ 后重跑(见拒绝文案)。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

OK, NG = "✅", "🔴"


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


def fail(msgs: list[str]) -> int:
    print(NG + " 开发放行守卫拒绝进入开发,先处理以下问题:")
    for m in msgs:
        print("  - " + m)
    print("(补救:完成 sdlc-gate Step 4 逐条裁决并过 --release 闭环校验后,"
          "将最新 issues 头部「评审状态」置「已放行(日期)」;若因实质变更开了新一轮"
          "(r2 待裁决),完成该轮裁决放行,或确认误开后将其移出 review/ 目录;"
          "设计的人工 ack 只是定稿信号,不替代评审放行。处理后重跑本命令)")
    return 1


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    root, req = Path(sys.argv[1]).resolve(), sys.argv[2]
    review_dir = root / "sdlc" / req / "review"
    files = sorted(review_dir.glob("*.md")) if review_dir.is_dir() else []
    if not files:
        rel = f"sdlc/{req}/review"
        return fail([f"未做评审关口:{rel} 不存在或为空——先完成 sdlc-gate Step 1-3 生成 issues,"
                     f"走完裁决与放行后再启动开发"])
    latest = latest_by_name(files)
    text = latest.read_text(encoding="utf-8", errors="replace")
    val = header_kv(text, "评审状态")
    if val is None:
        return fail([f"评审状态字段缺失:{latest.name} 头部无「评审状态」行——"
                     f"非 issues 模板产物;按 issue-template 重产,或修正 review/ 目录文件命名"])
    if not val.startswith("已放行"):
        return fail([f"评审关口未放行:{latest.name} 头部「评审状态」= {val!r}——"
                     f"先完成 sdlc-gate 逐条裁决(Step 4)与放行闭环(Step 5);"
                     f"设计的人工 ack(确认点③/协作文档确认)只是定稿信号,不构成放行"])
    print(f"{OK} 开发放行守卫通过:{latest.name} 评审状态={val}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

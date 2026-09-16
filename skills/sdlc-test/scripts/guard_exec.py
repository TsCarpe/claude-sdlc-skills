#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sdlc-test 关卡守卫（exec / static 入口前置校验）。

下沉自 SKILL.md「关卡强制」文字规则：模型调用入口命令时必然触发，
状态判定由脚本完成，不再依赖模型读头部后自觉拒绝。

用法：
    python3 guard_exec.py <项目根> <需求名> <exec|static>

检查项（不通过 exit 1，缺失清单直出）：
  1. sdlc/<需求名>/test/cases.md 存在
  2. 关卡1：cases.md 头部「审核状态」以「已确认」开头；
     或 sdlc/<需求名>/review/*.md 的「评审状态」= 已放行（sdlc-gate 关卡互认）
  3. 轮次目录命名：reports/ 下目录须为 YYYYMMDD-r<N>（小写 r）
  4. spec 一致性（防 R3 型丢失）：cases.md 中标注 spec ✓ 的用例条目存在时，
     test/specs/*.spec.ts 必须非空——标注在而资产丢，回归轮两步会静默跳过这些用例
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

OK, NG = "✅", "🔴"


def fail(msgs: list[str]) -> int:
    print(NG + " 关卡守卫拒绝执行，先处理以下问题：")
    for m in msgs:
        print("  - " + m)
    print("（关卡1 补救：人工审核用例后将 cases.md 头部「审核状态」改为「已确认（日期）」；"
          "或完成 sdlc-gate 裁决使「评审状态=已放行」。处理后重跑本命令）")
    return 1


def main() -> int:
    if len(sys.argv) != 4 or sys.argv[3] not in ("exec", "static"):
        print(__doc__)
        return 2
    root, req, phase = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3]
    test_dir = root / "sdlc" / req / "test"
    cases = test_dir / "cases.md"
    msgs: list[str] = []

    # 1. cases.md 存在
    if not cases.is_file():
        return fail([f"用例文件不存在：{cases.relative_to(root)}——先跑 cases 生成用例"])

    text = cases.read_text(encoding="utf-8", errors="replace")

    # 2. 关卡1（含 sdlc-gate 互认）
    m = re.search(r"审核状态[：:]\s*(.+)", text)
    confirmed = bool(m and m.group(1).strip().startswith("已确认"))
    if not confirmed:
        released = False
        review_dir = root / "sdlc" / req / "review"
        if review_dir.is_dir():
            for rfile in sorted(review_dir.glob("*.md")):
                if re.search(r"\|\s*评审状态\s*\|\s*已放行", rfile.read_text(encoding="utf-8", errors="replace")):
                    released = True
                    break
        if released:
            print(f"{OK} 关卡1 通过（sdlc-gate 互认：评审状态=已放行）")
        else:
            msgs.append(f"关卡1 未过：cases.md 头部「审核状态」= {m.group(1).strip() if m else '（字段缺失）'}"
                        f"，且 review/ 无「评审状态=已放行」")

    # 3. 轮次目录命名（exec 与 static 同口径）
    reports = test_dir / "reports"
    if reports.is_dir():
        bad = [d.name for d in reports.iterdir()
               if d.is_dir() and not re.fullmatch(r"\d{8}-r\d+", d.name)]
        if bad:
            msgs.append(f"轮次目录命名违规（须 YYYYMMDD-r<N> 小写 r）：{', '.join(bad)}")

    # 4. spec 标注一致性（防资产丢失后标注失真）
    if re.search(r"spec\s*✓", text):
        specs_dir = test_dir / "specs"
        spec_files = list(specs_dir.glob("*.spec.ts")) if specs_dir.is_dir() else []
        if not spec_files:
            msgs.append("cases.md 存在「spec ✓」标注但 specs/ 无任何 .spec.ts——"
                        "资产丢失（R3 型失真），回归轮两步会静默跳过这些用例；先重跑 spec 资产化或清除失真标注")

    if msgs:
        return fail(msgs)
    print(f"{OK} 关卡守卫通过（{phase}，审核状态与资产一致性就绪）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

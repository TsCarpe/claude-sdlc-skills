#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""runner 命令形态一致性校验（claude-sdlc-skills 仓自检）。

红线来源（本地版为准）：skills/sdlc-test/references/spec/spec-guide.md
「runner 执行纪律」——调用形态必须绝对路径二进制 + 绝对路径 config；
cd+npx 三形态实测不可靠；路径过滤禁 ../../ 相对前缀。

豁免（有意保留，勿报）：
  - `npx playwright install`（安装命令，env-template）
  - spec-guide.md 内红线自带的反例引文（含「实测不可靠」）——仅限该文件，
    其它文件写「实测不可靠」不豁免（防借豁免词洗白违规行）

用法：
    python3 scripts/check_runner_form.py <仓根> [--out <报告路径>]
退出码：0 = 基线干净；1 = 有违形态（基线应为 0，09-14 三度复核后定型）；
2 = 用法错误（参数个数不对 / 仓根非目录——曾致 rglob 扫空报告假绿）
"""
from __future__ import annotations

import re
import sys
import datetime
from pathlib import Path

VIOLATIONS = [
    (re.compile(r"npx\s+playwright\s+(?!install)"), "npx playwright <cmd> 形态（须绝对路径二进制）"),
    (re.compile(r"cd\s+[^\n|>]*&&[^\n]*playwright"), "cd ... && playwright 形态（cwd 不持久，红线禁用）"),
    (re.compile(r"--config\s+\.\./"), "--config 相对路径前缀（禁 ../../）"),
]
EXEMPT_INSTALL = re.compile(r"npx\s+playwright\s+install")  # 任意文件：安装命令
EXEMPT_SPECGUIDE = re.compile(r"实测不可靠")  # 仅 spec-guide.md：红线自带反例引文
SPEC_GUIDE = "skills/sdlc-test/references/spec/spec-guide.md"


def main() -> int:
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    out_path = None
    if "--out" in sys.argv:
        if sys.argv.index("--out") + 1 >= len(sys.argv):
            print("🔴 --out 缺少参数值（用法：check_runner_form.py <仓根> [--out <报告路径>]）")
            return 2
        out_path = Path(sys.argv[sys.argv.index("--out") + 1])
    if not argv:
        print(__doc__)
        return 2
    root = Path(argv[0]).resolve()
    if not root.is_dir():
        # 位置参数错位（如 --out 前置把报告路径顶进 root）或路径写错时，
        # rglob 扫空会给出「0 违规」假绿——必须在扫描前拦下
        print(f"🔴 仓根不是目录：{root}（--out 须尾置：check_runner_form.py <仓根> [--out <报告路径>]）")
        return 2

    hits: list[tuple[str, int, str]] = []
    files = sorted(root.rglob("*.md"))
    for f in files:
        in_spec_guide = f.relative_to(root).as_posix() == SPEC_GUIDE
        for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if EXEMPT_INSTALL.search(line):
                continue
            if in_spec_guide and EXEMPT_SPECGUIDE.search(line):
                continue
            for pat, desc in VIOLATIONS:
                if pat.search(line):
                    hits.append((f.relative_to(root).as_posix(), i, desc))

    lines = [
        "# runner 命令形态一致性校验",
        "",
        f"> {datetime.date.today()} ｜ 扫描 {len(files)} 个 md ｜ 红线：spec-guide「runner 执行纪律」（绝对路径二进制形态）",
        "",
    ]
    if hits:
        lines.append(f"🔴 违形态 {len(hits)} 处：")
        lines.extend(f"- {f}:{i} {d}" for f, i, d in hits)
        verdict = 1
    else:
        lines.append("✅ 基线 0 违规（豁免：npx install 安装命令、spec-guide 反例引文）")
        verdict = 0
    report = "\n".join(lines) + "\n"
    print(report, end="")
    if out_path:
        out_path.write_text(report, encoding="utf-8")
        print(f"\n（已落档 {out_path}）")
    return verdict


if __name__ == "__main__":
    sys.exit(main())

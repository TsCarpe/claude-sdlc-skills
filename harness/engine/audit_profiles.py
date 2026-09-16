#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OVAL 分组对账审计（scan 专用，不挂 hook）。

checklist §2.2「漏一层则该层完全不设防」的分组级版本：
Controller 的 @Validate("x") 若没有任何 Req 字段的 profiles 引用 x，
该接口的 OVAL 校验整体空转（请求进来什么都不校验）。

用法：
    python3 audit_profiles.py <repo_root>

输出：
    悬空分组（@Validate 有值、全项目 profiles 无定义）——高危，按文件列出
    未使用分组（profiles 有定义、无任何 @Validate 引用）——低危提示
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SKIP_PARTS = ("/target/", "/.git/", "/node_modules/", "/.trellis/", "/sdlc/")

RE_VALIDATE = re.compile(r'@Validate\("([^"]+)"\)')
RE_PROFILES = re.compile(r'profiles\s*=\s*(\{[^}]*\}|"[^"]*")')


def main() -> int:
    root = Path(sys.argv[1]).resolve()
    used: dict[str, list[str]] = {}    # 分组名 -> [Controller 文件,...]
    defined: dict[str, list[str]] = {}  # 分组名 -> [Req 文件,...]

    for p in root.rglob("*.java"):
        s = str(p)
        if any(part in s for part in SKIP_PARTS):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(p.relative_to(root))
        for m in RE_VALIDATE.finditer(text):
            used.setdefault(m.group(1), []).append(rel)
        for m in RE_PROFILES.finditer(text):
            for v in re.findall(r'"([^"]+)"', m.group(1)):
                if v:
                    defined.setdefault(v, []).append(rel)

    dangling = sorted(set(used) - set(defined))
    orphan = sorted(set(defined) - set(used))

    print(f"=== OVAL 分组对账（@Validate ↔ profiles）===")
    print(f"@Validate 引用分组 {len(used)} 个 | profiles 定义分组 {len(defined)} 个\n")

    if dangling:
        print(f"🔴 悬空分组 {len(dangling)} 个（接口校验空转，高危）：")
        for v in dangling:
            files = ", ".join(sorted(set(used[v]))[:3])
            more = f" 等{len(set(used[v]))}处" if len(set(used[v])) > 3 else ""
            print(f"  - {v}  ← {files}{more}")
    else:
        print("✅ 无悬空分组")

    if orphan:
        print(f"\n🟡 定义未使用分组 {len(orphan)} 个（低危，可能是废代码或拼写不一致）：")
        for v in orphan[:20]:
            files = ", ".join(sorted(set(defined[v]))[:2])
            print(f"  - {v}  ← {files}")
        if len(orphan) > 20:
            print(f"  ... 其余 {len(orphan) - 20} 个略")

    return 1 if dangling else 0


if __name__ == "__main__":
    sys.exit(main())

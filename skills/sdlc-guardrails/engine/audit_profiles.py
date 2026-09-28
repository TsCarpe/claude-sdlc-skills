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
    非字面量引用（@Validate(Consts.X) / profiles = Consts.X）——静态不可解析，
    计数提示不纳入对账，也不据其误判悬空

退出码：0 = 无悬空；1 = 有悬空分组；2 = 用法错误；3 = 内部错误
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SKIP_PARTS = ("/target/", "/.git/", "/node_modules/", "/.trellis/", "/sdlc/")

# @Validate 参数体：容忍换行空白与 单值/数组/数组构造 形态
# （@Validate("x") / @Validate(\n "x"\n) / @Validate({"x"}) / @Validate({"x","y"}) / @Validate(new String[]{"x"})）
RE_VALIDATE = re.compile(r'@Validate\(\s*(?:new\s+\w+\s*\[\s*\]\s*)?(?:\{[^}]*\}|"[^"]*")\s*\)')
# profiles 赋值字面量右值：同上容忍数组构造前缀；非常量形态由 RE_*_NONLIT 单独计数
RE_PROFILES = re.compile(r'profiles\s*=\s*(?:new\s+\w+\s*\[\s*\]\s*)?(\{[^}]*\}|"[^"]*")')
# 非字面量引用（常量/表达式）：右值不以字面量开头 → 无法静态解析，只计数不纳入对账
RE_VALIDATE_NONLIT = re.compile(r'@Validate\(\s*(?!\s*(?:new\s+\w+\s*\[\s*\]\s*)?[{"])')
RE_PROFILES_NONLIT = re.compile(r'profiles\s*=\s*(?!\s*(?:new\s+\w+\s*\[\s*\]\s*)?[{"])')


def main() -> int:
    if len(sys.argv) != 2:
        print("用法：python3 audit_profiles.py <repo_root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"🔴 目录不存在：{root}", file=sys.stderr)
        return 2
    used: dict[str, list[str]] = {}    # 分组名 -> [Controller 文件,...]
    defined: dict[str, list[str]] = {}  # 分组名 -> [Req 文件,...]
    nonlit = {"@Validate": 0, "profiles": 0}

    try:
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
                for v in re.findall(r'"([^"]+)"', m.group(0)):
                    used.setdefault(v, []).append(rel)
            for m in RE_PROFILES.finditer(text):
                for v in re.findall(r'"([^"]+)"', m.group(1)):
                    if v:
                        defined.setdefault(v, []).append(rel)
            nonlit["@Validate"] += len(RE_VALIDATE_NONLIT.findall(text))
            nonlit["profiles"] += len(RE_PROFILES_NONLIT.findall(text))
    except OSError as e:
        print(f"🔴 扫描中断（内部错误）：{e}", file=sys.stderr)
        return 3

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

    total_nonlit = nonlit["@Validate"] + nonlit["profiles"]
    if total_nonlit:
        print(f"\n⚠️ 非字面量引用 {total_nonlit} 处（@Validate {nonlit['@Validate']} / "
              f"profiles {nonlit['profiles']}），未纳入对账——常量分组静态不可解析，"
              f"悬空/未使用结论可能因此失真，建议人工抽检")

    return 1 if dangling else 0


if __name__ == "__main__":
    sys.exit(main())

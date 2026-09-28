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
     或 sdlc/<需求名>/review/ 最新一份 issues（latest_by_name，v0.12.0 起
     由「任一份」改为最新份——r1 已放行后开 r2 待裁决时不再误放行）的
     「评审状态」= 已放行（sdlc-gate 关卡互认）
  2.5 风险分级三口径（经 _shared.tier_three_ways，与 verify_dev.py 同源）：
     整行缺失 → 提示「按 A 级继续」不拦（存量兼容）；
     存在但空/坏值/非 A|B|C → 拦；digest 头与 cases 头均有值且不一致 → 拦；
     review 最新 issues 头有值但坏值或与 cases 头不一致 → 拦，
     目录无文件/无该字段/「未分级(按 A)」→ note 不拦
     （tier 只升不降，升级后须同步 cases/issues/digest 头三处一致）
  3. 轮次目录命名：reports/ 下目录须为 YYYYMMDD-r<N>（小写 r）
  4. spec 一致性（防 R3 型丢失）：cases.md 中标注 spec ✓ 的用例条目存在时，
     test/specs/*.spec.ts 必须非空——标注在而资产丢，回归轮两步会静默跳过这些用例
  5. 开发完成验证（留档反查 + 交叉校验，一律拦、老需求补跑一次即过）：
     dev/verify-*.md 最新一份头部「验证状态」= 通过（「通过(人工降级,…))」
     形态放行但显式 ⚠️ 警示）；留档字段读取一律限定头部区块（首个 ## 标题前，
     经 _shared.header_kv——正文插行伪造状态不识别）；交叉校验四项——验证时
     HEAD ≠ 当前 HEAD → 拦（代码已变更，验证过期）；local 模式须有同轮
     boot-*.log（优先读留档头部「boot 日志」字段，旧留档缺失时按文件名
     verify-→boot- 推导）；A/B 级留档冒烟明细条数 = smoke.md 条数（条目标题
     口径经 _shared.SM_HEAD，与 verify_dev.parse_smoke 同源）；C 级留档遇
     A/B 分级 → 拦（tier 已升级）
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import _shared

OK, NG = "✅", "🔴"


def fail(msgs: list[str], hints: list[str] | None = None) -> int:
    print(NG + " 关卡守卫拒绝执行，先处理以下问题：")
    for m in msgs:
        print("  - " + m)
    for h in (hints or []):
        print(h)
    return 1


def strip_fences(text: str) -> str:
    """剥离四反引号围栏块(verify_dev 留档用 ```` 包命令/日志输出尾部,围栏行固定
    无缩进):围栏内形如 `| SM-xx | … |` 的构建/回归日志引用行不参与留档反查计数。"""
    return re.sub(r"(?ms)^````\n.*?\n````$", "", text)


def main() -> int:
    if len(sys.argv) != 4 or sys.argv[3] not in ("exec", "static"):
        print(__doc__)
        return 2
    root, req, phase = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3]
    test_dir = root / "sdlc" / req / "test"
    cases = test_dir / "cases.md"
    msgs: list[str] = []
    hints: list[str] = []
    gate1_failed = dev_failed = False

    # 1. cases.md 存在
    if not cases.is_file():
        return fail([f"用例文件不存在：{cases.relative_to(root)}——先跑 cases 生成用例"])

    text = cases.read_text(encoding="utf-8", errors="replace")

    # 2. 关卡1（含 sdlc-gate 互认；v0.12.0 起互认锚定最新一份 issues）
    review_dir = root / "sdlc" / req / "review"
    m = re.search(r"审核状态[：:]\s*(.+)", text)
    confirmed = bool(m and m.group(1).strip().startswith("已确认"))
    if not confirmed:
        rfiles = sorted(review_dir.glob("*.md")) if review_dir.is_dir() else []
        latest = _shared.latest_by_name(rfiles) if rfiles else None
        released, rel_name = False, ""
        if latest is not None:
            val = _shared.header_kv(latest.read_text(encoding="utf-8", errors="replace"), "评审状态")
            released = bool(val and val.startswith("已放行"))
            rel_name = latest.name
        if released:
            print(f"{OK} 关卡1 通过（sdlc-gate 互认：{rel_name} 评审状态=已放行）")
        else:
            gate1_failed = True
            msgs.append(f"关卡1 未过：cases.md 头部「审核状态」= {m.group(1).strip() if m else '（字段缺失）'}"
                        f"，且 review/ 最新一份{'（' + rel_name + '）' if rel_name else ''}无「评审状态=已放行」"
                        f"——若因实质变更开了新一轮，完成该轮裁决放行，或确认误开后将其移出 review/")

    # 2.5 风险分级（三口径：cases 头 + digest 头 + review 最新 issues 头，经 _shared 与 verify_dev.py 同源）
    tier, notes, terrs = _shared.tier_three_ways(text, _shared.latest_digest(root, req), review_dir)
    msgs += terrs
    for n in notes:
        print(f"{OK} {n}")
    tier_now = tier or "A"

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

    # 5. 开发完成验证（留档反查 + 交叉校验；老需求无留档一律拦，补跑一次即过）
    dev_dir = root / "sdlc" / req / "dev"
    verifies = sorted(dev_dir.glob("verify-*.md")) if dev_dir.is_dir() else []
    if not verifies:
        dev_failed = True
        msgs.append("开发完成验证未跑：sdlc/<需求名>/dev/ 下无 verify-*.md——"
                    "先运行 /sdlc-test dev（或 python3 <skill 目录>/scripts/verify_dev.py <项目根> <需求名>）")
    else:
        v = _shared.latest_by_name(verifies)
        vtext = v.read_text(encoding="utf-8", errors="replace")

        def kv(field: str) -> str | None:
            # 头部区块限定（首个 ## 标题前，经 _shared.header_kv）：正文插行伪造状态不识别，
            # 与 sdlc-gate 侧 guard_dev.py 内联同款行为一致（两处复刻，改口径须两侧同步）
            return _shared.header_kv(vtext, field)

        vstatus = kv("验证状态")
        if vstatus is None:
            dev_failed = True
            msgs.append(f"开发完成验证留档异常：{v.name} 头部无「验证状态」行——按 verify_dev.py 重新生成")
        elif not vstatus.startswith("通过"):
            dev_failed = True
            msgs.append(f"开发完成验证未过：{v.name} 头部「验证状态」= {vstatus!r}——"
                        f"按留档失败步修复后重跑 verify_dev.py 生成新轮次留档")
        else:
            if "人工降级" in vstatus:
                print(f"⚠️ 注意：{v.name} 为人工降级验证（非机器执行留档）——请知悉后继续")
            # 交叉校验 a：HEAD 比对（代码变更后旧验证过期）
            vhead, cur_head = kv("验证时 HEAD"), _shared.git_head(root)
            if (vhead and cur_head and "未知" not in vhead and "未知" not in cur_head
                    and vhead != cur_head):
                dev_failed = True
                msgs.append(f"开发完成验证过期：{v.name} 验证时 HEAD={vhead} ≠ 当前 HEAD={cur_head}"
                            f"——代码已变更，重跑 verify_dev.py")
            # 交叉校验 b：local 模式须有同轮 boot 日志（优先读留档头部「boot 日志」字段，
            # 旧留档无该字段时按文件名 verify-→boot- 推导，兼容）
            if (kv("启动模式") or "") == "local":
                boot_name = kv("boot 日志") or (v.stem.replace("verify-", "boot-") + ".log")
                boot_log = dev_dir / boot_name
                if not boot_log.is_file():
                    dev_failed = True
                    msgs.append(f"开发完成验证留档不完整：{v.name} 为 local 模式但无同轮 {boot_log.name}"
                                f"——重跑 verify_dev.py")
            # 交叉校验 c/d：A/B 级——冒烟条数与 smoke.md 同源、C 级留档不配 A/B 分级
            if tier_now in ("A", "B"):
                vscope = kv("执行范围") or ""
                if "C 级" in vscope:
                    dev_failed = True
                    msgs.append(f"开发完成验证范围过期：{v.name} 执行范围为 C 级，当前风险分级 {tier_now}"
                                f"——tier 已升级，重跑 verify_dev.py")
                smoke = dev_dir / "smoke.md"
                if not smoke.is_file():
                    dev_failed = True
                    msgs.append("A/B 级冒烟清单缺失：dev/smoke.md 不存在——先跑 /sdlc-test dev 生成")
                else:
                    # 条目标题口径经 _shared.SM_HEAD，与 verify_dev.parse_smoke 同源（改口径须两侧同步）；
                    # 留档正文围栏(构建/回归日志输出尾部)内的 `| SM-xx |` 引用行剥离后再计数
                    n_smoke = len(_shared.SM_HEAD.findall(
                        smoke.read_text(encoding="utf-8", errors="replace")))
                    n_rows = len(re.findall(r"^\|\s*SM-\d+\s*\|", strip_fences(vtext), re.M))
                    if n_smoke != n_rows:
                        dev_failed = True
                        msgs.append(f"开发完成验证与冒烟清单不符：{v.name} 冒烟明细 {n_rows} 条"
                                    f" ≠ smoke.md {n_smoke} 条——冒烟清单已变更，重跑 verify_dev.py")

    if msgs:
        if gate1_failed:
            hints.append("（关卡1 补救：人工审核用例后将 cases.md 头部「审核状态」改为「已确认（日期）」；"
                         "或完成 sdlc-gate 裁决使「评审状态=已放行」。处理后重跑本命令）")
        if dev_failed:
            hints.append("（开发完成验证补救：按 references/env-template.md「开发验证档」创建 sdlc/env/dev.md"
                         "（C 级最轻：仅「构建」「启动」两节），再运行 /sdlc-test dev"
                         "（或 python3 <skill 目录>/scripts/verify_dev.py <项目根> <需求名>）生成留档。"
                         "处理后重跑本命令）")
        return fail(msgs, hints)
    print(f"{OK} 关卡守卫通过（{phase}，审核状态/开发完成验证/资产一致性就绪）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

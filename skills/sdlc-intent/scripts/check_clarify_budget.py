#!/usr/bin/env python3
"""check_clarify_budget.py — 澄清量分档预算硬门校验（dimensions.md「检查顺序与使用说明」第 10 条的机械面）

七层体检照走、命中照记（留痕不降），本脚本只把「PM 入选数量与需求规模相称」变成可执行的反馈环。
**档位线只约束未经🔴自证的问题（🟡+🔵 合计）；🔴 过自证不计数、必问不拦**——真硬伤再多也全问。

重推携带豁免（--carry-file）：executor 在质检任务启动时把平台已有处置痕迹的行
（answer 非空 ∨ status≠pending ∨ note 非空，且 origin ∈ skill/incremental）落盘为工作区
carry.json。脚本对「seq 在清单 ∧ 问题文本 strip 后逐字一致」的项豁免——携带项不占预算、
永不删减（重推合并按 seq+文本双键携带处置，豁免口径与之同构）；seq 复现但文本被改写 =
平台不会携带（答复丢失），不豁免、计入预算并在 textDrift 透出（改回原文或按新问题计数）。

level fail-closed：非 red/yellow/blue（小写）的 level——含缺失与 emoji——一律 exit 1。
推送面只拦非空非法值、缺失默认 yellow 放行（requirement 服务层），本脚本是缺失/未知 level
的唯一拦截面。

超线或 🔵 超限时 exit 1，先删减黄蓝中的好奇级/顺带级（携带保护项除外，永不删减）；删后
仍超且全为动手级时，在 audit 执行摘要补「超档自证」小节后带 --allow-over 重跑放行
（自证文本由人/eval 核，脚本不核散文）。

档位判定与 dimensions.md 第 10 条分档表同源（改动须三侧同步：本脚本 + dimensions.md +
prompts.py 速查卡/第 5 步⑦）：
  重型 = FR>20 或 信号缺失（fr_points / roles / risk_tier 三者全无）→ 不设上限
  标准 = A 级或 B 级 或 FR 9~20              → 🟡+🔵 ≤25
  轻量 = 其余（C 级或 tier 缺失，且 FR≤8）    → 🟡+🔵 ≤12

用法：
  check_clarify_budget.py --payload payload-anchored.json                          # 首推硬门
  check_clarify_budget.py --payload payload-anchored.json --carry-file carry.json  # 重推：携带豁免
  check_clarify_budget.py --payload payload-anchored.json --allow-over             # 补自证后放行
"""
import argparse
import json
import sys
from typing import NoReturn

# 阈值常量：与 dimensions.md 第 10 条分档表同源（改动须三侧同步：本脚本 + dimensions + prompts 速查卡）
LIGHT_MAX = 12      # 轻量档目标上限
STANDARD_MAX = 25   # 标准档目标上限
LIGHT_FR = 8        # FR≤8 → 轻量信号（C 级/tier 缺失时）
STANDARD_FR = 20    # FR 9~20 → 标准信号；FR>20 → 重型（不论 tier，拿不准从高）
BLUE_LIMIT = 3      # 🔵 例外通道上限
VALID_LEVELS = ("red", "yellow", "blue")


def fail(msg: str) -> NoReturn:
    print(f"CLARIFY_BUDGET_FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def load_carry(path: str) -> dict[str, str]:
    """carry.json → {seq: question(strip 后)}。文件缺失/结构非法一律 fail（豁免面不静默降级）。"""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        fail(f"carry 文件不存在：{path}（重推硬门必须携带 executor 落盘的平台清单，缺失即拦）")
    except json.JSONDecodeError as e:
        fail(f"carry 文件不是合法 JSON：{e}（只可用 executor 落盘的 carry.json，不得手写改写）")
    if not isinstance(data, list):
        fail("carry 文件顶层必须是数组（executor 落盘的 [{seq,question,level}] 清单）")
    out: dict[str, str] = {}
    for i, row in enumerate(data):
        if not isinstance(row, dict):
            fail(f"carry 文件第 {i} 项不是对象")
        seq, question = row.get("seq"), row.get("question")
        if not isinstance(seq, str) or not seq.strip() or not isinstance(question, str):
            fail(f"carry 文件第 {i} 项缺 seq/question 字符串字段")
        out[seq.strip()] = question.strip()
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload", required=True, help="质检 payload JSON 路径（resolve_anchors 后的产物）")
    ap.add_argument("--carry-file", default="",
                    help="重推携带保护清单（executor 落盘的工作区 carry.json）：清单内 seq 且问题文本"
                         "逐字一致的项豁免计数、永不删减")
    ap.add_argument("--allow-over", action="store_true",
                    help="超档放行：要求已在 audit 执行摘要补「超档自证」小节（逐条 Pxx+一句理由）")
    args = ap.parse_args()

    try:
        with open(args.payload, encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        fail(f"payload 文件不存在：{args.payload}（先完成 resolve_anchors 再跑本脚本）")
    except json.JSONDecodeError as e:
        fail(f"payload 不是合法 JSON：{e}（检查组装/锚点附加是否破坏了结构）")
    if not isinstance(payload, dict):
        fail("payload 顶层不是 JSON 对象")
    items = payload.get("items")
    if not isinstance(items, list):
        fail("items 必须是数组")
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            fail(f"items 第 {i} 项不是对象")
    carry = load_carry(args.carry_file) if args.carry_file else {}

    digest = payload.get("digest") if isinstance(payload.get("digest"), dict) else {}
    frs = digest.get("fr_points") or []
    roles = digest.get("roles") or []
    tier = str(digest.get("risk_tier") or "").strip().upper()
    n_fr, n_roles = len(frs), len(roles)

    signals_missing = n_fr == 0 and n_roles == 0 and not tier
    if signals_missing or n_fr > STANDARD_FR:
        # FR>20 一律不封顶（不论 tier——C 级大需求不拿最紧预算）；信号缺失从高
        tier_name, cap = "重型", None
    elif tier in ("A", "B"):
        # A/B 级至少标准（A级小卡不判轻量——最高风险不拿最紧预算）
        tier_name, cap = "标准", STANDARD_MAX
    else:
        # C 级 / tier 缺失且 FR≤20：FR 9~20 → 标准；FR≤8（含 0）→ 轻量
        tier_name, cap = ("标准", STANDARD_MAX) if LIGHT_FR < n_fr <= STANDARD_FR else ("轻量", LIGHT_MAX)

    levels = {"red": 0, "yellow": 0, "blue": 0}
    carried = 0
    drift: list[str] = []
    for i, it in enumerate(items):
        lv = str(it.get("level") or "").strip().lower()
        if lv not in VALID_LEVELS:
            # fail-closed：缺失/未知 level 不静默跳过——推送面对缺失默认 yellow 放行，本脚本是唯一拦截面
            seq = it.get("seq") if isinstance(it.get("seq"), str) else ""
            where = f"seq={seq}" if seq else f"第 {i} 项"
            fail(f"items {where} 的 level 非法：{it.get('level')!r}——只允许小写 "
                 f"{'/'.join(VALID_LEVELS)}（emoji/缺失/大写均须修正后重跑）")
        seq = str(it.get("seq") or "").strip()
        question = str(it.get("question") or "").strip()
        if seq and seq in carry:
            if carry[seq] == question:
                carried += 1  # 携带豁免：平台已有处置（seq+文本双键命中），不占预算、永不删减
                continue
            drift.append(seq)  # seq 复现但文本被改写：平台不会携带（处置丢失）→ 不豁免，计入预算
        levels[lv] += 1
    n = len(items)
    non_red = levels["yellow"] + levels["blue"]

    # 档位线只数未经🔴自证的问题（🟡+🔵）；🔴 自证过不计数、必问不拦；携带豁免项已剔除
    over_budget = cap is not None and non_red > cap
    blue_over = levels["blue"] > BLUE_LIMIT

    result = {
        "tier": tier_name, "riskTier": tier or "(缺)", "frPoints": n_fr, "roles": n_roles,
        "items": n, "red": levels["red"], "yellow": levels["yellow"], "blue": levels["blue"],
        "nonRed": non_red, "carried": carried, "textDrift": drift,
        "overBudget": over_budget, "blueOver": blue_over,
    }
    print("CLARIFY_BUDGET " + json.dumps(result, ensure_ascii=False))
    if drift:
        print(f"CLARIFY_BUDGET_DRIFT: seq {','.join(drift)} 在 carry 清单内但问题文本被改写——"
              f"平台重推合并不会携带（答复丢失）：要么改回原文（豁免不占预算），要么按新问题计数",
              file=sys.stderr)

    if n == 0:
        fail("items 为空——平台拒收空澄清清单（dimensions 第 10 条：确无动手级问题时保留信息量"
             "最大的一条，可降🔵）")
    if blue_over:
        fail(f"🔵 {levels['blue']} 条超过例外通道上限 {BLUE_LIMIT}——删减至 {BLUE_LIMIT} 条内"
             f"（好奇级问题移入体检明细留痕，不进清单；携带豁免项不计入 🔵 计数）")
    if over_budget and not args.allow_over:
        fail(f"{tier_name}档 🟡+🔵 合计 {non_red} 条超过上限 {cap}（🔴 {levels['red']} 条已自证不计数；"
             f"携带豁免 {carried} 条不计、永不删减）——先删减黄蓝中的好奇级/顺带级至线内"
             f"（留痕不删明细，携带保护项除外）；删后仍超且全为动手级时，在 audit 执行摘要补"
             f"「超档自证」小节（逐条 Pxx+一句理由）后带 --allow-over 重跑")


if __name__ == "__main__":
    main()

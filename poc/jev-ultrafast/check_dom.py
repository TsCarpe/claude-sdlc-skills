"""阶段 A：静态 DOM 覆盖率检查——jev 元素表 vs 独立控件普查。不调模型，不需要 API key。

用法（在 jev-ultrafast checkout 内，依赖已 uv sync）：
    uv run python check_dom.py --url 'https://<目标页面>' --wait 3 --out artifacts/dom

口径说明：普查按语义选择器数可见可交互控件，jev 按 DOM 节点去重收录，两者是近似对齐；
覆盖率仅作量级判断，精确差集看两侧 label 清单（人工/模型目检）。
"""

import argparse
import base64
import json
import sys
import time
from pathlib import Path

# 独立于 jev snapshot.js 的控件普查：语义选择器 + 可见性过滤，按交互方式归类。
POLL_JS = """(() => {
  const SELECTORS = [
    'button', 'a', 'select', 'textarea', 'summary', 'input',
    '[role="button"]', '[role="combobox"]', '[role="tab"]', '[role="switch"]',
    '[role="checkbox"]', '[role="radio"]', '[role="menuitem"]', '[role="option"]',
    '[contenteditable="true"]',
  ].join(',');
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight
      && r.right > 0 && r.left < innerWidth  // 横向越界与 jev 口径对齐
      && el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })
      && !el.disabled && el.getAttribute('aria-disabled') !== 'true';
  };
  const classify = (el) => {
    const tag = el.tagName.toLowerCase();
    const type = (el.getAttribute('type') || '').toLowerCase();
    if (tag === 'select') return 'select';
    if (tag === 'textarea' || el.isContentEditable) return 'textbox';
    if (tag === 'input') {
      if (['date', 'datetime-local', 'month', 'time', 'week'].includes(type)) return 'date';
      if (['text', 'search', 'email', 'url', 'tel', 'password', 'number'].includes(type) || !type) return 'textbox';
      return 'click';  // checkbox/radio/button 类 input，交互方式等同点击
    }
    return 'click';  // button/a/summary/role=*
  };
  const out = {};
  for (const el of document.querySelectorAll(SELECTORS)) {
    if (!visible(el)) continue;
    const label = (el.getAttribute('aria-label') || el.innerText || el.value || el.placeholder || '')
      .trim().replace(/\\s+/g, ' ').slice(0, 40);
    const slot = out[classify(el)] ?? (out[classify(el)] = { count: 0, labels: [] });
    slot.count += 1;
    if (slot.labels.length < 60) slot.labels.push(label);
  }
  return out;
})()"""

# 普查分类 → jev 动作 kind 的近似映射（date 无确定映射，本身就是观察点）。
CLASS_TO_KIND = {
    "click": "click",
    "textbox": "fill",
    "select": "select",
    "date": None,
}

THRESHOLD_TOTAL = 0.80


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="目标页面 URL（test 环境）")
    parser.add_argument("--wait", type=float, default=3.0, help="observe 前等待 SPA 渲染的秒数")
    parser.add_argument("--out", default="artifacts/dom", help="结果输出目录")
    args = parser.parse_args()

    from jev_ultrafast.browser import Browser  # noqa: PLC0415 须在 jev checkout 内运行

    browser = Browser(args.url)
    try:
        time.sleep(args.wait)
        # 视口宽度自适应：jev 硬编码 1120，中后台宽版布局会被右边界裁掉操作列。
        # 接入时同样要处理（改 jev browser.py 或外层先适配）。
        scroll_width = browser.evaluate("document.documentElement.scrollWidth") or 1120
        if scroll_width > 1120:
            browser.call(
                "Emulation.setDeviceMetricsOverride",
                width=int(scroll_width) + 40, height=780, deviceScaleFactor=1, mobile=False,
            )
            time.sleep(1.5)
        page = browser.observe(screenshot=True)
        poll = browser.evaluate(POLL_JS) or {}
    finally:
        browser.close()

    # jev 侧：按 kind 计数 + label 清单
    jev = {}
    for action in page["actions"]:
        kind = action["kind"]
        slot = jev.setdefault(kind, {"count": 0, "labels": []})
        slot["count"] += 1
        if len(slot["labels"]) < 60:
            slot["labels"].append(str(action.get("label", ""))[:40])

    rows, poll_total, covered = [], 0, 0
    for cls, poll_slot in sorted(poll.items()):
        kind = CLASS_TO_KIND.get(cls)
        jev_slot = jev.get(kind, {"count": 0, "labels": []}) if kind else {"count": 0, "labels": []}
        poll_total += poll_slot["count"]
        if kind:
            covered += min(jev_slot["count"], poll_slot["count"])
        rate = (min(jev_slot["count"], poll_slot["count"]) / poll_slot["count"]) if poll_slot["count"] else 1.0
        rows.append({
            "class": cls, "mapped_kind": kind or "(观察点)",
            "poll_count": poll_slot["count"], "jev_count": jev_slot["count"],
            "coverage": round(rate, 3),
            "poll_labels": poll_slot["labels"], "jev_labels": jev_slot["labels"],
        })

    overall = round(covered / poll_total, 3) if poll_total else 0.0
    zeroed = [r["class"] for r in rows if r["class"] in ("select", "textbox") and r["coverage"] == 0.0]
    result = {
        "url": args.url, "wait_s": args.wait,
        "overall_coverage": overall, "threshold": THRESHOLD_TOTAL,
        "s1_pass": overall >= THRESHOLD_TOTAL,
        "s2_pass": not zeroed, "s2_zeroed_classes": zeroed,
        "rows": rows,
    }

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "dom_coverage.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    (out / "page.png").write_bytes(base64.b64decode(page["screenshot"]))  # 目检用

    print(f"页面: {args.url}")
    print(f"{'类':<10}{'映射kind':<12}{'普查':>6}{'jev':>6}{'覆盖率':>8}")
    for r in rows:
        print(f"{r['class']:<10}{r['mapped_kind']:<12}{r['poll_count']:>6}{r['jev_count']:>6}{r['coverage']:>8.1%}")
    print(f"\nS1 总体覆盖率 {overall:.1%}（阈值 {THRESHOLD_TOTAL:.0%}）: {'PASS' if result['s1_pass'] else 'FAIL'}")
    print(f"S2 关键类归零: {zeroed or '无'} → {'PASS' if result['s2_pass'] else 'FAIL'}")
    print(f"S3 日期类覆盖请人工确认（rows 中 class=date 行 + page.png）")
    print(f"明细已写入 {out / 'dom_coverage.json'}，截图 {out / 'page.png'}")
    return 0 if result["s1_pass"] and result["s2_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

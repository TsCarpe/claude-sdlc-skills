#!/usr/bin/env python3
"""check_flowviz.py — flow-viz 图协议机检（references/flow-viz-protocol.md 的机械面）

校验 markdown 产物中全部 ```flow-viz 代码块：JSON 可解析、kind 合法、nodes 非空、
id 全图唯一、边 from/to 指向已声明节点、节点 lane 引用已声明泳道、无自环。
只验协议本身（图结构与字段形态），不验语义出处——出处与 payload 投影对齐由
digest 梳理纪律与平台 dangling 校验承担。

权威源是仓根 scripts/check_flowviz.py（平台流水线直调路径），本文件是随
sdlc-intent skill 分发的副本——修改必须双写两份，先改权威源再同步本副本。

退出码：0 = 全部通过；1 = 有违规（stderr 逐条给块位置与修复建议）。
用法：
  check_flowviz.py <md 文件>...          # 一个或多个产物 markdown
  check_flowviz.py --selftest            # 内置自测（合法/非法样例）
"""
import argparse
import json
import re
import sys
from pathlib import Path

FLOW_RE = re.compile(r"```flow-viz[ \t]*\n(.*?)```", re.DOTALL)


def check_md_text(text: str, src: str) -> list[str]:
    """返回违规列表（空 = 通过）。"""
    problems: list[str] = []
    for i, m in enumerate(FLOW_RE.finditer(text), start=1):
        block_no = f"{src} 第 {i} 个 flow-viz 块"
        raw = m.group(1)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            problems.append(f"{block_no}：JSON 解析失败（第 {e.lineno} 行 {e.msg}）——"
                            f"检查尾逗号/注释/引号配对，JSON 纪律见 references/flow-viz-protocol.md")
            continue
        if not isinstance(data, dict):
            problems.append(f"{block_no}：块内容不是 JSON 对象")
            continue
        kind = data.get("kind")
        if kind not in ("flow", "state"):
            problems.append(f"{block_no}：kind 必须是 \"flow\" 或 \"state\"（当前：{kind!r}）")
            continue

        lanes = data.get("lanes") or []
        if not isinstance(lanes, list):
            problems.append(f"{block_no}：lanes 必须是数组")
            lanes = []
        lane_ids = [l.get("id") for l in lanes if isinstance(l, dict) and l.get("id")]

        nodes = data.get("nodes")
        if not isinstance(nodes, list) or not nodes:
            problems.append(f"{block_no}：nodes 为空或缺失——无可渲染内容")
            continue
        seen: set[str] = set()
        for n in nodes:
            if not isinstance(n, dict):
                problems.append(f"{block_no}：节点不是对象")
                continue
            nid = n.get("id")
            if not nid or not isinstance(nid, str):
                problems.append(f"{block_no}：存在无 id 节点——每个节点必须有字符串 id")
            elif nid in seen:
                problems.append(f"{block_no}：节点 id {nid!r} 重复——id 全图唯一（重复即渲染丢弃，意图丢失）")
            else:
                seen.add(nid)
            lane = n.get("lane")
            if lane is not None and lane not in lane_ids:
                problems.append(f"{block_no}：节点 {nid!r} 引用未声明泳道 {lane!r}——"
                                f"在 lanes 中声明或删除该 lane 字段")

        edges = data.get("edges") or []
        if not isinstance(edges, list):
            problems.append(f"{block_no}：edges 必须是数组")
            edges = []
        for e in edges:
            if not isinstance(e, dict):
                problems.append(f"{block_no}：存在非对象边")
                continue
            fr, to = e.get("from"), e.get("to")
            for side, v in (("from", fr), ("to", to)):
                if v is None:
                    problems.append(f"{block_no}：边缺 {side} 字段")
                elif v not in seen:
                    problems.append(f"{block_no}：边 {fr!r}→{to!r} 的 {side}={v!r} 不在 nodes——"
                                    f"悬空边渲染即丢弃，补声明节点或删该边")
            if fr == to and fr is not None:
                problems.append(f"{block_no}：自环边 {fr!r}→{to!r}——协议不表达自环，"
                                f"原文明说的自迁移写节点 note")
    return problems


def _selftest() -> int:
    ok = json.dumps({
        "kind": "flow", "lanes": [{"id": "L1", "label": "A"}],
        "nodes": [{"id": "n1", "lane": "L1", "label": "x"}],
        "edges": [],
    }, ensure_ascii=False)
    bad_json = '{"kind": "flow", "nodes": [{"id": "n1"}],}'      # 尾逗号
    bad_dangling = json.dumps({"kind": "flow",
                               "nodes": [{"id": "n1", "label": "x"}],
                               "edges": [{"from": "n1", "to": "ghost"}]}, ensure_ascii=False)
    bad_selfloop = json.dumps({"kind": "state",
                               "nodes": [{"id": "s1", "type": "state", "label": "x"}],
                               "edges": [{"from": "s1", "to": "s1"}]}, ensure_ascii=False)
    cases = [
        ("ok", f"```flow-viz\n{ok}\n```", 0),
        ("bad-json", f"```flow-viz\n{bad_json}\n```", 1),
        ("dangling", f"```flow-viz\n{bad_dangling}\n```", 1),
        ("selfloop", f"```flow-viz\n{bad_selfloop}\n```", 1),
    ]
    failed = 0
    for name, text, want in cases:
        got = len(check_md_text(text, "selftest"))
        status = "PASS" if (got > 0) == (want == 1) else "FAIL"
        if status == "FAIL":
            failed += 1
        print(f"selftest {name}: {status}")
    # 跨文件围栏正则一致软断言:check_standard_doc.py 内嵌同款 FV_BLOCK 定义,漂移即 FAIL。
    # 候选按部署形态探测(skill 树内 / 仓根 skills 树),均不存在(单装环境)则跳过。
    fence_def = 'FV_BLOCK = re.compile(r"```flow-viz[ \\t]*\\n(.*?)```", re.DOTALL)'
    here = Path(__file__).resolve().parent
    for cand in (here.parent / "skills" / "sdlc-sync" / "scripts" / "check_standard_doc.py",
                 here.parent.parent / "sdlc-sync" / "scripts" / "check_standard_doc.py"):
        if cand.is_file():
            ok = fence_def in cand.read_text(encoding="utf-8")
            print(f"selftest fv-fence-drift({cand.parents[2].name}/sdlc-sync): {'PASS' if ok else 'FAIL'}")
            if not ok:
                failed += 1
    return 1 if failed else 0


def main() -> None:
    ap = argparse.ArgumentParser(description="flow-viz 图协议机检")
    ap.add_argument("files", nargs="*", help="产物 markdown 文件")
    ap.add_argument("--selftest", action="store_true", help="内置自测")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(_selftest())
    if not args.files:
        ap.error("至少给一个 md 文件（或 --selftest）")

    total_blocks = 0
    problems: list[str] = []
    for f in args.files:
        p = Path(f)
        if not p.exists():
            sys.exit(f"FLOWVIZ_FAIL: 文件不存在 {f}")
        text = p.read_text(encoding="utf-8")
        total_blocks += len(FLOW_RE.findall(text))
        problems += check_md_text(text, p.name)

    if problems:
        print("FLOWVIZ_FAIL: flow-viz 块未过协议机检，逐条修复后重跑：", file=sys.stderr)
        for msg in problems:
            print(f"  - {msg}", file=sys.stderr)
        sys.exit(1)
    print(f"FLOWVIZ {json.dumps({'files': len(args.files), 'blocks': total_blocks, 'problems': 0}, ensure_ascii=False)}")


if __name__ == "__main__":
    main()

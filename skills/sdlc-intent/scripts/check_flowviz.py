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


def check_md_text(text: str, src: str) -> tuple[list[str], list[str]]:
    """返回 (违规列表, 观察列表)（违规空 = 通过；观察不阻断 exit 0）。"""
    problems: list[str] = []
    warns: list[str] = []
    blocks = list(FLOW_RE.finditer(text))
    if text.strip() and not blocks:
        # 调用面是 digest 产物（§5/§6 必有图）：0 块 = 图载体退化（如画成 mermaid），必须打回
        problems.append(f"{src}：未找到任何 flow-viz 块——流程/状态图必须用 flow-viz fenced JSON 载体"
                        f"（mermaid 或纯文字描述不接受，改写后重跑）")
        return problems, warns
    for i, m in enumerate(blocks, start=1):
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

        # ---- 泳道质量（kind=flow 且泳道化；口径与前端 swimlane.js 同步，改须双侧）----
        if kind == "flow" and lane_ids:
            group = {n.get("id"): n.get("lane") or "__free__"
                     for n in nodes if isinstance(n, dict) and n.get("id")}
            valid_edges = [e for e in edges if isinstance(e, dict)
                           and e.get("from") in group and e.get("to") in group]
            out_ids = {e.get("from") for e in valid_edges}
            in_solid = {e.get("to") for e in valid_edges if not e.get("dashed")}
            in_any = {e.get("to") for e in valid_edges}
            # 纯标注断点（前端 splitFloatGaps 浮放集同判定）：gap 且有入边、入边全 dashed、无出边
            float_ids = {nid for n in nodes if isinstance(n, dict)
                         for nid in [n.get("id")]
                         if nid and n.get("gap") is True and nid in in_any
                         and nid not in in_solid and nid not in out_ids}
            if len(lane_ids) > 4:
                warns.append(f"{block_no}：泳道数 {len(lane_ids)} >4——粒度过细，"
                             f"建议按角色职责段合并泳道")
            for nid in float_ids:
                if group.get(nid, "__free__") != "__free__":
                    warns.append(f"{block_no}：纯标注断点 {nid!r} 带 lane——断点不写 lane"
                                 f"（渲染贴宿主浮放，泳道归属被忽略）")
            # 跨泳道率：非 dashed 边、计数 ≥4、严格 >50%（free 组独立，同 '__free__' 不算跨）
            counted = [(e["from"], e["to"]) for e in valid_edges if not e.get("dashed")]
            cross = [(fr, to) for fr, to in counted if group[fr] != group[to]]
            if len(counted) >= 4 and len(cross) / len(counted) > 0.5:
                detail = "、".join(f"{fr}({group[fr]})→{to}({group[to]})" for fr, to in cross)
                problems.append(f"{block_no}：跨泳道边 {len(cross)}/{len(counted)}"
                                f"（{len(cross) * 100 // len(counted)}%）——泳道应按角色职责段聚簇，"
                                f"系统判定/页面展示类节点归当前操作角色泳道，勿按操作/响应逐边换道；"
                                f"跨道边：{detail}")
    return problems, warns


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
        ("ok", f"```flow-viz\n{ok}\n```", "clean"),
        ("bad-json", f"```flow-viz\n{bad_json}\n```", "fail"),
        ("dangling", f"```flow-viz\n{bad_dangling}\n```", "fail"),
        ("selfloop", f"```flow-viz\n{bad_selfloop}\n```", "fail"),
    ]
    # 泳道质量：锯齿换道 FAIL / 健康聚簇干净 / 断点带 lane WARN / 泳道>4 WARN
    high_cross = json.dumps({"kind": "flow",
                             "lanes": [{"id": "L1"}, {"id": "L2"}],
                             "nodes": [{"id": "A1", "lane": "L1", "label": "a"},
                                       {"id": "A2", "lane": "L2", "label": "b"},
                                       {"id": "A3", "lane": "L1", "label": "c"},
                                       {"id": "A4", "lane": "L2", "label": "d"},
                                       {"id": "A5", "lane": "L1", "label": "e"}],
                             "edges": [{"from": "A1", "to": "A2"}, {"from": "A2", "to": "A3"},
                                       {"from": "A3", "to": "A4"}, {"from": "A4", "to": "A5"}]},
                            ensure_ascii=False)
    clustered = json.dumps({"kind": "flow",
                            "lanes": [{"id": "L1"}, {"id": "L2"}],
                            "nodes": [{"id": "A1", "lane": "L1", "label": "a"},
                                      {"id": "A2", "lane": "L1", "label": "b"},
                                      {"id": "A3", "lane": "L1", "label": "c"},
                                      {"id": "B1", "lane": "L2", "label": "d"}],
                            "edges": [{"from": "A1", "to": "A2"}, {"from": "A2", "to": "A3"},
                                      {"from": "A3", "to": "B1"}, {"from": "B1", "to": "A3", "dashed": True}]},
                           ensure_ascii=False)
    gap_lane = json.dumps({"kind": "flow",
                           "lanes": [{"id": "L1"}],
                           "nodes": [{"id": "A1", "lane": "L1", "label": "a"},
                                     {"id": "A2", "lane": "L1", "label": "b"},
                                     {"id": "G", "lane": "L1", "label": "断点", "gap": True}],
                           "edges": [{"from": "A1", "to": "A2"}, {"from": "A2", "to": "G", "dashed": True}]},
                          ensure_ascii=False)
    lanes5 = json.dumps({"kind": "flow",
                         "lanes": [{"id": f"L{i}"} for i in range(1, 6)],
                         "nodes": [{"id": f"n{i}", "lane": f"L{i}", "label": "x"} for i in range(1, 6)],
                         "edges": []}, ensure_ascii=False)
    cases += [
        ("high-cross", f"```flow-viz\n{high_cross}\n```", "fail"),
        ("clustered", f"```flow-viz\n{clustered}\n```", "clean"),
        ("gap-lane-warn", f"```flow-viz\n{gap_lane}\n```", "warn"),
        ("lanes-over-4", f"```flow-viz\n{lanes5}\n```", "warn"),
        ("no-block", "正文无图（mermaid 退化形态）\n```mermaid\nflowchart TD\n  A-->B\n```\n", "fail"),
    ]
    failed = 0
    for name, text, want in cases:
        problems, warns = check_md_text(text, "selftest")
        got = "fail" if problems else ("warn" if warns else "clean")
        status = "PASS" if got == want else "FAIL"
        if status == "FAIL":
            failed += 1
        print(f"selftest {name}: {status} (want={want}, got={got})")
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
    warns: list[str] = []
    for f in args.files:
        p = Path(f)
        if not p.exists():
            sys.exit(f"FLOWVIZ_FAIL: 文件不存在 {f}")
        text = p.read_text(encoding="utf-8")
        total_blocks += len(FLOW_RE.findall(text))
        block_problems, block_warns = check_md_text(text, p.name)
        problems += block_problems
        warns += block_warns

    # WARN 只进 stdout（agent 按 stderr+exit 码驱动修复循环，exit-0 输出混入 stderr 会被误读）
    for msg in warns:
        print(f"FLOWVIZ_WARN: {msg}")
    if problems:
        print("FLOWVIZ_FAIL: flow-viz 块未过协议机检，逐条修复后重跑：", file=sys.stderr)
        for msg in problems:
            print(f"  - {msg}", file=sys.stderr)
        sys.exit(1)
    print(f"FLOWVIZ {json.dumps({'files': len(args.files), 'blocks': total_blocks, 'problems': 0, 'warns': len(warns)}, ensure_ascii=False)}")


if __name__ == "__main__":
    main()

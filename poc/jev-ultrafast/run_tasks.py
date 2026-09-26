"""阶段 B：动态任务执行——jev 走任务清单，独立 verify 断言终态，汇总判定 D1/D2/D3。

用法（在 jev-ultrafast checkout 内，.env 已配 TYPESAFE_API_KEY / TEXT_MODEL_API_KEY）：
    uv run --env-file .env python run_tasks.py --tasks tasks_local --out artifacts/run

任务清单是 Python 模块（复制 tasks_example.py 为 tasks_local.py 后编辑），每项：
    {"id": str, "url": str, "goals": str | list[str], "tags": [str],
     "verify": lambda page -> {"passed": bool, "checks": dict}}
jev 的 DONE 不可信，verify 必须独立断言（官方 examples/flights.py 同款姿势）。
"""

import argparse
import importlib
import json
import signal
import sys
import time
from pathlib import Path

# 判定阈值（与 README.md 同步，改动须两处一起改）
THRESHOLD_PASS_RATE = 0.60     # D1 真通过率 ≥ 60%
THRESHOLD_MISJUDGE = 0.10      # D2 误判率 ≤ 10%
THRESHOLD_AVG_SECONDS = 30.0   # D3 平均耗时 ≤ 30s/任务
MIN_TASKS_FOR_VERDICT = 10     # 任务数不足只出参考值
TASK_TIMEOUT_SECONDS = 180     # 单任务墙钟保险（jev 内部另有 MAX_STEPS 预算）


def run_one(task, out_dir):
    from jev_ultrafast import Agent  # noqa: PLC0415 须在 jev checkout 内运行

    task_dir = out_dir / task["id"]
    task_dir.mkdir(parents=True, exist_ok=True)
    outcome, detail = "error", ""

    def on_timeout(signum, frame):
        raise TimeoutError(f"task exceeded {TASK_TIMEOUT_SECONDS}s")

    old_handler = signal.signal(signal.SIGALRM, on_timeout)
    signal.alarm(TASK_TIMEOUT_SECONDS)
    agent = None
    try:
        agent = Agent(task["url"], task["goals"], record_dir=task_dir)
        for _ in agent.run():
            pass
        state = agent.snapshot()
        if state["status"] == "done":
            verification = task["verify"](state["page"])
            outcome = "done_verified" if verification.get("passed") else "done_unverified"
            state["verification"] = verification
        else:
            outcome = "blocked" if state["status"] == "blocked" else f"status:{state['status']}"
        (task_dir / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2, default=str))
        elapsed_ms = state.get("elapsed_ms", 0)
    except TimeoutError:
        outcome, detail, elapsed_ms = "timeout", "wall clock", TASK_TIMEOUT_SECONDS * 1000
    except Exception as exc:  # 模型连接/预算耗尽/verify 自身异常等，原样留痕
        outcome, detail, elapsed_ms = "error", f"{type(exc).__name__}: {exc}", 0
        if agent is not None:
            try:
                state = agent.snapshot()
                (task_dir / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2, default=str))
            except Exception:
                pass
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        if agent is not None:
            try:
                agent.close()
            except Exception:
                pass
    return {"id": task["id"], "tags": task.get("tags", []), "outcome": outcome,
            "detail": detail, "elapsed_ms": elapsed_ms}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", default="tasks_local", help="任务清单模块名（默认 tasks_local）")
    parser.add_argument("--only", help="只跑指定任务（逗号分隔 id），冒烟用")
    parser.add_argument("--out", default="artifacts/run", help="结果输出目录")
    args = parser.parse_args()

    try:
        tasks = importlib.import_module(args.tasks).TASKS
    except ModuleNotFoundError:
        print(f"找不到任务清单模块 {args.tasks}：先 cp tasks_example.py {args.tasks}.py 并填写真实任务")
        return 2
    if args.only:
        wanted = {x.strip() for x in args.only.split(",")}
        tasks = [t for t in tasks if t["id"] in wanted]

    out_dir = Path(args.out)
    results = [run_one(task, out_dir) for task in tasks]

    total = len(results)
    done = [r for r in results if r["outcome"].startswith("done")]
    verified = [r for r in results if r["outcome"] == "done_verified"]
    misjudged = [r for r in results if r["outcome"] == "done_unverified"]
    pass_rate = len(verified) / total if total else 0.0
    misjudge_rate = len(misjudged) / len(done) if done else 0.0
    avg_seconds = (sum(r["elapsed_ms"] for r in results) / total / 1000) if total else 0.0

    formal = total >= MIN_TASKS_FOR_VERDICT
    summary = {
        "total": total,
        "outcomes": {o: sum(1 for r in results if r["outcome"] == o) for o in {r["outcome"] for r in results}},
        "d1_pass_rate": {"value": round(pass_rate, 3), "threshold": THRESHOLD_PASS_RATE},
        "d2_misjudge_rate": {"value": round(misjudge_rate, 3), "threshold": THRESHOLD_MISJUDGE},
        "d3_avg_seconds": {"value": round(avg_seconds, 1), "threshold": THRESHOLD_AVG_SECONDS},
        "fallback_rate": round(1 - pass_rate, 3),
        "formal_verdict": formal,
        "results": results,
    }
    if formal:
        summary["verdict"] = "PASS" if (
            pass_rate >= THRESHOLD_PASS_RATE
            and misjudge_rate <= THRESHOLD_MISJUDGE
            and avg_seconds <= THRESHOLD_AVG_SECONDS
        ) else "FAIL"

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))

    print(f"{'任务':<24}{'结果':<18}{'耗时s':>8}  备注")
    for r in results:
        print(f"{r['id']:<24}{r['outcome']:<18}{r['elapsed_ms'] / 1000:>8.1f}  {r['detail']}")
    print(f"\nD1 真通过率 {pass_rate:.1%}（阈值 ≥{THRESHOLD_PASS_RATE:.0%}）")
    print(f"D2 误判率   {misjudge_rate:.1%}（阈值 ≤{THRESHOLD_MISJUDGE:.0%}）")
    print(f"D3 平均耗时 {avg_seconds:.1f}s（阈值 ≤{THRESHOLD_AVG_SECONDS:.0f}s）")
    if formal:
        print(f"判定: {summary['verdict']}")
        return 0 if summary["verdict"] == "PASS" else 1
    print(f"任务数 {total} < {MIN_TASKS_FOR_VERDICT}，仅参考值，不作正式判定")
    print(f"明细已写入 {out_dir / 'summary.json'}（含每任务 record 截图，误判复核用）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

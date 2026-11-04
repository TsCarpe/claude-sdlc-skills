#!/usr/bin/env python3
"""digest_transcript.py — compact a JSONL session transcript into a readable digest.

Used by sdlc-handoff to let a new session recover *intent* from the old session
without paying for the full transcript. Standard library only; no third-party
dependencies. Unknown record shapes are skipped rather than treated as errors.

Usage:
  python3 digest_transcript.py --session /path/to/session.jsonl [--tail 40]
  python3 digest_transcript.py --dir /path/to/sessions --cwd /path/to/project
  python3 digest_transcript.py --list --dir /path/to/sessions

Exit code is always 0 (a failed parse must never block a handoff).
"""

import argparse
import json
import os
import sys

MAX_TOOL_INPUT = 120
MAX_TEXT = 400
FILE_KEYS = ("path", "paths", "file_path", "filePath", "notebook_path", "files")


def parse_record(raw):
    """Return (role, content, timestamp) for a record, or None."""
    try:
        rec = json.loads(raw)
    except Exception:
        return None
    if not isinstance(rec, dict):
        return None

    msg = rec.get("message") if isinstance(rec.get("message"), dict) else None
    if msg is None and "role" in rec and "content" in rec:
        msg = rec
    if msg is None:
        return None

    role = msg.get("role") or rec.get("type")
    content = msg.get("content", msg.get("text", ""))
    ts = rec.get("timestamp") or msg.get("timestamp") or ""
    return role, content, ts


def as_parts(content):
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if isinstance(content, list):
        return [p for p in content if isinstance(p, dict)]
    return []


def short(value, limit=MAX_TOOL_INPUT):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + "…"


def tool_files(name, payload):
    out = []
    if isinstance(payload, dict):
        for key in FILE_KEYS:
            value = payload.get(key)
            if isinstance(value, str):
                out.append(value)
            elif isinstance(value, list):
                out.extend([v for v in value if isinstance(v, str)])
    return out


def hhmm(ts):
    if not isinstance(ts, str) or len(ts) < 16:
        return "--:--"
    return ts[11:16]


def digest(path, tail=None, max_chars=12000):
    user_lines = []
    timeline = []
    files = {}
    total = 0

    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        raw_lines = handle.readlines()
    if tail:
        raw_lines = raw_lines[-tail:]

    for raw in raw_lines:
        parsed = parse_record(raw)
        if parsed is None:
            continue
        role, content, ts = parsed
        parts = as_parts(content)
        if not parts:
            continue
        total += 1

        has_tool_result = any(p.get("type") in ("tool_result", "tool_response") for p in parts)
        texts = [p.get("text", "") for p in parts if p.get("type") == "text" and p.get("text")]
        calls = [p for p in parts if p.get("type") in ("tool_use", "tool_call", "function_call")]

        if role in ("user", "human") and not has_tool_result and texts:
            for text in texts:
                user_lines.append("[%s] %s" % (hhmm(ts), short(text, MAX_TEXT)))
        if calls:
            counts = {}
            details = []
            for call in calls:
                name = call.get("name") or call.get("tool") or "tool"
                payload = call.get("input") or call.get("arguments") or {}
                counts[name] = counts.get(name, 0) + 1
                if len(calls) == 1:
                    details.append("%s: %s" % (name, short(payload)))
                for hit in tool_files(name, payload):
                    files[hit] = files.get(hit, 0) + 1
            if details:
                timeline.append("[%s] %s" % (hhmm(ts), details[0]))
            else:
                rendered = ", ".join("%s x%d" % (n, c) for n, c in counts.items())
                timeline.append("[%s] %s" % (hhmm(ts), rendered))

    out = []
    out.append("# 会话摘要")
    out.append("file: %s" % path)
    out.append("messages: %d" % total)
    out.append("")
    out.append("## 用户原话（意图 ground truth）")
    out.extend(user_lines or ["(none)"])
    out.append("")
    out.append("## 动作时间线（工具调用折叠）")
    out.extend(timeline or ["(none)"])
    out.append("")
    out.append("## 触碰文件（按次数）")
    if files:
        for name, count in sorted(files.items(), key=lambda kv: (-kv[1], kv[0])):
            out.append("%dx %s" % (count, name))
    else:
        out.append("(none)")

    text = "\n".join(out)
    if len(text) > max_chars:
        text = text[:max_chars] + "\n…（已截断，用 --tail 或 --max-chars 调整）"
    return text


def newest_session(directory, cwd=None):
    best = None
    for root, _dirs, names in os.walk(directory):
        for name in names:
            if not name.endswith(".jsonl") or name.endswith(".checkpoints.jsonl"):
                continue
            full = os.path.join(root, name)
            if cwd:
                try:
                    with open(full, "r", encoding="utf-8", errors="replace") as handle:
                        head = json.loads(handle.readline() or "{}")
                except Exception:
                    continue
                if head.get("cwd") != cwd:
                    continue
            stamp = os.path.getmtime(full)
            if best is None or stamp > best[0]:
                best = (stamp, full)
    return best[1] if best else None


def list_sessions(directory):
    found = []
    for root, _dirs, names in os.walk(directory):
        for name in names:
            if not name.endswith(".jsonl") or name.endswith(".checkpoints.jsonl"):
                continue
            full = os.path.join(root, name)
            found.append((os.path.getmtime(full), full))
    for _stamp, full in sorted(found, reverse=True)[:20]:
        print(full)
    return found


def main():
    parser = argparse.ArgumentParser(description="Compact a JSONL session transcript.")
    parser.add_argument("--session", help="path to a session .jsonl file")
    parser.add_argument("--dir", help="directory to search for session records")
    parser.add_argument("--cwd", help="only match session records whose header cwd equals this")
    parser.add_argument("--tail", type=int, default=0, help="only the last N records")
    parser.add_argument("--max-chars", type=int, default=12000, help="hard output cap")
    parser.add_argument("--list", action="store_true", help="list candidate session files and exit")
    args = parser.parse_args()

    try:
        if args.list:
            if not args.dir:
                print("--list requires --dir", file=sys.stderr)
                return 0
            list_sessions(args.dir)
            return 0

        path = args.session
        if not path and args.dir:
            path = newest_session(args.dir, args.cwd)
        if not path:
            print("digest unavailable: no session record found (pass --session or --dir)", file=sys.stderr)
            return 0
        if not os.path.isfile(path):
            print("digest unavailable: %s is not a readable file" % path, file=sys.stderr)
            return 0

        print(digest(path, tail=args.tail or None, max_chars=args.max_chars))
    except Exception as exc:  # never block a handoff because of a transcript quirk
        print("digest unavailable: %s" % exc, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sdlc guardrails engine — 可移植的确定性红线检查引擎。

设计约定（与 docs/design/agent-stack-mental-model.md §4 对应）：
- 引擎（机制）全局一份，规则（内容）在项目 `.claude/guardrails.yaml`
- 新项目接入只写规则文件 + settings 挂载段，不改本文件
- hook 模式永不阻塞 agent 循环：任何内部异常静默退出 0，拦截只通过 JSON decision 表达

两种用法：
1. hook 模式（默认）：stdin 读 Claude Code PostToolUse payload，校验
   tool_input.file_path，违规输出 {"decision":"block","reason":...}
2. check 模式：`check.py --check <file> [<file>...]` 人类可读输出，
   违规 exit 1（供 pre-commit / 基线扫描用）

规则文件：从被检文件向上逐级找 `.claude/guardrails.yaml`，找不到即 no-op。
规则结构：
  rules:
    - id: ctrl-logrecord          # 唯一标识，用于 reason 回溯
      glob: "**/controller/**/*Controller.java"   # ** 跨目录, * 单段
      type: count_ge | require | forbid
      anchor: "@PostMapping"      # count_ge 专用：分母
      pattern: "@LogRecord"       # 正则
      message: "每个接口方法必须带 @LogRecord"
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RULES_FILENAME = ".claude/guardrails.yaml"
MAX_FILE_BYTES = 2 * 1024 * 1024  # 超过 2MB 的文件跳过（生成产物/数据文件）


def glob_to_regex(glob: str) -> re.Pattern:
    """支持 ** 与 * 的极简 glob → regex（不做完整 fnmatch 兼容）。"""
    out = []
    i = 0
    while i < len(glob):
        c = glob[i]
        if glob[i:i + 3] == "**/":
            out.append("(?:.*/)?")
            i += 3
        elif c == "*":
            out.append("[^/]*")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return re.compile("".join(out) + "$")


def find_rules_file(target: Path) -> Path | None:
    for parent in [target.parent, *target.parent.parents]:
        candidate = parent / RULES_FILENAME
        if candidate.is_file():
            return candidate
    return None


def load_rules(rules_path: Path):
    import yaml  # 仅在找到规则文件后才 import，no-op 路径零依赖

    data = yaml.safe_load(rules_path.read_text(encoding="utf-8")) or {}
    rules = data.get("rules") or []
    for r in rules:
        r["_re"] = glob_to_regex(r.get("glob", "**/*"))
        r["_pattern"] = re.compile(r["pattern"])
        if r.get("type") == "require_if":
            r["_when"] = re.compile(r["when"])
        if r.get("type") == "count_ge":
            r["_anchor"] = re.compile(r["anchor"])
    return rules


def check_content(rules, path_str: str, content: str, kinds=None) -> list[str]:
    """返回违规描述列表（空=通过）。kinds 限定规则类型（Edit 增量模式只跑 forbid）。"""
    violations = []
    basename = Path(path_str).name
    for r in rules:
        if not r["_re"].search(path_str):
            continue
        rtype = r.get("type")
        if kinds and rtype not in kinds:
            continue
        msg = r.get("message", r["id"])
        if rtype == "forbid":
            m = r["_pattern"].search(content)
            if m:
                line = content.count("\n", 0, m.start()) + 1
                violations.append(f"[{r['id']}] {basename}:{line} {msg}")
        elif rtype == "require":
            if not r["_pattern"].search(content):
                violations.append(f"[{r['id']}] {basename} {msg}")
        elif rtype == "require_if":
            # 文件命中 when 模式时，pattern 必须出现（如分页 Req 有 page 字段则须有 @Min）
            if r["_when"].search(content) and not r["_pattern"].search(content):
                violations.append(f"[{r['id']}] {basename} {msg}")
        elif rtype == "count_ge":
            need = len(r["_anchor"].findall(content))
            if need == 0:
                continue  # 无锚点（如无接口方法）不适用
            have = len(r["_pattern"].findall(content))
            if have < need:
                violations.append(
                    f"[{r['id']}] {basename} {msg}（{r['pattern']} 出现 {have} 次 < 锚点 {r['anchor']} {need} 次）"
                )
    return violations


def check_file(rules, path_str: str) -> list[str]:
    p = Path(path_str)
    try:
        if not p.is_file() or p.stat().st_size > MAX_FILE_BYTES:
            return []
        content = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return check_content(rules, path_str, content)


# ---------- hook 模式 ----------

def run_hook_mode() -> int:
    try:
        payload = json.load(sys.stdin)
        ti = payload.get("tool_input") or {}
        file_path = ti.get("file_path")
        if not file_path:
            return 0
        target = Path(file_path)
        rules_path = find_rules_file(target)
        if rules_path is None:
            return 0
        rules = load_rules(rules_path)
        if "new_string" in ti:
            # Edit 增量模式：只对本次新增文本跑 forbid——
            # 存量旧账（如缺 @Validate）不阻塞编辑者，进基线报告处理
            violations = check_content(rules, file_path, ti["new_string"], kinds=("forbid",))
        else:
            # Write 新文件：全文件全规则
            violations = check_file(rules, file_path)
        if violations:
            print(json.dumps({
                "decision": "block",
                "reason": "guardrails 红线拦截：\n" + "\n".join(violations)
                          + "\n修复后重写该文件即可继续。",
                "suppressOutput": True,
            }, ensure_ascii=False))
        return 0
    except Exception as e:  # 引擎任何异常都不得打断 agent 循环
        print(f"guardrails engine error (ignored): {e}", file=sys.stderr)
        return 0


# ---------- check 模式 ----------

def run_check_mode(files: list[str]) -> int:
    failed = False
    for f in files:
        rules_path = find_rules_file(Path(f).resolve())
        if rules_path is None:
            print(f"{f}: 无 {RULES_FILENAME}，跳过")
            continue
        rules = load_rules(rules_path)
        for v in check_file(rules, f):
            print(f"{f}: {v}")
            failed = True
    return 1 if failed else 0


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] == "--check":
        return run_check_mode(args[1:])
    return run_hook_mode()


if __name__ == "__main__":
    sys.exit(main())

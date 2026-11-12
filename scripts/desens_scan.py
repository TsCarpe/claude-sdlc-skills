#!/usr/bin/env python3
"""仓库脱敏扫描器（CLAUDE.md 脱敏红线第 5 条的机检化，替代手写 rg 命令）。

扫描范围：`git ls-files --cached --others --exclude-standard`
——跟踪文件 + 未忽略的未跟踪文件。未提交的新文件正是脱敏主防对象，
纯 --cached 会把它们盲掉，造成「改写后零命中」的假阴性。

两级词表见同目录 desens_words.json（词表演进只改该文件，不改本脚本）：
  fail   零容忍，命中退出码 1（CI 拦截）；英文词大小写不敏感
  review 泛词人工复核，默认按文件汇总提示；--strict 时计败

用法：
  python3 scripts/desens_scan.py            # fail 级拦截
  python3 scripts/desens_scan.py --strict   # review 级也拦截
  python3 scripts/desens_scan.py --list     # 只打印词表与扫描范围

退出码：0=干净；1=存在 fail 命中（--strict 下含 review）。纯标准库。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORDS = HERE / "desens_words.json"


def load_words() -> dict:
    data = json.loads(WORDS.read_text(encoding="utf-8"))
    fail = [str(w) for w in data.get("fail", [])]
    review = [str(w) for w in data.get("review", [])]
    excludes = [str(x) for x in data.get("excludes", [])]
    return {"fail": fail, "review": review, "excludes": excludes}


def excluded(path: str, excludes: list[str]) -> bool:
    """CHANGELOG.md/CLAUDE.md 按文件名匹配任意目录；.github/** 按目录前缀；其余按精确路径。"""
    name = path.rsplit("/", 1)[-1]
    for pat in excludes:
        if pat.endswith("/**"):
            if path.startswith(pat[:-2]):
                return True
        elif "/" in pat:
            if path == pat:
                return True
        elif name == pat:
            return True
    return False


def scan_file(path: Path, fail_words: list[str], review_words: list[str]) -> tuple[list[str], Counter]:
    """返回 (fail 命中明细, review 计数)。二进制/解码失败文件跳过。"""
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return [], Counter()
    lower = text.lower()
    fails: list[str] = []
    for w in fail_words:
        needle = w.lower()
        start = 0
        while True:
            i = lower.find(needle, start)
            if i == -1:
                break
            line_no = text.count("\n", 0, i) + 1
            snippet = text[max(0, i - 15): i + len(w) + 15].replace("\n", " ")
            fails.append(f"{w}: {snippet}")
            start = i + len(w)
    reviews = Counter(w for w in review_words if w in text)
    return fails, reviews


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="desens_scan.py", description="仓库脱敏扫描（fail 零容忍 / review 人工复核）")
    ap.add_argument("--strict", action="store_true", help="review 级泛词命中也计败")
    ap.add_argument("--list", dest="list_only", action="store_true", help="只打印词表与扫描范围")
    a = ap.parse_args(argv)

    words = load_words()
    if a.list_only:
        print(f"fail({len(words['fail'])}): {'|'.join(words['fail'])}")
        print(f"review({len(words['review'])}): {'|'.join(words['review'])}")
        print(f"excludes: {'|'.join(words['excludes'])}")
        return 0

    try:
        out = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            capture_output=True, text=True, check=True, timeout=30,
        ).stdout
    except (subprocess.SubprocessError, OSError) as e:
        print(f"错误:无法枚举扫描范围(git ls-files 失败,需在 git 仓库内运行):{e}", file=sys.stderr)
        return 2
    files = [f for f in out.splitlines() if f and not excluded(f, words["excludes"])]

    fail_hits: list[str] = []
    review_total: Counter = Counter()
    review_files = 0
    for f in files:
        p = Path(f)
        if not p.is_file():
            continue
        fails, reviews = scan_file(p, words["fail"], words["review"])
        for detail in fails:
            fail_hits.append(f"{f}: {detail}")
        if reviews:
            review_files += 1
            review_total.update(reviews)

    if fail_hits:
        print(f"== FAIL 级命中 {len(fail_hits)} 处（零容忍,改写为中性虚构或登记豁免+理由）==")
        for h in fail_hits:
            print(f"  {h}")
    if review_total:
        level = "FAIL" if a.strict else "REVIEW"
        print(f"== {level} 级泛词 {sum(review_total.values())} 处 / {review_files} 文件（人工复核;--strict 计败）==")
        for w, n in sorted(review_total.items(), key=lambda kv: -kv[1]):
            print(f"  {w} ×{n}")
    if fail_hits:
        print("汇总:FAIL 命中未清零——脱敏红线未通过", file=sys.stderr)
        return 1
    if review_total and a.strict:
        print("汇总:--strict 下 review 命中计败", file=sys.stderr)
        return 1
    print(f"OK: fail 级零命中（扫描 {len(files)} 文件;review 级 {sum(review_total.values())} 处待人工复核）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""build_suite_bundle.py — 打 SkillHub Suite Bundle（根目录 SUITE.yaml + skills/<name>/）

从 git 提交（默认 HEAD）取 skills/，只打 git 跟踪的文件（本地缓存、未提交改动不进包），
生成 SUITE.yaml（kind: SkillSuiteBundle）后打成一个 ZIP，供 SkillHub「创建技能套件 → 本地导入」
一次上传：确认后各成员按独立技能发布并送审，全部就绪才生成套件草稿。

成员 = marketplace.json 的 plugins[0].skills；顺序与一句话说明见下方 MEMBERS。
增删/改名 skill 必须同步 MEMBERS，两边不一致时脚本拒绝出包。
成员版本取各 SKILL.md 的 metadata.version（缺省时 SkillHub 生成时间版本）；
SkillHub 不允许覆盖已发布版本，改过的 skill 发版前先改大它的 metadata.version。

用法：
  build_suite_bundle.py                                            # 新建套件：mode CREATE，版本 1.0.0
  build_suite_bundle.py --mode UPDATE --base-version 1.0.0 --version 1.1.0   # 基于已发布版本出新版
  build_suite_bundle.py --ref <commit> --out <path.zip> --namespace <命名空间>
退出码：0 = 已出包；1 = 校验失败（stderr 给原因）。
"""
import argparse
import io
import json
import re
import subprocess
import sys
import tarfile
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SUITE_SLUG = "sdlc-suite"
SUITE_NAME = "SDLC 研发全流程套件"
SUITE_SUMMARY = "需求梳理与平台定稿、技术设计、AI 测试、对抗式评审、视觉还原、上线前检查、写入红线与会话交接，覆盖研发全流程的技能套件"
ENTRY = "sdlc-platform"

# (skill, 分组, 一句话说明)。分组：flow = 按研发顺序使用；cross = 横切。列表顺序即套件成员顺序。
MEMBERS = [
    ("sdlc-platform", "flow", "在产物平台上把原始需求变成标准需求文档，并交给开发（入口，需接 sdlc-in / sdlc-out 两个 MCP）"),
    ("sdlc-intent", "flow", "本地梳理 PRD，出结构化摘要和七层体检问题清单，并做 A/B/C 风险分档"),
    ("sdlc-sync", "flow", "本地 markdown 与平台之间同步摘要、体检、答复、定稿等产物"),
    ("sdlc-design", "flow", "根据确认后的需求摘要出技术设计 design.md"),
    ("sdlc-test", "flow", "AI 测试编排，cases / dev / static / exec / spec / report 六个子命令"),
    ("sdlc-gate", "flow", "设计与用例定稿后的分档对抗式评审关卡，并检查开发入口"),
    ("sdlc-doubt", "flow", "对非平凡技术决策做全新上下文的对抗式复查"),
    ("sdlc-ui-visual", "flow", "以 Figma 或基准图为准做截图比对与分轮修复"),
    ("sdlc-release-check", "flow", "扫描相对基线分支的改动，列出上线时要手工做的配置、注册、DDL/DML 与通知（只能手动调用）"),
    ("sdlc-guardrails", "cross", "写入时按项目 guardrails.yaml 拦截红线，另有 pre-commit 兜底"),
    ("sdlc-handoff", "cross", "会话交接卡，换会话 / 换机器 / 换 agent 继续任务"),
]

NOTE = "sdlc-guardrails 的 hook、sdlc-test 的 Playwright 回归需要本机 Python / Node 环境；安装套件不会自动执行任何步骤。"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def git(*args: str) -> bytes:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
    if r.returncode:
        fail(f"git {' '.join(args)}: {r.stderr.decode(errors='replace').strip()}")
    return r.stdout


def frontmatter(text: str) -> str:
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    return m.group(1) if m else ""


def fm_value(fm: str, key: str) -> str | None:
    m = re.search(rf"^\s*{re.escape(key)}:\s*(.+?)\s*$", fm, re.M)
    return m.group(1).strip("\"'") if m else None


def q(s: str) -> str:
    """YAML 双引号标量（JSON 字符串是合法的 YAML 双引号形式）。"""
    return json.dumps(s, ensure_ascii=False)


def build_overview(meta: dict) -> str:
    lines = [f"# {SUITE_NAME}", "",
             f"{len(MEMBERS)} 个技能覆盖需求、设计、测试、评审、上线，可按需单独使用，也可整套安装。"
             "成员之间用同级相对路径互相引用，整套安装时引用都能打开。", "", "按研发顺序使用：", ""]
    flow = [m for m in MEMBERS if m[1] == "flow"]
    lines += [f"{i}. {n}（{meta[n]['display']}）：{d}" for i, (n, _, d) in enumerate(flow, 1)]
    lines += ["", "横切技能：", ""]
    lines += [f"- {n}（{meta[n]['display']}）：{d}" for n, g, d in MEMBERS if g == "cross"]
    lines += ["", f"注意事项：{NOTE}"]
    return "\n".join(lines)


def build_manifest(args, meta: dict) -> str:
    out = ["apiVersion: skillhub.iflytek.com/v1alpha1", "kind: SkillSuiteBundle", "metadata:",
           f"  namespace: {args.namespace}", f"  slug: {SUITE_SLUG}", "spec:",
           f"  mode: {args.mode}", f"  version: {q(args.version)}"]
    if args.mode == "UPDATE":
        out.append(f"  baseVersion: {q(args.base_version)}")
    out += [f"  displayName: {q(SUITE_NAME)}", f"  summary: {q(SUITE_SUMMARY)}", "  overview: |"]
    out += [f"    {l}" if l else "" for l in build_overview(meta).splitlines()]
    if args.changelog:
        out.append(f"  changelog: {q(args.changelog)}")
    out += [f"  visibility: {args.visibility}", f"  entry: {q(f'@{args.namespace}/{ENTRY}')}", "  members:"]
    for n, _, _ in MEMBERS:
        out += [f"    - skill: {q(f'@{args.namespace}/{n}')}", "      package:",
                f"        path: skills/{n}", f"        visibility: {args.visibility}"]
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="打 SkillHub Suite Bundle ZIP")
    ap.add_argument("--ref", default="HEAD", help="取 skills/ 的 git 提交（默认 HEAD）")
    ap.add_argument("--mode", choices=["CREATE", "UPDATE"], default="CREATE")
    ap.add_argument("--version", default="1.0.0", help="套件版本")
    ap.add_argument("--base-version", help="UPDATE 必填：已发布的基线套件版本")
    ap.add_argument("--changelog", help="版本说明（可选）")
    ap.add_argument("--namespace", default="global")
    ap.add_argument("--visibility", choices=["PUBLIC", "NAMESPACE_ONLY", "PRIVATE"], default="PUBLIC")
    ap.add_argument("--out", help="输出 ZIP（默认 outputs/sdlc-suite-bundle-<版本>.zip）")
    args = ap.parse_args()

    if args.mode == "UPDATE" and not args.base_version:
        fail("--mode UPDATE 需要 --base-version（已发布的基线套件版本）")
    if args.mode == "UPDATE" and args.base_version == args.version:
        fail("--version 不能等于 --base-version")

    names = [n for n, _, _ in MEMBERS]
    market = json.loads(git("show", f"{args.ref}:.claude-plugin/marketplace.json"))
    market_names = [Path(p).name for p in market["plugins"][0]["skills"]]
    if sorted(names) != sorted(market_names):
        fail(f"MEMBERS 与 marketplace.json 不一致：多 {sorted(set(names) - set(market_names))}，"
             f"缺 {sorted(set(market_names) - set(names))}")
    if ENTRY not in names:
        fail(f"入口 {ENTRY} 不在 MEMBERS 里")

    meta = {}
    for n in names:
        fm = frontmatter(git("show", f"{args.ref}:skills/{n}/SKILL.md").decode("utf-8"))
        if fm_value(fm, "name") != n:
            fail(f"skills/{n}/SKILL.md 的 name 与目录名不一致")
        meta[n] = {"display": fm_value(fm, "display-name") or n, "version": fm_value(fm, "version")}
        if not meta[n]["version"]:
            print(f"WARN: {n} 没有 metadata.version，SkillHub 会生成时间版本", file=sys.stderr)

    if args.ref == "HEAD" and git("status", "--porcelain", "--", "skills", ".claude-plugin").strip():
        print("WARN: skills/ 有未提交改动，本包只含 HEAD 的内容", file=sys.stderr)

    out = Path(args.out) if args.out else ROOT / "outputs" / f"sdlc-suite-bundle-{args.version}.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    tar = tarfile.open(fileobj=io.BytesIO(git("archive", "--format=tar", "--prefix=skills/", f"{args.ref}:skills")))
    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("SUITE.yaml", build_manifest(args, meta))
        for m in tar.getmembers():
            if not m.isfile() or m.name.split("/")[1] not in names:
                continue
            info = zipfile.ZipInfo(m.name, date_time=time.localtime(m.mtime)[:6])
            info.external_attr = (0o100000 | m.mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, tar.extractfile(m).read())
            count += 1

    ref = git("rev-parse", "--short", args.ref).decode().strip()
    print(f"OK: {out}（{args.mode} {SUITE_SLUG}@{args.version}，{len(names)} 个成员 / {count} 个文件，来自 {ref}）")
    for n in names:
        print(f"  {'*' if n == ENTRY else ' '} {n} {meta[n]['version'] or '(时间版本)'}")


if __name__ == "__main__":
    main()

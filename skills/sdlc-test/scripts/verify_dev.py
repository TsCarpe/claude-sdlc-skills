#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""开发完成验证编排(compile/boot/冒烟/回归的确定性执行与留档)。

分工边界:冒烟清单 sdlc/<需求名>/dev/smoke.md 由 agent 在 /sdlc-test dev 第①步
从 cases.md P0/核心用例推导落盘(计划-验证-执行:本脚本只验证结构并执行,不做
推导);复杂业务断言(落库/权限)不在此——留 exec 阶段四类证据。

配置(sdlc/env/,模板见 references/env-template.md「开发验证档」):
    sdlc/env/dev.md           项目级入库:模式/构建/启动/冒烟/回归 五节
    sdlc/env/dev-auth.local.md  gitignored 本机供给,「头名: 值」逐行;免鉴权时不需要

用法:
    python3 verify_dev.py <项目根> <需求名>

执行编排(设计内失败:任一步失败即停后续步,仍完整留档后 exit 1;未预期异常:
先兜底写「验证状态=未通过(异常中断)」留档、服务停止由 finally 保证,然后异常
向上传播(exit 非零,guard_exec 检查 5 反查留档可见而非仅崩溃无档)):
  0. 前置校验:cases.md 存在;风险分级三口径(经 _shared.tier_three_ways,与
     guard_exec 检查 2.5 同源);env 必填键齐;A/B 级另要求回归命令非空、
     smoke.md 存在且条目全部可解析(断言语法/来源引用在构建前快失败)、
     来源 用例.TC-xx 在 cases.md 存在;需鉴权但 local 文件缺失 → 拒
  1. 构建(超时默认 600s)
  2. 启动:local 模式本地起服务(日志落 dev/boot-<日期>[-rN].log)后轮询健康;
     unmanaged 模式跳过起停、直接探测 env 配置的目标(服务由外部供给——
     用户手起/IDE/远程 dev 环境;仍是机器验证,非人工声明)
  3. 冒烟(A/B 级):按 smoke.md 文件序逐条执行(前条数据后条可用),单条失败
     不中断后续,全量留档
  4. 回归(A/B 级,超时同构建)
  5. 停服务(finally:进程组 SIGTERM→10s→SIGKILL;启动命令勿自行 nohup/disown,
     后台化由本脚本负责;多服务写单条复合启动命令,同一进程组统一清理)
  6. 留档 dev/verify-<日期>[-rN].md(同日重跑 -r2/-r3,跨日重置):头部 kv
     (验证状态/风险分级/启动模式/执行范围/验证时 HEAD/开发放行守卫/boot 日志)
     + 正文逐步命令+exit/耗时+输出尾部+冒烟逐条表

超时默认值依据(防巫术常量,env/dev.md 可覆盖):构建/回归 600s(Maven 全量
构建典型量级)、启动等待 120s(Spring Boot 启动典型上限)、轮询间隔 2s、
单次健康探测 5s、单次冒烟请求 30s。

降级边界:C 级 = 步 1-2(compile+boot);命令按整串 shell 执行(信任模型同
Makefile,来源为入库配置);无 git 时 HEAD 记「未知(降级)」;开发放行守卫
(guard_dev.py)尽力调用——同仓库安装 sdlc-gate 时留档记录其结果,未安装记
「未检」,不硬依赖。
"""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import _shared

OK, NG = "✅", "🔴"
BUILD_TIMEOUT = 600      # 构建/回归上限(s),env「超时秒」可覆盖
HEALTH_WAIT = 120        # 启动后健康等待上限(s)
POLL_INTERVAL = 2        # 健康轮询间隔(s)
PROBE_TIMEOUT = 5        # 单次健康探测超时(s)
SMOKE_TIMEOUT = 30       # 单次冒烟请求超时(s)
KILL_GRACE = 10          # SIGTERM 后等待进程退出(s)

SEC = re.compile(r"^##\s*(.+?)\s*$")
KV = re.compile(r"^-\s*([^：:]+?)\s*[：:]\s*(.*)$")
SM_HEAD = _shared.SM_HEAD  # 冒烟条目标题(编号后至少一空白,名称可空)——与 guard_exec 检查 5 计数同源,改口径须两侧同步
VAR = re.compile(r"\{\{\s*(\w+)\s*\}\}")
ASSERT_TOKEN = re.compile(
    r'\s*(?:HTTP\s*(\d+)|code\s*=\s*(\d+)|包含\s*["“]([^"”]+)["”]|存\s+(\w+)\s*←\s*([\w.]+))\s*(?:且|$)')


def tail_of(text: str, n: int = 30) -> str:
    lines = (text or "").splitlines()
    return "\n".join(lines[-n:])


def parse_env(path: Path, root: Path) -> tuple[dict | None, list[str]]:
    if not path.is_file():
        return None, [f"sdlc/env/dev.md 不存在——按 references/env-template.md「开发验证档」创建后重跑"]
    cfg: dict[str, str] = {}
    sec = ""
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = SEC.match(ln)
        if m:
            sec = m.group(1)
            continue
        kv = KV.match(ln.strip())
        if kv:
            cfg[f"{sec}/{kv.group(1)}"] = kv.group(2).strip()
    return cfg, []


def parse_auth(path: Path) -> dict[str, str]:
    headers: dict[str, str] = {}
    if not path.is_file():
        return headers
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        kv = KV.match(ln.strip())
        if kv is None:  # env-template dev-auth「头名: 值」逐行形态(无 - 前缀)同样接受
            kv = re.match(r"^([^：:]+?)\s*[：:]\s*(.+)$", ln.strip())
        if kv:
            headers[kv.group(1).strip()] = kv.group(2).strip()
    return headers


def tokenize_asserts(expr: str) -> tuple[list[tuple], list[str]]:
    asserts: list[tuple] = []
    errs: list[str] = []
    pos, s = 0, expr.strip()
    while pos < len(s):
        m = ASSERT_TOKEN.match(s, pos)
        if not m:
            # 点路径含数组下标(data.items[0].id)会令整条断言 match 失败——单独点名,不给笼统的语法非法
            sm = re.match(r"\s*存\s+\w+\s*←\s*([\w.]+)(\[[^\s且]*)", s[pos:])
            if sm:
                errs.append(f"点路径暂不支持数组下标({sm.group(1) + sm.group(2)}),"
                            f"请改用可从对象直取的扁平字段")
            else:
                errs.append(f"断言语法非法:{s[pos:].strip()!r}"
                            f"(合法:HTTP <n> / code=<n> / 包含\"<文本>\" / 存 <变量> ← <点路径>,「且」连接)")
            break
        if m.group(1) is not None:
            asserts.append(("http", int(m.group(1))))
        elif m.group(2) is not None:
            asserts.append(("code", int(m.group(2))))
        elif m.group(3) is not None:
            asserts.append(("contains", m.group(3)))
        else:
            asserts.append(("store", m.group(4), m.group(5)))
        pos = m.end()
    return asserts, errs


def parse_smoke(path: Path) -> tuple[list[dict], list[str], set[int]]:
    """返回 (条目列表, 错误清单, 不适用 P0 编号集)。头部(首个 SM 标题前)的
    「不适用 P0」表格行在此收集(值恰为「无」视为全部适用,空集)。"""
    entries: list[dict] = []
    errs: list[str] = []
    waived: set[int] = set()
    cur: dict | None = None
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = SM_HEAD.match(ln)
        if m:
            cur = {"id": m.group(1), "name": m.group(2).strip()}
            entries.append(cur)
            continue
        if cur is None:
            wm = re.match(r"^\|\s*不适用\s*P0\s*\|\s*([^\|]+)", ln.strip())
            if wm:  # 头部「不适用 P0」清单:TC-xx:原因;… ;全部适用写「无」
                val = wm.group(1).strip()
                # 精确匹配:值恰为「无」=全部适用;子串匹配会把含「无」字的原因
                # (如「TC-01: 无前置数据环境」)误判成全部适用、静默丢弃整张豁免清单
                if val != "无":
                    waived = {int(x) for x in re.findall(r"TC-(\d+)", val)}
            continue
        kv = KV.match(ln.strip())
        if not kv:
            continue
        k, v = kv.group(1).strip(), kv.group(2).strip()
        if k == "请求":
            mm = re.fullmatch(r"(GET|POST|PUT|PATCH|DELETE)\s+(\S+)", v)
            if mm:
                cur["method"], cur["url"] = mm.group(1), mm.group(2)
            else:
                errs.append(f"{cur['id']} 「请求」行非法:{v!r}(须『METHOD /path』,path 相对 base URL)")
        elif k == "请求体":
            cur["body"] = v
        elif k == "预期":
            cur["expect"] = v
        elif k == "来源":
            cur["source"] = v
    for e in entries:
        if "method" not in e:
            errs.append(f"{e['id']} 缺「请求」行")
        if not e.get("expect"):
            errs.append(f"{e['id']} 缺「预期」行")
        else:
            a, ae = tokenize_asserts(e["expect"])
            e["asserts"] = a
            if not a:
                errs.append(f"{e['id']} 预期未解析出任何断言:{e['expect']!r}")
            errs.extend(f"{e['id']} {x}" for x in ae)
        if not e.get("source"):
            errs.append(f"{e['id']} 缺「来源」行")
    return entries, errs, waived


def check_sources(entries: list[dict], cases_text: str) -> list[str]:
    errs = []
    for e in entries:
        m = re.fullmatch(r"用例\.TC-(\d+)", e.get("source", ""))
        if not m:
            errs.append(f"{e['id']} 「来源」格式非法:{e.get('source')!r}(须『用例.TC-xx』)")
        elif not re.search(rf"\bTC-0*{int(m.group(1))}\b", cases_text):
            errs.append(f"{e['id']} 来源 {e['source']} 在 cases.md 中不存在——核对冒烟清单来源引用")
    return errs


def check_vars(entries: list[dict]) -> list[str]:
    """{{变量}} 闭包校验:URL/请求体/预期中引用的变量须由前序条目『存 v ← …』定义
    (条目有序,前条数据后条可用;本条「存」定义的变量要到后条才可引用)。"""
    errs: list[str] = []
    defined: set[str] = set()
    for e in entries:
        refs: set[str] = set()
        for s in (e.get("url", ""), e.get("body", ""), e.get("expect", "")):
            refs |= set(VAR.findall(s or ""))
        for v in sorted(refs - defined):
            errs.append(f"{e['id']} 冒烟变量未定义:{{{{{v}}}}},"
                        f"请检查『存 {v} ← …』条目顺序(条目有序,前条数据后条可用)")
        defined |= {a[1] for a in e.get("asserts", []) if a[0] == "store"}
    return errs


def extract_p0_cases(cases_text: str) -> set[int]:
    """提取 cases.md 的 P0 用例编号:用例总览表行(第 3 列优先级=P0)+ 明细小节标题
    下的「优先级:P0」行,两形态并集;解析不出(格式不识别或确无 P0)返回空集,调用方记 note 跳过。"""
    ids: set[int] = set()
    for m in re.finditer(r"^\|\s*TC-(\d+)\s*\|[^|]*\|\s*P0\b", cases_text, re.M):
        ids.add(int(m.group(1)))
    cur: int | None = None
    for ln in cases_text.splitlines():
        m = re.match(r"^#{1,6}\s+TC-(\d+)\b", ln)
        if m:
            cur = int(m.group(1))
        elif ln.startswith("#"):
            cur = None
        elif cur is not None and re.search(r"优先级[：:]\s*P0\b", ln):
            ids.add(cur)
    return ids


def auth_gitignore_state(root: Path) -> str:
    """dev-auth.local.md 的 git 忽略状态:ignored / not-ignored / unknown
    (非 git 仓库、git 不可得或异常——一律降级,不拦)。"""
    target = root / "sdlc" / "env" / "dev-auth.local.md"
    try:
        p = subprocess.run(["git", "check-ignore", "-q", str(target)],
                           cwd=root, capture_output=True, timeout=15)
    except Exception:
        return "unknown"
    if p.returncode == 0:
        return "ignored"
    if p.returncode == 1:
        return "not-ignored"
    return "unknown"  # 128=非 git 仓库等


def run_step(cmd: str, timeout: int) -> tuple[bool, str, str]:
    t0 = time.time()
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, timeout=timeout)
        out = (p.stdout or b"").decode("utf-8", "replace")
        return p.returncode == 0, f"exit={p.returncode},耗时 {int(time.time() - t0)}s", tail_of(out)
    except subprocess.TimeoutExpired as e:
        out = e.output if isinstance(e.output, str) else (e.output or b"").decode("utf-8", "replace")
        return False, f"超时(上限 {timeout}s)", tail_of(out)


def boot_service(cmd: str, log_path: Path) -> subprocess.Popen:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(log_path, "wb")
    try:
        proc = subprocess.Popen(cmd, shell=True, stdout=fh, stderr=subprocess.STDOUT,
                                start_new_session=True)
    except BaseException:
        fh.close()  # Popen 失败(命令/环境异常)时日志句柄不悬空,关闭后重抛
        raise
    proc._log_fh = fh  # 停服务时一并关闭(见 stop_service)
    return proc


def wait_health(url: str, max_wait: int) -> tuple[bool, str]:
    deadline, n, last, t0 = time.time() + max_wait, 0, "", time.time()
    while time.time() < deadline:
        n += 1
        try:
            with urllib.request.urlopen(url, timeout=PROBE_TIMEOUT) as resp:
                if 200 <= resp.status < 300:
                    return True, f"第 {n} 次探测就绪,耗时 {int(time.time() - t0)}s"
                last = f"HTTP {resp.status}"
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
        except Exception as e:  # URLError / timeout 等:计为一次失败探测
            last = str(e)
        time.sleep(POLL_INTERVAL)
    return False, f"超时(上限 {max_wait}s,共 {n} 次探测,最后:{last})"


def stop_service(proc: subprocess.Popen | None) -> None:
    """幂等:进程未退→进程组 SIGTERM→宽限→SIGKILL;已退/重复调用→直接善后日志句柄返回。"""
    if proc is None:
        return
    try:
        if proc.poll() is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                try:
                    proc.wait(timeout=KILL_GRACE)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    proc.wait(timeout=5)
            except (ProcessLookupError, PermissionError):
                pass
    finally:
        fh = getattr(proc, "_log_fh", None)
        if fh:
            proc._log_fh = None  # 置空保证重复调用幂等
            try:
                fh.close()
            except OSError:
                pass


def interp(s: str, variables: dict[str, str]) -> str:
    return VAR.sub(lambda m: variables.get(m.group(1), m.group(0)), s)


def dig(obj, path: str) -> tuple[object, bool, str]:
    """按点路径取值。不支持数组下标:中途遇数组时返回明确原因(供留档断言明细),
    而非笼统的「路径不存在」;路径末段本身是数组则整体返回(允许存数组)。"""
    cur = obj
    segs = path.split(".")
    for i, seg in enumerate(segs):
        if isinstance(cur, list):
            bad = ".".join(segs[:i])
            return None, False, f"路径 {bad} 为数组(点路径暂不支持数组下标),请改用可从对象直取的扁平字段"
        if isinstance(cur, dict) and seg in cur:
            cur = cur[seg]
        else:
            return None, False, ""
    return cur, True, ""


def run_smoke_entry(e: dict, base_url: str, headers: dict[str, str],
                    variables: dict[str, str]) -> tuple[bool, str]:
    url = base_url.rstrip("/") + "/" + interp(e["url"], variables).lstrip("/")
    body = interp(e.get("body", ""), variables) if e.get("body") else ""
    data = body.encode("utf-8") if (body and e["method"] in ("POST", "PUT", "PATCH")) else None
    req = urllib.request.Request(url, data=data, method=e["method"], headers=headers)
    try:
        try:
            with urllib.request.urlopen(req, timeout=SMOKE_TIMEOUT) as resp:
                status, raw = resp.status, resp.read()
        except urllib.error.HTTPError as err:
            status, raw = err.code, err.read()
    except Exception as ex:
        return False, f"连接失败:{ex}"
    text = raw.decode("utf-8", "replace")
    try:
        rjson = json.loads(text)
    except Exception:
        rjson = None
    ok, detail = True, []
    for a in e.get("asserts", []):
        kind = a[0]
        if kind == "http":
            good = status == a[1]
            detail.append(f"HTTP={status}" if good else f"HTTP 预期 {a[1]} 实际 {status}")
        elif kind == "code":
            got = rjson.get("code") if isinstance(rjson, dict) else None
            good = got is not None and str(got).strip() == str(a[1]).strip()  # 归一化比较:"0" 与 0 等值
            detail.append(f"code={got}" if good else f"code 预期 {a[1]} 实际 {got}")
        elif kind == "contains":
            good = a[1] in text
            detail.append(f"包含\"{a[1]}\"=命中" if good else f"包含\"{a[1]}\"=未命中")
        else:  # store
            val, found, why = dig(rjson, a[2])
            good = found
            if good:
                variables[a[1]] = val if isinstance(val, str) else json.dumps(val, ensure_ascii=False)
            detail.append(f"存 {a[1]}←{a[2]}" if good else f"存 {a[1]}←{a[2]} {why or '路径不存在'}")
        if not good:
            ok = False
    return ok, ", ".join(detail)


def gate_guard_note(root: Path, req: str) -> str:
    script = Path(__file__).resolve().parents[2] / "sdlc-gate" / "scripts" / "guard_dev.py"
    if not script.is_file():
        return "未检(sdlc-gate 未安装)"
    try:
        p = subprocess.run([sys.executable, str(script), str(root), req],
                           capture_output=True, timeout=30)
        out = (p.stdout or b"").decode("utf-8", "replace").strip()
        if p.returncode == 0:
            m = re.search(r"(issues-[\w.-]+\.md)", out)
            return f"已放行({m.group(1)})" if m else "已放行(文件名未识别)"
        return f"未过(exit={p.returncode})"
    except Exception:
        return "未检(调用失败)"


def next_name(dev_dir: Path, date: str) -> tuple[str, str]:
    existing = list(dev_dir.glob(f"verify-{date}*.md"))
    maxr = max((int(m.group(1)) for p in existing
                if (m := re.search(r"-r(\d+)$", p.stem))), default=0)
    n = maxr + 1 if maxr else (2 if existing else 1)
    suffix = "" if n == 1 else f"-r{n}"
    return f"verify-{date}{suffix}.md", f"boot-{date}{suffix}.log"


def write_archive(dev_dir: Path, vname: str, req: str, tier: str, mode: str,
                  full: bool, status: str, gate: str, head: str, boot_log: str,
                  sections: list[tuple[str, list[str]]]) -> Path:
    """boot_log:local 模式实际 boot 日志文件名(交叉校验锚点);unmanaged / 未起服务记「-」。"""
    today = time.strftime("%Y-%m-%d")
    scope = "compile+boot+冒烟+回归(全量)" if full else "compile+boot(C 级)"
    lines = [f"# {req} 开发完成验证 {today}",
             "",
             "| 项 | 值 |",
             "|---|---|",
             f"| 验证状态 | {status} |",
             f"| 风险分级 | {tier} |",
             f"| 启动模式 | {mode} |",
             f"| 执行范围 | {scope} |",
             f"| 验证时 HEAD | {head} |",
             f"| 开发放行守卫 | {gate} |",
             f"| boot 日志 | {boot_log} |",
             "",
             "> 留档正文含命令输出尾部;对外分享前注意响应片段脱敏(去手机号/token 类字段)。"]
    for title, body in sections:
        lines += ["", f"## {title}"] + body
    path = dev_dir / vname
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def fail_pre(msgs: list[str]) -> int:
    print(NG + " 开发完成验证前置校验未过,先处理以下问题:")
    for m in msgs:
        print("  - " + m)
    print("(补救:A/B 级先跑 /sdlc-test dev 第①步从 cases.md 生成 smoke.md、按 "
          "references/env-template.md「开发验证档」补齐 sdlc/env/dev.md;分级取 cases.md 头「风险分级」)")
    return 1


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    root, req = Path(sys.argv[1]).resolve(), sys.argv[2]
    base = root / "sdlc" / req
    dev_dir = base / "dev"
    cases = base / "test" / "cases.md"

    # ---- 步 0 前置校验 ----
    pre: list[str] = []
    if not cases.is_file():
        return fail_pre([f"用例文件不存在:{base.relative_to(root) / 'test' / 'cases.md'}——先跑 /sdlc-test cases"])
    cases_text = cases.read_text(encoding="utf-8", errors="replace")
    tier, notes, terrs = _shared.tier_three_ways(cases_text, _shared.latest_digest(root, req),
                                                 base / "review")
    pre += terrs
    if tier is None and not terrs:
        tier = "A"  # 未标注按 A 级(存量兼容)
    full = tier in ("A", "B")
    env, env_errs = parse_env(root / "sdlc" / "env" / "dev.md", root)
    pre += env_errs
    mode = (env or {}).get("模式/启动模式", "")
    if env is not None and mode not in ("local", "unmanaged"):
        pre.append("sdlc/env/dev.md「模式/启动模式」缺失或非法(合法:local | unmanaged)")
    cfg = env or {}
    build_cmd = cfg.get("构建/命令", "")
    health_url = cfg.get("启动/健康探测", "")
    if env is not None:
        if not build_cmd:
            pre.append("sdlc/env/dev.md 缺「构建/命令」——按「开发验证档」补齐")
        if not health_url:
            pre.append("sdlc/env/dev.md 缺「启动/健康探测」——按「开发验证档」补齐")
        else:
            u = urlparse(health_url)  # 步 0 快失败,不再让轮询 120s 慢失败
            if u.scheme not in ("http", "https") or not u.netloc:
                pre.append(f"sdlc/env/dev.md「启动/健康探测」URL 非法:{health_url!r}"
                           f"(须 http(s)://<host>[:port]/<path>)")
        if mode == "local" and not cfg.get("启动/命令"):
            pre.append("sdlc/env/dev.md 缺「启动/命令」(local 模式必填;本地起不来服务改用 unmanaged)")
        for k in ("构建/超时秒", "回归/超时秒", "启动/最大等待秒"):
            v = cfg.get(k, "")
            if v:
                try:
                    int(v)  # 快失败:不让运行期裸 ValueError 崩 traceback
                except ValueError:
                    pre.append(f"sdlc/env/dev.md「{k}」值非法:{v!r}(须为整数秒数)")
    entries: list[dict] = []
    base_url = cfg.get("冒烟/base URL", "")
    auth_headers: dict[str, str] = {}
    smoke_count = 0
    if env is not None and full:
        if not base_url:
            pre.append("sdlc/env/dev.md 缺「冒烟/base URL」(A/B 级必填)")
        if not cfg.get("回归/命令"):
            pre.append("sdlc/env/dev.md 缺「回归/命令」(A/B 级必填,须为真实测试套件入口——占位命令=空转)")
        auth_mode = cfg.get("冒烟/鉴权", "")
        if not auth_mode:
            pre.append("sdlc/env/dev.md 缺「冒烟/鉴权」(合法:免鉴权 或 dev-auth.local.md)")
        elif auth_mode != "免鉴权":
            auth_headers = parse_auth(root / "sdlc" / "env" / "dev-auth.local.md")
            if not auth_headers:
                pre.append("冒烟需鉴权但 sdlc/env/dev-auth.local.md 不存在或为空"
                           "(本机供给「头名: 值」逐行;依赖项目 .gitignore 含 sdlc/env/*.local.md)")
            else:
                gi = auth_gitignore_state(root)
                if gi == "not-ignored":
                    pre.append("sdlc/env/dev-auth.local.md 未被 .gitignore 忽略——"
                               "项目 .gitignore 需含 sdlc/env/*.local.md(防鉴权真值入库),补齐后重跑")
                elif gi == "unknown":
                    notes.append("git check-ignore 不可得(非 git 仓库/命令缺失)——"
                                 "dev-auth.local.md 忽略状态未核,人工确认 .gitignore 含 sdlc/env/*.local.md")
        smoke = base / "dev" / "smoke.md"
        if not smoke.is_file():
            pre.append(f"冒烟清单不存在:{base.relative_to(root) / 'dev' / 'smoke.md'}"
                       f"——先跑 /sdlc-test dev 第①步从 cases.md P0/核心用例推导生成")
        else:
            entries, serrs, waived = parse_smoke(smoke)
            smoke_count = len(entries)
            pre += serrs
            pre += check_sources(entries, cases_text)
            pre += check_vars(entries)
            # P0 覆盖核对:每个 P0 用例须有 SM 条目(来源引用)或在头部「不适用 P0」声明,防静默缩面
            p0_ids = extract_p0_cases(cases_text)
            if not p0_ids:
                notes.append("cases.md 未解析出 P0 用例(总览表/明细优先级行未命中,或确无 P0)——P0 覆盖核对跳过")
            else:
                covered = {int(m.group(1)) for e in entries
                           if (m := re.fullmatch(r"用例\.TC-(\d+)", e.get("source", "")))}
                for n in sorted(p0_ids - covered - waived):
                    pre.append(f"P0 用例 TC-{n} 既无冒烟条目也未声明不适用,禁止静默缩面"
                               f"——补『来源: 用例.TC-{n}』的 SM 条目,或在 smoke.md 头部「不适用 P0」逐条列原因")
    if pre:
        return fail_pre(pre)
    for n in notes:
        print(f"{OK} {n}")

    build_to = int(cfg.get("构建/超时秒", BUILD_TIMEOUT) or BUILD_TIMEOUT)
    regress_to = int(cfg.get("回归/超时秒", BUILD_TIMEOUT) or BUILD_TIMEOUT)
    health_wait = int(cfg.get("启动/最大等待秒", HEALTH_WAIT) or HEALTH_WAIT)
    regress_cmd = cfg.get("回归/命令", "")
    boot_cmd = cfg.get("启动/命令", "")

    date = time.strftime("%Y%m%d")
    vname, bname = next_name(dev_dir, date)
    sections: list[tuple[str, list[str]]] = []
    fail_step: str | None = None
    proc = None

    # ---- 步 1 构建 ----
    print(f"[构建] 命令:{build_cmd}")
    ok, det, tail = run_step(build_cmd, build_to)
    print(f"{'✅ 构建通过' if ok else '🔴 构建失败'}({det})")
    sections.append(("1 构建", [f"- 命令:`{build_cmd}`", f"- 结果:{'✅' if ok else '🔴'} {det}",
                                "- 输出尾部:", "````", tail, "````"]))
    if not ok:
        fail_step = "构建失败"

    # 步 2-4 包 try/except/finally:正常/KeyboardInterrupt/未预期异常路径都保证服务被停
    # (见 docstring 步 5);未预期异常另兜底留档「异常中断」后再向上传播
    try:
        # ---- 步 2 启动/健康 ----
        if fail_step is None:
            body = [f"- 模式:{mode}", f"- 健康探测:{health_url}(单次 {PROBE_TIMEOUT}s,间隔 {POLL_INTERVAL}s)"]
            if mode == "local":
                print(f"[启动] 命令:{boot_cmd}")
                proc = boot_service(boot_cmd, dev_dir / bname)
                time.sleep(1)
                if proc.poll() is not None:
                    log_tail = tail_of((dev_dir / bname).read_text(encoding="utf-8", errors="replace"))
                    print(f"🔴 启动失败(进程即退,exit={proc.returncode}),日志 {bname}")
                    body += [f"- 命令:`{boot_cmd}`", f"- 结果:🔴 进程即退(exit={proc.returncode})",
                             f"- 日志:{bname}", "- 日志尾部:", "````", log_tail, "````"]
                    fail_step = "启动失败"
            if fail_step is None:
                ok2, det2 = wait_health(health_url, health_wait)
                print(f"{'✅ 服务就绪' if ok2 else '🔴 健康探测未过'}({det2})")
                body.append(f"- 结果:{'✅' if ok2 else '🔴'} {det2}")
                if mode == "local":
                    body.append(f"- 日志:{bname}")
                if not ok2:
                    fail_step = "健康探测超时" if mode != "local" else "健康探测超时(启动失败或未就绪)"
            sections.append(("2 启动", body))

        # ---- 步 3 冒烟(A/B 级) ----
        if fail_step is None and full:
            variables: dict[str, str] = {}
            rows = ["| SM | 名称 | 结果 | 断言明细 | 来源 |", "|---|---|---|---|---|"]
            npass = 0
            for e in entries:
                ok3, det3 = run_smoke_entry(e, base_url, auth_headers, variables)
                npass += 1 if ok3 else 0
                print(f"{'✅' if ok3 else '🔴'} {e['id']} {e['name']} {'通过' if ok3 else '失败'}({det3})")
                rows.append(f"| {e['id']} | {e['name']} | {'✅' if ok3 else '🔴'} | {det3} | {e['source']} |")
                if not ok3:
                    fail_step = "冒烟失败"
            print(f"[冒烟] {npass}/{len(entries)} 条通过")
            sections.append((f"3 冒烟(共 {len(entries)} 条,{npass} 条通过)", rows))

        # ---- 步 4 回归(A/B 级) ----
        if fail_step is None and full:
            print(f"[回归] 命令:{regress_cmd}")
            ok4, det4, tail4 = run_step(regress_cmd, regress_to)
            print(f"{'✅ 回归通过' if ok4 else '🔴 回归失败'}({det4})")
            sections.append(("4 回归", [f"- 命令:`{regress_cmd}`", f"- 结果:{'✅' if ok4 else '🔴'} {det4}",
                                        "- 输出尾部:", "````", tail4, "````"]))
            if not ok4:
                fail_step = "回归失败"
    except BaseException as ex:  # noqa: BLE001 —— 未预期异常兜底留档后重抛(含 KeyboardInterrupt)
        head = _shared.git_head(root)
        gate = gate_guard_note(root, req)
        sections.append(("异常中断", [f"- 异常:{type(ex).__name__}: {ex}",
                                     "- 服务停止由 finally 保证;留档后异常向上传播"]))
        boot_log_field = bname if (mode == "local" and proc is not None) else "-"
        write_archive(dev_dir, vname, req, tier, mode, full,
                      f"未通过(异常中断:{type(ex).__name__})", gate, head,
                      boot_log_field, sections)
        raise
    finally:
        # ---- 步 5 停服务(finally 统一出口;stop_service 幂等,正常路径不会双重停止) ----
        if proc is not None:
            stop_service(proc)

    # ---- 步 6 留档 ----
    head = _shared.git_head(root)
    gate = gate_guard_note(root, req)
    today = time.strftime("%Y-%m-%d")
    status = f"通过({today})" if fail_step is None else f"未通过({fail_step})"
    env_note = f"sdlc/env/dev.md ｜ 冒烟清单 smoke.md({smoke_count} 条)" if full else "sdlc/env/dev.md"
    sections.append(("环境", [f"- 配置:{env_note}", f"- 开发放行守卫:{gate}", f"- 验证时 HEAD:{head}"]))
    boot_log_field = bname if (mode == "local" and proc is not None) else "-"  # local 实际日志名/其余记「-」
    path = write_archive(dev_dir, vname, req, tier, mode, full, status, gate, head,
                         boot_log_field, sections)
    if fail_step is None:
        print(f"{OK} 开发完成验证通过({tier} 级:{'全量' if full else 'compile+boot'}),留档:{path}")
        return 0
    print(f"{NG} 开发完成验证未通过({fail_step}),留档:{path}——按留档失败步修复后重跑本命令(新轮次留档)")
    return 1


if __name__ == "__main__":
    sys.exit(main())

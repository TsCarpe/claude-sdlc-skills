---
name: sdlc-guardrails
description: Deterministic guardrail engine that enforces "write-it-and-it's-wrong" red-lines at write time - a PostToolUse hook runs engine/check.py on every Write/Edit and blocks violations per project-defined guardrails.yaml rules (forbid / require / require_if / count_ge), with pre-commit fallback and --check baseline scanning for legacy code. Engine is mechanism (one global copy), rules are content (per project). Use when 接入或配置红线拦截、给项目编写 guardrails 规则、排查 hook 拦截了或没拦、扫描存量违规基线，或用户说 guardrails、红线引擎、红线拦截、接入红线、规则文件、红线扫描、baseline scan。
---

# sdlc-guardrails：红线拦截引擎

把「写了就是错」的服从性规则从文档下沉为**写文件瞬间的确定性拦截**：引擎全局一份（本 skill 的 `engine/check.py`），规则各项目自写（`.claude/guardrails.yaml`），无规则文件 = no-op。

## 何时用

- 新项目接入红线拦截（下方三步接入）
- 为已接入项目增删规则、调整 glob 与规则类型
- 排障：为什么拦了 / 为什么没拦
- 存量代码违规基线扫描（旧账出报告，不阻塞编辑）

## 架构（引擎与规则分离）

| 侧 | 内容 | 载体 |
|---|---|---|
| 引擎（机制） | 检查逻辑，python3 零项目知识 | `engine/check.py`，随 skill 装到用户级 `~/.claude/skills/sdlc-guardrails/` |
| 规则（内容） | 各项目的红线 | 项目 `.claude/guardrails.yaml`，从被检文件向上逐级查找 |

规则四类：`forbid`（出现即违规）/ `require`（至少出现一次）/ `require_if`（命中 `when` 则 `pattern` 必须出现）/ `count_ge`（`pattern` 计数 ≥ `anchor` 计数）。字段写法与样例见 [README.md](README.md)。

## 三步接入（脆弱操作：按序执行，不给发挥空间）

1. **挂载 hook**：把 [templates/settings-hook.json](templates/settings-hook.json) 的 `hooks` 段合并进项目 `.claude/settings.json`（保留已有事件），引擎路径用安装位置 `~/.claude/skills/sdlc-guardrails/engine/check.py`（`npx skills add` 全局安装即在此；`~` 不展开则改用 `$HOME`）
2. **写规则文件**：项目根 `.claude/guardrails.yaml`——不凭空编规则，从用户红线清单或 [README.md](README.md) 样例起步
3. **pipe-test 实测（反馈环，必做）**：写一个故意违规的文件，执行

   ```bash
   echo '{"tool_input":{"file_path":"<违规文件绝对路径>"}}' \
     | python3 ~/.claude/skills/sdlc-guardrails/engine/check.py
   ```

   预期输出 `{"decision":"block",...}`。**未实测拦截就宣布接入完成 = 失败**。

## 日常操作

| 需求 | 动作 |
|---|---|
| 增删规则 | 编辑项目 `guardrails.yaml`，每次写入即时生效；改完 pipe-test 复验一条 |
| Edit 存量文件 | 引擎只查本次新增文本，存量旧账不阻塞编辑者 |
| 存量基线报告 | 执行 `python3 <引擎路径> --check <文件...>`（违规 exit 1，人类可读输出） |
| git 提交兜底 | 复制 [templates/pre-commit](templates/pre-commit) 到 `.githooks/`，执行 `git config core.hooksPath .githooks` |

## 边界与排障

- 规则纯 regex 不做 AST；类型/跨文件分析类规则不在此层，走 CI/测试期（ArchUnit 等）
- 引擎异常静默 `exit 0`，永不打断 agent 循环——排障直接跑 pipe-test 看输出，不猜
- OVAL `@Validate`↔profiles 跨文件对账：执行 `engine/audit_profiles.py`（对账工具，不是拦截器）

## 参考（一层引用）

- [README.md](README.md)：架构细则、规则语法全量、语义要点（Write/Edit 差异、no-op 行为）、已知边界
- [templates/](templates/)：settings-hook.json / pre-commit / run_regression.sh / runner 四件（回归 runner 模板，配合 sdlc-test 的 spec 资产使用）

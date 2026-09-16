# 项目侧接入指南（装完 skill 之后配什么）

> **这份文档是什么**：skill 装好只是开始——guardrails 红线拦截、回归 runner、测试环境文件都在项目侧。本文给出「每个文件配在哪、怎么来的（复制模板 / 按约定自写 / skill 首跑引导生成）、干什么用」的全景清单。方法论源项目（某 Java DDD 系统）即按此清单接入。
> **和另两份的关系**：[sdlc-workflow-landscape.md](design/sdlc-workflow-landscape.md) 讲资产为什么分层（理念），[harness/README.md](../harness/README.md) 讲引擎三步接入（细节），本文讲「一个新项目从零到全功能的操作地图」（清单）。

## 目录

- [0. 前置：全局侧（一次性）](#0-前置全局侧一次性)
- [1. harness 强制层（可选，与 skills 无耦合）](#1-harness-强制层可选与-skills-无耦合)
- [2. runner 基础设施（spec 资产化 + 回归轮）](#2-runner-基础设施spec-资产化--回归轮)
- [3. 环境配置（sdlc/env/，skill 首跑引导生成）](#3-环境配置sdlcenv-skill-首跑引导生成)
- [4. 最小配置阶梯（按需逐级上）](#4-最小配置阶梯按需逐级上)
- [5. 已知边界](#5-已知边界)

## 配置全景一图流

```mermaid
flowchart TB
    subgraph G["全局侧（一次性）"]
        G1["安装 skills<br/>项目级 .claude/skills/ 或全局 ~/.claude/skills/"]
        G2["claude-sdlc-skills 仓库 checkout<br/>（harness 引擎，被 hook 以绝对路径引用）"]
        G3["MCP 工具（可选，均带降级）"]
    end

    subgraph H["① harness 强制层（可选，与 skills 无耦合）"]
        H1["settings.json hook 段<br/>「复制模板」改 ENGINE_PATH"]
        H2["guardrails.yaml 规则集<br/>「项目自写」四类规则"]
        H3["pre-commit 兜底<br/>「复制模板」+ hooksPath"]
    end

    subgraph R["② runner 基础设施（spec 资产化 / 回归轮）"]
        R1["sdlc/ 根三件<br/>package.json · playwright.config · node_modules<br/>「复制模板」+ npm install"]
        R2["sdlc/env/runner/<br/>capture-login · spike · run_regression.sh<br/>「复制模板」，browser-state 为运行产出"]
        R1 --> R2
    end

    subgraph E["③ 环境配置"]
        E1["sdlc/env/ 四件<br/>test · repos.local · accounts.local · ui-recipe<br/>「skill 首跑引导生成」"]
    end

    G2 -. 引擎路径 .-> H1
    G2 -. 引擎路径，SDLCSKILLS_HOME 可覆盖 .-> H3
```

①②③ 三层相互独立、按需逐级上（见第 4 节阶梯）；引号内为该文件的来源。

---

## 0. 前置：全局侧（一次性）

| 项 | 怎么来 | 说明 |
|---|---|---|
| 安装 skills | `npx skills add TsCarpe/claude-sdlc-skills`（项目级 `.claude/skills/`）或 `-g`（全局 `~/.claude/skills/`） | 两种位置都行；与项目内其他工具型 skill（如任务框架）互不冲突 |
| 本仓库 checkout | `git clone` 到本机固定位置 | harness 引擎（`harness/engine/check.py`）被项目侧 hook 以**绝对路径**引用——这是项目侧配置里唯一的本机路径依赖 |
| MCP 工具（全部可选） | chrome-devtools / mysql / codegraph / YApi / lark-cli | 每个 skill 对外部依赖都声明了降级路径，缺了不炸（[降级矩阵](faq.md)） |

## 1. harness 强制层（可选，与 skills 无耦合）

红线拦截三档（入口守卫 / 写入拦截 / 提交兜底）中的后两档落在项目侧，共三个文件：

| 项目侧文件 | 怎么来的 | 作用 |
|---|---|---|
| `.claude/settings.json` 的 `PostToolUse` hooks 段 | **复制** [`harness/templates/settings-hook.json`](../harness/templates/settings-hook.json)，把 `ENGINE_PATH` 改为本机仓库 checkout 的绝对路径，合并进项目已有 hooks | Write/Edit 写文件瞬间调 `check.py` 拦红线（子代理写入同样拦） |
| `.claude/guardrails.yaml` | **项目自写**：从项目规范里挑「可 grep 机械化」的条目翻译成四类规则（forbid / require / require_if / count_ge）；写法参考 [`docs/dev-standards-reference/guardrails.example.yaml`](dev-standards-reference/guardrails.example.yaml)（20 条示例） | 规则集。知识层（怎么写对）留在项目规范文档，本文件只拦「写了就是错」 |
| `.githooks/pre-commit` | **复制** [`harness/templates/pre-commit`](../harness/templates/pre-commit)，执行一次 `git config core.hooksPath .githooks` | git commit 兜底（不经 Claude 的提交也拦）；引擎路径可用 `SDLCSKILLS_HOME` 环境变量覆盖，引擎缺失时警告放行（不阻塞未接入的同事） |

三步接入的完整细节（含 pipe-test 实测拦截）见 [harness/README.md](../harness/README.md)。

## 2. runner 基础设施（spec 资产化 + 回归轮）

sdlc-test 的 spec 资产化与回归轮依赖一套 Playwright runner，全部落在项目侧 `sdlc/` 目录：

```text
<项目根>/sdlc/
├── package.json          ← 复制 harness/templates/runner/package.json
├── playwright.config.ts  ← 复制 harness/templates/runner/playwright.config.ts（baseURL 按项目替换）
├── node_modules/         ← 在 sdlc/ 根执行 npm install（位置红线，见下）
└── env/runner/
    ├── capture-login.mjs     ← 复制 harness/templates/runner/capture-login.mjs（3 处占位符按项目替换）
    ├── spike.spec.ts         ← 复制 harness/templates/runner/spike.spec.ts（3 处占位符按项目替换）
    ├── browser-state.json    ← 运行 node capture-login.mjs 产出（SSO 登录态，gitignore）
    ├── run_regression.sh     ← 复制 harness/templates/run_regression.sh（一键回归，不占轮次号）
    └── test-results/         ← runner 运行产出（失败留痕，可随时清）
```

要点（依据与坑的完整记录见 skill 的 `references/spec/spec-guide.md`「runner 标准布局」）：

- **依赖必须装在 sdlc 根**：装在 `env/runner/` 子目录时 specs 的模块解析会命中项目根另一份 `@playwright/test` → 双树冲突（实测踩坑）
- `channel:'chrome'` 走系统 Chrome，零下载、不碰日常浏览器会话
- 模板里的占位符（`<app>`、`<list-api>`、鉴权键特征等）按项目实际替换；spike 冒烟通过 = runner 基础设施就绪
- 项目 `.gitignore` 建议三条：`sdlc/env/*.local.md`、`sdlc/env/runner/browser-state.json`（含会话凭据）、`sdlc/env/runner/test-results/`

## 3. 环境配置（sdlc/env/，skill 首跑引导生成）

这层**不需要预先手写**——sdlc-test 首次执行对应阶段时，skill 会按 [env-template.md](../skills/sdlc-test/references/env-template.md) 模板引导创建，此处只列清单：

| 文件 | 何时生成 | 内容 |
|---|---|---|
| `sdlc/env/test.md` | exec 首跑引导（入库） | 环境说明：URL / 登录方式 / 角色 / 前置数据 / 数据核验入口 |
| `sdlc/env/repos.local.md` | static 首跑引导（gitignore） | 前后端仓库本地路径与索引状态 |
| `sdlc/env/accounts.local.md` | exec 首跑引导（gitignore） | 角色 → 账号密码 |
| `sdlc/env/ui-recipe.md` | exec 首条用例侦察后沉淀（入库） | 项目特有 UI 配方：路由清单 / 环境检查恢复动作 / 鉴权直调头 / 项目特有坑；跨需求复用，持续增量回写 |

## 4. 最小配置阶梯（按需逐级上）

| 想跑什么 | 项目侧需要的配置 |
|---|---|
| sdlc-intent / sdlc-doubt / sdlc-config-review | **零配置**，装 skill 即用 |
| sdlc-test cases | 零硬配置（YApi / lark-cli 为可选增强） |
| sdlc-test static | `sdlc/env/repos.local.md` + codegraph / mysql MCP |
| sdlc-test exec | `sdlc/env/` 四份环境文件 + chrome-devtools MCP |
| spec 资产化 + 回归轮 | 第 2 节 runner 全套 |
| 红线强制拦截 | 第 1 节 harness 全套 |

两层（harness 与 runner）相互独立：只上测试不上拦截、或反之，都成立。

## 5. 已知边界

- **引擎路径是本机绝对路径**（hook 段模板的既有形态）：换机器要改 `ENGINE_PATH`；pre-commit 档可用 `SDLCSKILLS_HOME` 环境变量统一覆盖
- **`.claude/` 与 `sdlc/env/` 本地文件是否入库是项目自选**：源项目选择 gitignore（引擎路径个人化 + 账号/登录态敏感），代价是换机器或新同事要重配第 1、2 节
- runner 模板从源项目实测脚本脱敏收录（2026-09-14 试点定型），占位符替换工作量集中在 `capture-login.mjs` 的登录判定条件与 `spike.spec.ts` 的目标页锚点

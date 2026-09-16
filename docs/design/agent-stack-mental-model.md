# Agent Stack 核心概念心智模型

> 沉淀自 2026-09-15 与 Claude 的架构讨论（skill 路线 vs 调整工作流 → 概念分层 → 落地判据 → hooks/CI 机制与载体路由）。
> 用途：遇到 AI 开发栈的新概念时先归层；调整工作流时按决策流程选承载形式。
> 2026-09-16 随资产回收整理；本仓库 skills/sdlc-guardrails/ 即本文 §4「判断的留下，服从的下沉」的落地产物。

## 0. 总纲：两个桶 + 一个问题

所有层出不穷的概念，最终只落在两个桶里，外加一个贯穿问题：

- **桶 A：要过模型的**（消耗判断力，可能漂移）——model 是核心，其他都是喂它的知识
- **桶 B：不过模型的**（确定性代码，不漂移，也不灵活）——harness 里的各种机制
- **贯穿问题：下一轮由谁发起？**——人、定时器、事件、还是 agent 自己。这是 loop engine 的位置

任何新概念，先问它进哪个桶、要不要回答那个贯穿问题。归不进的，多半是营销词。

## 1. 五个核心概念

统一格式：**本质 / 在 CC 里 / 边界（它不做什么）**。边界是防止混淆的关键。

### 1.1 Model（模型）
- 本质：输入文本 → 输出文本的推理机。没有记忆、没有手脚、没有意志。一切智能来自它，一切不可靠也来自它
- 在 CC 里：被 harness 调用的那个推理核心
- 边界：**不做任何事，它只说话**

### 1.2 Agent（智能体）
- 本质：model + 工具 + 循环。让模型能"做事 → 看结果 → 再决定下一步"的结构
- 在 CC 里：主会话是一个 agent，子代理也是 agent——区别只在工具面和上下文
- 定位：**判断的执行者**
- 边界：**不强制。它的所有"遵守"都是概率性的**

### 1.3 Skill（技能）
- 本质：注入 agent 上下文的知识包——SOP、模板、校准、判断标准。改变 agent **怎么想**，不改变它**能做什么**
- 在 CC 里：SKILL.md + references 按需加载
- 边界：**不执行、不强制、不计时。它只是文字**。写"如何判断"是本职，写"禁止"是弱约束——后者找错了层

### 1.4 Harness（运行时）
- 本质：agent 循环外面的一切确定性机制——工具实现、权限门、hooks、上下文压缩、调度器、子代理派生
- 在 CC 里：CC 的本体是 harness，不是"一个大 agent"。主 agent 只是它跑的进程之一
- 边界：**不判断**。只能规则匹配，遇到剧本外的情况只会放行或拦截，不会变通

### 1.5 Loop Engine（循环引擎）
- 本质：回答"下一轮什么时候、由谁发起"。四种形态：人肉推 / 定时推（scheduler、cron）/ 事件推（hook、CI）/ 自旋推（agent 给自己排下一轮）
- 在 CC 里：scheduler、后台任务、/loop；**人肉推就是当前 sdlc 流程里每个阶段手动推进的自己**
- 边界：**不判断**。只管"再来一轮"，不管"该不该再来"

## 2. 派生概念归位表

| 概念 | 一句话 | 归属 |
|---|---|---|
| Tool | agent 的手，一段确定性代码 | 桶 B，被 agent 调用 |
| MCP | 工具的接入协议（USB 口标准），让同一个工具被不同 agent 复用 | 桶 B 的连接层 |
| Hook | harness 开给你的拦截点——工具调用前后、会话开始、每条 prompt，跑你的代码。skill 是跟 agent 商量，hook 是不商量 | 桶 B |
| Subagent | harness 派生的新 agent 实例：干净上下文 + 受限工具面。买隔离，付信息不共享 | 桶 A 的执行形态 |
| Workflow | 确定性编排脚本，agent 调用是脚本里的一行。形状固定的多 agent 协作从"靠模型按剧本走"变成"代码保证" | 桶 B，过程层 |
| Context / Memory | context = 单次会话的工作记忆；memory = 跨会话的笔记本 | 载体，桶 A 的燃料 |

## 3. 落地决策流程（治"无从下手"）

遇到任何一个需求，按顺序问：

```
1. 需要判断力吗？
   否（规则明确、可机械验证）→ hook / 脚本 / CI，到此为止
   是 ↓
2. 知识问题还是执行问题？
   知识（怎么判断、什么标准）→ skill，到此为止
   执行（谁来做）↓
3. 需要干净上下文或并行吗？
   要   → subagent
   不要 → 主 agent
4. 重复发生且每次形状一样？
   是，单步可验证        → runner/脚本（spec 资产化）
   是，多 agent 固定协作 → workflow
   周期性需要盯          → scheduler/loop
```

注意：不是"把 skill 整体转成 hook"，是逐条问"需要判断力吗"——**判断的留下，服从的下沉**。skill 因此变薄，不是消失。

三条默认规则：

1. **拿不准先放 skill**——改动成本最低、可迭代、随时能迁
2. **同一个坑踩第二次就下沉**——漂移是"该下沉到确定性层"的信号，不是"在 skill 里再写一条禁止行"的信号。反合理化表越加越长 = 在错误的层反复加固
3. **写规则的那一刻就决定它住哪层**——事前路由是零成本习惯，事后盘点是一次性工程

（下沉到确定性层后，CLI 守卫 / hook / CI 怎么选 → 见 §4）

## 4. 强制层详解：三档、路由与机制

> 2026-09-15 追加：hooks/CI 深入讨论后的沉淀。依据 = Claude Code 本地 settings schema（update-config skill 自带参考），个别标注处基于训练记忆。

### 4.1 三档可靠性梯度

"下沉到确定性层"不是二选一，是梯度：

| 档位 | 机制 | 谁保证时机 | 已有例子 |
|---|---|---|---|
| 文字约束 | skill 里的禁止行 | 模型自觉，概率性 | 反合理化表 |
| **入口守卫** | CLI 工具内的校验 | 调用命令时必然触发，进了就强制 | 任务 CLI `start` 拒空上下文文件、OVAL 注解（校验声明成注解，框架执行） |
| **全程强制** | hook / CI | 完全不经模型，harness/流水线决定时机 | UserPromptSubmit、SessionStart hook |

实操排序：**能进 CLI 守卫的先进 CLI**（改造成本最低，不动 cc 配置），拦不住时机的再上 hook（写文件瞬间拦）或 CI（提交时兜底）。

### 4.2 载体路由：时机定载体，范围用过滤器

分界不是"全局 vs 业务场景"，是"**规则依附于什么**"：

- **依附于流程步骤**（start 时、资产化时、提测时）→ **CLI 守卫**。检查时机就是"流程走到这一步"，只有流程命令入口能提供这个时机和上下文
- **依附于生命周期点位**（写文件、提交、会话开始）→ **hook / CI**。从产物形态就能判，不需要知道流程状态

反例："某业务域 Controller 也要五大注解"是业务场景规则，但该归 hook——能从代码形态判断，用 hook 的路径过滤圈定场景即可。真正归 CLI 的是**需要感知流程状态**的规则（如"exec 前必须过关卡1"——hook 不知道什么是关卡）。

hook 与 CI 不互斥，分工：

| | 反馈时机 | 对谁生效 | 依赖 |
|---|---|---|---|
| CLI 守卫 | 流程命令调用时 | 调命令的人 | 模型/人会去调命令 |
| hook | 写码瞬间打回 | 本机配了的会话 | 无（自动触发） |
| CI | 提交时兜底 | 全员、不可否认 | 无 |

同一检查脚本常两处挂：hook 即时拦（省 agent 后续空转轮次）+ CI 兜底（防本地没配、防人肉绕过）。

两问路由法：

```
这条规则的触发时机，天然落在哪？
├─ 流程步骤（start/资产化/提测）→ CLI 守卫，挂在流程命令入口
└─ 生命周期点位（写文件/提交/会话开始）
   ├─ 写码瞬间就要拦 → hook
   └─ 可以等到提交、要约束全员 → CI
   （被坑过就两层都挂，同脚本复用）
```

真实规则过一遍：

| 规则 | 时机落在 | 载体 |
|---|---|---|
| 任务 start 拒空上下文文件 | 流程步骤 | CLI（已做 ✓） |
| 五大注解 / ResultJson / 禁手算 offset | 写文件瞬间 | PostToolUse hook + CI 兜底 |
| 用例文件头关卡状态合法 / spec 必须带元数据 | 流程步骤（cases/exec 入口） | CLI 守卫 |
| 分层依赖违规（controller 依赖 mapper） | 编译/提交时 | CI（或测试期 ArchUnit） |
| 上线 Apollo key 清单 | 发版前 | CI（sdlc-config-review 脚本现成） |

### 4.3 hook 机制速查

**不是"任何环节都能触发"**：只能挂生命周期事件（30+ 个，按用途分组）：

| 组 | 事件 | 触发时机 |
|---|---|---|
| 工具级（最常用） | PreToolUse / PostToolUse / PostToolUseFailure | 每次工具调用前 / 成功后 / 失败后 |
| 输入级 | UserPromptSubmit | 每发一条消息（任务框架的 workflow-state 注入即此） |
| 会话级 | SessionStart / SessionEnd / PreCompact / PostCompact | 会话开始结束、压缩前后 |
| 停止级 | Stop / SubagentStop | 主 agent / 子代理结束响应时（可做"没跑测试不许停"） |
| 任务级 | TaskCreated / TaskCompleted | 后台任务创建/完成 |
| 权限级 | PermissionRequest / PermissionDenied | 权限弹窗前 / 被拒后 |

**不是"纯规则"**：hook 有五种类型——`command`（跑脚本，最常用）、`prompt`（小模型判断条件）、`agent`（起 agent 验证）、`http`（POST 远端）、`mcp_tool`（调 MCP 工具）。判断也能塞进 hook，只是默认用 command。

**同步串联（核心机制）**：默认 hook 同步阻塞，agent 循环等它跑完：

```
模型发起工具调用
  → PreToolUse hook 执行
    → 拦截（exit 2 或 permissionDecision: "deny"）→ 工具不执行，
      reason 回给模型 → 模型看到原因，下一步自我修正
    → 放行 → 工具执行 → PostToolUse hook 执行
      → 校验失败（decision: "block" + reason）→ reason 回给模型修复
      → 通过 → 循环继续
```

subagent 的工具调用同样走 harness 工具执行层，工具级 hook 一样生效（训练记忆，`claude --debug` 可实测）。每个 hook 可配 `timeout`（默认 60s）、`async`（后台不阻塞）、`asyncRewake`（后台跑、出错才唤醒模型）。

**限制**：
1. 只能挂点位，不能挂"模型思考到一半"
2. 默认同步：慢 hook 拖慢每次工具调用，脚本必须快、尽早跳过不相关调用
3. hook 看不到对话上下文，只拿 stdin 的事件 payload（tool_name、tool_input 等 JSON）
4. 以你的 shell 权限运行任意代码——项目里新 hook 首次加载会要求确认
5. 误报代价高：拦错的 hook 反复打断工作流，拿不准的宁放行 + CI 兜底
6. settings.json 语法坏了会静默禁用该文件全部配置

**作用域两级控制**：

第一级——配在哪个文件 = 对谁生效：

| 文件 | 范围 | 入库 |
|---|---|---|
| ~/.claude/settings.json | 全局所有项目 | 否 |
| .claude/settings.json | 本项目团队共享 | 是 |
| .claude/settings.local.json | 本项目仅本机 | 否 |

第二级——触发条件三层过滤（以五大注解为例）：

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{ "type": "command",
        "command": "python3 .claude/scripts/check_controller.py" }]
    }]
  }
}
```

```python
# .claude/scripts/check_controller.py（骨架）
import sys, json, re
payload = json.load(sys.stdin)
path = payload["tool_input"]["file_path"]
# ②路径过滤：不是 controller 的 java 文件，秒退
if not re.search(r"controller/.*Controller\.java$", path):
    sys.exit(0)
content = open(path).read()
missing = [a for a in ["@PostMapping", "@RequestBody", "@LogRecord",
                       "@LoginRequired", "@Validate"] if a not in content]
# ③实质校验：失败 block + 原因回给模型
if missing:
    print(json.dumps({"decision": "block",
        "reason": f"缺少必填注解: {', '.join(missing)}"}))
```

- ① `matcher`：按工具名正则（Write|Edit）；另有 `if` 字段用权限规则语法粗过滤（如 `"Bash(git *)"`），不匹配连进程都不起
- ② 脚本读 file_path 自己判断，不相关就秒退
- ③ 真正的规则校验

> 注解名随示例框架而异——通用做法是把"框架强制注解存在性"写成规则集（本仓库的落地形态见 [sdlc-guardrails](../../skills/sdlc-guardrails/README.md)：引擎 `engine/check.py` + 项目侧 `guardrails.yaml`）。

### 4.4 CI 速查

CI = Continuous Integration（持续集成），比 LLM 早二十年：push 代码时远端机器自动跑检查，失败挡合并。与 AI 无关，是兜底层。

落地产物（都在仓库里）：

| 产物 | 形态 |
|---|---|
| 流水线配置 | GitHub Actions `.github/workflows/*.yml` / GitLab CI `.gitlab-ci.yml` / Jenkinsfile |
| 检查脚本 | 和 hook 里跑的是**同一份**脚本 |

与 hook 的分工：hook 写码瞬间拦（快反馈、本机），CI 提交时拦（兜底、全员、不依赖本地配置）。穷人版替代：git `pre-commit`（本地提交前跑，不需远端）。

## 5. 已验证案例（用自己体系走过流程）

| 案例 | 走到第几步 | 落点 |
|---|---|---|
| 任务 CLI start 拒绝空上下文文件 | 第 1 步（可机械验证） | 脚本强制。之前是 skill 纪律时反复出问题，下沉后消失 |
| spec runner 回归轮 | 第 4 步（重复、单步可验证） | 脚本。零 token 1.8 分钟跑 13 条 |
| sdlc-gate 四子代理 | 第 3 步（要干净上下文防污染） | subagent |
| 人工关卡/确认点 | 第 5 概念（人肉 loop） | 判断密集环节，人推是对的；回归段已换成脚本推 |
| 五大注解 hook + CI | §4.2 两问路由 → 写文件瞬间 | 已落地：harness 引擎 + 项目 guardrails 规则集 |

## 6. 新概念解码器

再冒出新词，问三个问题：

1. 模型内的（知识）还是模型外的（机制）？
2. 它判断还是只执行？
3. 它发起轮次吗？

示例："agentic workflow" = 过程层包装；"RAG" = 知识注入的一种；"MCP server" = 工具；"autonomous agent" = loop 自旋 + agent；"copilot vs agent" = 人推还是自推。
概念再多，槽位就这几个——新词是换皮，不是新知识。

## 附录 A：CC 的结构（不是"一个大 agent"）

```
CC (harness)
 ├─ 主 agent ← 你对话的这个，全工具面
 ├─ 子 agents ← Agent tool 派生，各自独立循环、受限工具
 ├─ hooks / 权限 / 调度器 ← 确定性代码路径，无模型参与
 └─ skills / MCP / memory ← 注入到 agent 上下文的资产
```

类比：agent 是司机，harness 是车。刹车、门锁、仪表盘都是车提供的——司机决定去哪，但决定不了"没系安全带能不能开"。

会话里的证据：UserPromptSubmit hook 每轮确定性注入 workflow-state（不经过模型决定）；权限弹窗在工具执行前拦截；子代理的工具面裁剪是 harness 做的。

## 附录 B：对当前体系的三个调整方向（本框架的推导输出，2026-09-16 标注落地状态）

1. **红线盘点下沉**：✅ **已落地（2026-09-15/16）**——引擎 [sdlc-guardrails/engine/check.py](../../skills/sdlc-guardrails/engine/check.py)（规则由项目侧 `.claude/guardrails.yaml` 定义）+ PostToolUse hook 拦写入（含 Edit 增量语义）+ pre-commit 拦提交（[sdlc-guardrails/templates/pre-commit](../../skills/sdlc-guardrails/templates/pre-commit)）+ `audit_profiles.py` 管跨文件对账 + `guard_exec.py` 管 sdlc-test 关卡；首轮存量基线扫描（约 1200 文件）命中 109 处 + 6 个悬空分组，口径存量不追溯
2. **固定编排上浮**：⏸ **未做，待议**——sdlc-gate 4 角色扇出 + RECONCILE 预理的 workflow 化未实施；exec 批量轮维持 skill 指示派发。触发条件：再次出现编排漂移事故时重议
3. **可验证重复劳动继续 spec 化**：◐ **部分落地**——一键回归命令已建（模板 [sdlc-test/templates/run_regression.sh](../../skills/sdlc-test/templates/run_regression.sh)，人工触发，spike 健康检查→runner→`-manual` 报告，不占轮次号）；定时触发经评估否决（迭代生命周期短）；specs 资产重建随 exec 轮滚动进行

skill 知识资产（校准、模板、判断规则）不动——换任何载体都有效，且它们本就该住知识层。

附带收益（已兑现）：红线下沉后两份 checklist 头注标明机器拦截范围，自检范围收窄到判断类条目，context 稀释减轻。

反面提醒：
- 确定性不是免费的：脚本对异常状态脆，"阻塞前穷尽解锁三路径"这类即兴是模型的长处；判断密集环节（需求 digest、裁决）人 + 模型仍是对的
- 人工关卡数据（45 落改 / 1 驳回）证明关卡在抓真东西，不为自动化而自动化

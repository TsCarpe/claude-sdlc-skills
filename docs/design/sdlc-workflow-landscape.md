# SDLC 工作流全貌

> **这份文档是什么**：方法论源项目（某 Java DDD 业务系统）开发工作流在 2026-09-16 的完整地图快照——有哪些资产、各在哪一层、一条需求怎么走完全程、人机怎么分工。可移植层即本仓库；项目层部分是"你需要在目标项目自建什么"的范例（完整规范参考实现见 [dev-standards-reference/](../dev-standards-reference/README.md)）。
> **和另一份的关系**：[agent-stack-mental-model.md](agent-stack-mental-model.md) 回答"为什么这样设计"（概念分层 + 载体路由），本文档回答"现在有什么、怎么运转"（是什么）。
> 2026-09-16 随资产回收整理（删去源项目内部遗留事项清单）。

## 目录

1. [资产地图](#一资产地图四层--两域)
2. [需求生命周期](#二需求生命周期一条主线看资产怎么接力)
3. [人机分工](#三人机分工)
4. [体系热力图](#四体系热力图诚实版)

---

## 一、资产地图：四层 × 两域

设计原则一句话：**可移植的住本仓库（skills），项目细节住项目里**——换项目只写项目侧文件。

```
┌─────────────────────────────────────────────────────────────────┐
│ 可移植层（claude-sdlc-skills 仓，即本仓库）                         │
│                                                                   │
│ 📚 知识层（怎么判断）                                               │
│    sdlc-intent    需求梳理 + 六层体检（digest / audit / Q表）        │
│    sdlc-gate      评审关口（4 角色扇出 + RECONCILE + 人工裁决）      │
│    sdlc-test      测试四阶段（cases / static / exec / report）      │
│    sdlc-doubt     决策对抗复查                                      │
│    sdlc-config-review  发版配置审计                                 │
│    （另有 sdlc-doc / sdlc-yapi：飞书技术设计文档与接口文档同步，      │
│      依赖个人全局环境，暂不在本仓库——见 Roadmap）                    │
│                                                                   │
│ 🔒 强制层（什么必须/禁止，不经模型）                                 │
│    sdlc-guardrails/engine/check.py 规则引擎（项目侧配置规则）       │
│    sdlc-guardrails/engine/audit_profiles.py OVAL 分组跨文件对账    │
│    sdlc-guardrails/engine/check_runner_form.py 文档命令形态自检    │
│    sdlc-test/scripts/guard_exec.py   关卡守卫                       │
│    sdlc-gate/scripts/check_trace.py  产物链追溯校验                 │
│    sdlc-guardrails/templates/ hook 段 / pre-commit / 回归         │
├─────────────────────────────────────────────────────────────────┤
│ 项目层（目标项目里自建，源项目为范例）                                │
│                                                                   │
│ 📚 知识层    CLAUDE.md（架构规范入口）                               │
│             → dev_standards/（详细规范细则，按需加载）                │
│             → 铁律速查层（指针型，一页纸）                            │
│                                                                   │
│ 🔒 强制层    .claude/guardrails.yaml     项目规则集（查什么）        │
│             .claude/settings.json hooks  注入型×3 + 拦截型×1        │
│             .githooks/pre-commit         提交兜底                   │
│                                                                   │
│ 📋 状态层    任务框架（CLI 入口带守卫）                               │
│             sdlc/<需求名>/  产物目录（req / test / review）          │
├─────────────────────────────────────────────────────────────────┤
│ 🔧 全局工具层：codegraph / mysql / yapi MCP / chrome-devtools /     │
│               serena / context7 / lark-cli                          │
└─────────────────────────────────────────────────────────────────┘
```

**强制层三档速查**（详见 [agent-stack-mental-model.md](agent-stack-mental-model.md) §4）：

| 档位 | 时机 | 实例 |
|---|---|---|
| 入口守卫（CLI） | 流程命令调用时 | 任务 CLI 各守卫、guard_exec.py |
| 写入拦截（hook） | 写文件瞬间 | PostToolUse → check.py |
| 提交兜底（pre-commit） | git commit 时 | .githooks/pre-commit |

---

## 二、需求生命周期：一条主线看资产怎么接力

### 轻量任务（≤2 层且 ≤3 文件）

```
需求
 → 主会话 inline + 开发前规范注入（任务 start 校验上下文文件非空）
 → 编码 ·············· 🔒 guardrails hook 写入即拦（含子代理）
 → 自检子代理 ········ 只查判断类（语义 / 组织 / 命名——存在性已被 hook 拦截）
 → git commit ········ 🔒 pre-commit 兜底（不经 cc 的提交也拦）
```

### 大需求（三段式 + 测试全链）

```
① 需求全貌
   sdlc-intent：digest + audit + Q表（飞书评论区必读，最新评论优先）
   → ⏸ 确认点①：四件核对 + 体检问题去向表

② 技术骨架 ∥ 测试用例（并行独立产出）
   技术骨架：接口契约读写分级 / 公共资产清单六类 / D 表八类别
   sdlc-test cases：红线禁读设计（保交叉独立性）
   → sdlc-gate：4 个 fresh-context 子代理扇出
      → RECONCILE 四分类 → 人工逐条裁决 → 放行
   → ⏸ 确认点②③

③ 实施与验证
   child 任务：implement / check 子代理（curate 过的上下文注入）
   → 编码 ·············· 🔒 hook 拦
   → 自检 ·············· 判断类复查
   → sdlc-test static ·· 代码 ↔ 用例一致性（三态结论）
   → exec ·············· 🔒 guard_exec 守卫（关卡1 / 互认 / 资产一致性）
        派发子代理执行 + 回归轮两步（spec 先跑 runner）
   → spec 资产化 ······· 已通过用例 → Playwright spec（零 token 回归）
   → 报告 + ⏸ 关卡2 复验
   → 上线前 sdlc-config-review（Apollo key 清单）

   之后随手回归：runner 一键回归脚本（人工触发，不占轮次号；
   模板见 sdlc-guardrails/templates/run_regression.sh）
```

---

## 三、人机分工

| 谁 | 管什么 | 一句话 |
|---|---|---|
| **你** | Q 表拍板、issue 裁决、关口放行、关卡确认、口径冲突定夺、方案选择 | 判断的事走 prompt（skill） |
| **主 agent** | 梳理、设计、编码、测试编排、报告 | 生成与判断的执行 |
| **子 agent** | implement / check / research、评审扇出、exec 切批 | 干净上下文的隔离执行 |
| **机器（harness）** | 红线拦截（写入 / 提交）、关卡守卫、跨文件对账、回归执行 | 服从的事走代码，零判断 |

---

## 四、体系热力图（诚实版）

| 维度 | 状态 | 说明 |
|---|---|---|
| 知识层 | ★★★ | 六 skill + 三级规范，多轮 best-practices 复核 |
| 执行层 | ★★★ | 子代理扇出、派发协议、spec runner 零 token |
| 强制层 | ★★☆ | 2026-09-15/16 从零拦截建成三档齐备——**未经真实任务检验** |
| 编排层 | ★★ | 扇出仍靠 skill 指示（workflow 化未做，触发条件：再出编排漂移事故） |

**下一个真实接口任务 = 整体验验**：观察 hook 触发是否自然、自检轮次是否下降、关卡守卫是否顺畅。跑完才算"验证过"，不只是"建成"。

---

*维护约定：体系结构性变化时更新本文档（新增/迁移资产、层职责变化）；头部更新记录同步。*

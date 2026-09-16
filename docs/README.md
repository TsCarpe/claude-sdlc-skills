# docs 导读

> 本目录文档分四种性质：**叙述**（流程怎么走）、**理论**（为什么这样设计）、**决策记录**（某个机制当时怎么定的）、**参考实现**（照抄结构不照抄规则）。先看地图，再按路径读。

## 文档地图

| 文档 | 性质 | 一句话定位 | 什么时候读 |
|---|---|---|---|
| [workflow.md](workflow.md) | 叙述 | 方法论主叙述：一个需求怎么走完一生，人机怎么分工 | 想了解全貌的第一篇 |
| [example-walkthrough.md](example-walkthrough.md) | 叙述 | 6 步走查，每步附真实产物片段 | 看一眼产物长什么样，比读十段描述更快 |
| [large-req-playbook.md](large-req-playbook.md) | 叙述 | 大需求三段式拆分方法论（框架无关） | 功能点 ≥5 / 跨域 / 涉表的大需求来了 |
| [ai-native-sdlc-guide.md](ai-native-sdlc-guide.md) | 理论 | Google/Anthropic/OpenAI 三篇 AI 原生 SDLC 文章的融合提炼 | 想知道这套流程的理论依据与业界共识 |
| [design/agent-stack-mental-model.md](design/agent-stack-mental-model.md) | 理论 | Agent Stack 心智模型：两个桶 + 载体路由（什么该进 skill、什么该下沉 harness） | 遇到 AI 开发栈新概念要归层，或调整自己的工作流时 |
| [design/sdlc-workflow-landscape.md](design/sdlc-workflow-landscape.md) | 理论 | 工作流资产全貌快照：可移植层（本仓库）vs 项目层各有什么 | 想知道「装完 skill 后项目侧还要自建什么」 |
| [sdlc-test-design.md](sdlc-test-design.md) | 决策记录 | sdlc-test 设计决策 D1-D21（四阶段编排 + 回归档） | 要改 sdlc-test 的行为前，先看当时为什么这样定 |
| [sdlc-test-spec-evolution.md](sdlc-test-spec-evolution.md) | 决策记录 | 「点击员→脚本作者」演进：流派研究 + 改进计划（已实施） | 想理解 spec 资产化与 runner 回归的来龙去脉 |
| [design/sdlc-id-linkage-plan.md](design/sdlc-id-linkage-plan.md) | 决策记录 | 跨产物 ID 体系（命名空间.编号）与交界衔接机制（已实施） | 产物互引断链 / 要新增产物类型时 |
| [dev-standards-reference/](dev-standards-reference/README.md) | 参考实现 | 项目级分层规范体系全套示例（入口/细则/checklist/guardrails） | 要给自己的项目搭「CTX 底座」时照抄结构 |
| [faq.md](faq.md) | 参考 | 安装触发、降级矩阵、术语表 | 装了没反应 / 报依赖缺失时 |

## 三条阅读路径

### 路径一：上手用（30 分钟）

装完 skill 想尽快跑起来——

1. 仓库 [README](../README.md)「装完先试这个」→ 用 sdlc-intent 梳理一个真实需求
2. [example-walkthrough.md](example-walkthrough.md) → 看每个关口的产物长什么样
3. [faq.md](faq.md) → 遇到问题回来查

### 路径二：理解方法论（2 小时）

想知道这套东西为什么这样设计——

1. [workflow.md](workflow.md) → 全流程叙述（主入口）
2. [ai-native-sdlc-guide.md](ai-native-sdlc-guide.md) → 业界理论框架，对照 §7 的实践映射
3. [design/agent-stack-mental-model.md](design/agent-stack-mental-model.md) → 「判断的进 skill，服从的下沉 harness」
4. [design/sdlc-workflow-landscape.md](design/sdlc-workflow-landscape.md) → 资产分层全貌

### 路径三：深入设计与改造（按需）

想改某个机制、或把自己的项目接进来——

1. 测试侧：[sdlc-test-design.md](sdlc-test-design.md)（D1-D21 决策）→ [sdlc-test-spec-evolution.md](sdlc-test-spec-evolution.md)（回归档演进）
2. 产物互引：[design/sdlc-id-linkage-plan.md](design/sdlc-id-linkage-plan.md)（ID 体系）
3. 项目侧接入：[dev-standards-reference/README.md](dev-standards-reference/README.md)（规范底座）→ [harness/README.md](../harness/README.md)（红线引擎三步接入）

## 按问题找文档

| 你的问题 | 去处 |
|---|---|
| 大需求怎么拆？ | [large-req-playbook.md](large-req-playbook.md) + [templates/](../templates/) |
| 为什么用例生成禁止读设计？ | [workflow.md](workflow.md) §3 + [sdlc-test-design.md](sdlc-test-design.md) D11 |
| 回归测试怎么不烧 token？ | [sdlc-test-spec-evolution.md](sdlc-test-spec-evolution.md) + sdlc-test spec 子命令 |
| 规则写 skill 还是写 hook？ | [design/agent-stack-mental-model.md](design/agent-stack-mental-model.md) §3 决策流程 |
| 怎么给自己的项目配红线拦截？ | [harness/README.md](../harness/README.md) + [dev-standards-reference/guardrails.example.yaml](dev-standards-reference/guardrails.example.yaml) |
| 产物间怎么互相引用？ | [design/sdlc-id-linkage-plan.md](design/sdlc-id-linkage-plan.md) §2 命名空间注册表 |

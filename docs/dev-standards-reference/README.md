# dev-standards-reference — 分层上下文工程参考实现

> 一套在真实 Java DDD 项目中运行了多个迭代的**项目级规范体系**完整示例（2026-09 脱敏整理收录）。它是 [workflow.md](../workflow.md)「CTX 底座（载体随项目自建）」那一层的实物：CLAUDE.md 只留入口与硬约束，细则按需加载，可 grep 的红线下沉到 guardrails 引擎。
> **照抄结构，不照抄规则**——注解（`@LogRecord`/`@LoginRequired`/`@Validate`）、工具类（`ResultJson`/`PageUtil`）均为示例框架的公开 API，替换成你自己项目的对应物；分层思想与组织方式才是可移植的部分。

## 三层结构

```
项目根/
  CLAUDE.md                    ← ① 入口层：每次会话全量加载。WHAT/WHY/HOW + 硬约束 + 按需加载表（≤1页）
  dev_standards/               ← ② 细则层：任务触发才读取，不进默认上下文
    development_checklist.md      编码后自检清单（30+ 条高杠杆规则）
    development_standards/*.md    7 份细则（命名/接口/OVAL/转换/分页/方法组织/AI 卫生）
    feishu-tech-review-guide.md   独立场景：技术设计文档生成规范
  .claude/guardrails.yaml      ← ③ 强制层：可机械校验的红线，写文件瞬间由 hook 拦截（不经模型）
```

| 层 | 载体 | 加载时机 | 谁保证执行 |
|---|---|---|---|
| ① 入口层 | `claude-entry.md`（示例的 CLAUDE.md） | 每轮会话全量 | token 换来的注意力，只放最高杠杆内容 |
| ② 细则层 | `details/*.md` + `development-checklist.md` | 触发对应任务时按表加载 | CLAUDE.md §4 的触发场景表路由 |
| ③ 强制层 | `guardrails.example.yaml` | Write/Edit 写文件的瞬间 | [harness 引擎](../../harness/README.md) hook 拦截，确定性 |

## 目录对照

| 本目录 | 在示例项目中的位置 | 说明 |
|---|---|---|
| `claude-entry.md` | `CLAUDE.md` | 入口层示例（含「按需加载表」和「正例锚点」两个关键设计） |
| `development-checklist.md` | `dev_standards/development_checklist.md` | 自检清单；头部标注了哪些条目已由 guardrails 机器拦截（自检只做判断类） |
| `guardrails.example.yaml` | `.claude/guardrails.yaml` | 22 条规则示例；由 checklist 中可 grep 的条目机械化而来 |
| `details/api-interface-design.md` | `development_standards/api_interface_design.md` | Controller 模板与必填注解 |
| `details/coding-norms.md` | `development_standards/coding_norms.md` | 类/方法/字段命名 |
| `details/ai-code-hygiene.md` | `development_standards/ai_code_hygiene.md` | AI 生成代码卫生（散参/Map 出参/全路径内联） |
| `details/oval-validation.md` | `development_standards/oval_validation_details.md` | OVAL 声明式校验（两棵决策树） |
| `details/object-conversion.md` | `development_standards/object_conversion_details.md` | 对象转换四类与层归属（决策树 + 反例对照） |
| `details/paginated-query.md` | `development_standards/paginated_query_details.md` | 分页三件套与响应结构 |
| `details/method-organization.md` | `development_standards/method_organization_details.md` | 方法组织（4 棵决策树 + 结构信号违规清单） |
| `details/feishu-tech-review-guide.md` | `dev_standards/feishu-tech-review-guide.md` | 技术设计文档自动生成规范（配套全局 skill `sdlc-doc`/`sdlc-yapi`，暂不在本仓库——见根 README Roadmap） |

## 两个关键设计

**1. 按需加载表（Progressive Disclosure）**：入口层不放规则全文，只放「触发场景 → 必读文档」的路由表。编码前按表读对应细则，规范细节永不进入每轮上下文——这是 token 成本与规则覆盖面的平衡点。见 `claude-entry.md` §4。

**2. 正例锚点（Pointer over Copy）**：规范不复制代码模板，只指向真实代码文件与行号（`XxxController.java:44` 式）。真实代码永不与规范脱节，且 AI 可直接跳转阅读。见 `claude-entry.md` §5 与各细则的「锚点」节。

## 红线如何下沉到引擎

checklist 里「写了就是错」的条目（存在性检查类：注解五件套、禁 `BeanUtils.copyProperties`、禁手算 offset……）已机械化进 `guardrails.example.yaml`，由 [harness/engine/check.py](../../harness/engine/check.py) 在写文件瞬间拦截；checklist 头部相应标注「机器已拦，自检不必重复核对」。**知识层（怎么写对）与强制层（写了就拦）的分工原则**见 [agent-stack-mental-model.md](../design/agent-stack-mental-model.md) §4。

新项目接入（三步）：复制 hook 挂载段 → 按本示例写自己的 guardrails.yaml → pipe-test。详见 [harness/README.md](../../harness/README.md)。

## 脱敏说明

- 项目/模块名：源项目已化名为 HRSystem / `hr-*` 模块；包名统一 `com.example.hr`
- 业务示例：真实业务域（比赛/培训/资源等）统一替换为中性虚构（商品 goods / 订单 order / 评选活动 activity）
- 正例锚点的文件路径与行号结构保留（演示「锚点」形态），指向的是脱敏后的虚构路径

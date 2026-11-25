# 任务框架交接契约（Trellis 为示例，框架无关）

> **定位**：design.md 产出后如何交给任务框架拆分执行。**分工**：设计决策与拆分规则随 design.md 交付（本文档管「设计交付接入」）；任务编排（建任务/排期/状态管理/归档）归任务框架；开发合法性关卡由 guard_dev 机械守卫承担（见「关卡接入」节）。
> **框架无关声明**：Trellis（开源任务框架，`.trellis/` 目录 + brainstorm→implement→check 流程）为示例载体；机制适配任意任务框架或纯目录约定。

## 目录（本文导航）

> 本目录是本文自身的导航（本文 >100 行，供部分读取时预览范围）。

- [落位规则](#落位规则)
- [prd.md 结构建议](#prdmd-结构建议)
- [确认点映射](#确认点映射)
- [上下文清单登记](#上下文清单登记)
- [spec 切分规范模板](#spec-切分规范模板)
- [关卡接入](#关卡接入)

## 落位规则

落位按**链路**判，不按风险分级——A 级轻量链路同样落 `sdlc/`：

| 场景 | design.md 位置 |
|---|---|
| 三段式链路（parent prd 已在任务目录，第一段产物） | parent 任务目录，与 prd.md 同目录（Trellis：`.trellis/tasks/<task>/design.md`） |
| 其余（sdlc-intent → sdlc-design 轻量链路，A/B/C 级皆然） | `sdlc/<需求名>/design/design.md`（C 级 `plan.md`） |

轻量链路 design 之后转任务框架执行时**不迁**：parent prd 技术方案区与上下文清单登记 `sdlc/` 下的原路径——sdlc-sync pull-dev-bundle 按该路径对账，迁走即出现两份。与 sdlc-gate 前置输入同口径（三段式按任务系统约定位置、其余按 `sdlc/<需求名>/design/` 定位设计文档）。

需求已接平台（判据：卡级 `sdlc/<需求名>/.platform` 存在，以 sdlc-sync bind / submit 写入的为准；或用户说明该需求已在平台建卡 / 发布——sdlc-platform「交给开发」把 `.platform` 写在用户主目录，项目内看不到，以用户说明为准）时**一律落 `sdlc/<需求名>/design/design.md`**，三段式链路也一样：平台定稿由 sdlc-sync pull-dev-bundle 只写到该路径并在其上加定稿锚点；parent prd 在输入源锚点条登记该路径为指针。判据误判的方向只是多落 `sdlc/`，无副作用。design 已落在 parent 任务目录、之后才接平台的：首次拉取后以带锚点的那份为需求与契约口径；parent 目录副本不删，改名 `design.local.md` 留档，其中平台定稿没有的内容（§7 切分约束、横切矩阵、H 接受条件）由人决定走平台修订并入，或在切片期作为补充约束登记进上下文清单；不得两份并存各改。

## prd.md 结构建议

design.md 直接作为任务输入后，任务框架的需求澄清环节（Trellis 的 brainstorm）**退化为 scope 确认**——不再逐问推导需求，只确认边界。prd.md 两区结构：

```markdown
# <需求名>

## 需求语义区（从 digest 三件套提炼，非重新脑暴）
- Goal：一句话
- In scope：功能.Fxx 清单（对应 digest 功能点地图）
- Out of scope：显式排除项 + 去向
- Acceptance criteria：业务级验收（对应 digest 规则表 + parent prd 验收标准）

## 技术方案区（指针，实现前必读）
- 技术设计：<design.md 路径>（三段式未接平台 = 同任务目录；其余 = `sdlc/<需求名>/design/design.md`，均不迁）——接口契约 / D 表决策 / 公共资产清单 / §7 实施切分约束
- 未决口径：以 design 头部 Q 表为准（不在本文档重复）
- 上游共识：`sdlc/<需求名>/intake/digest-<日期>.md`
```

> 红线：技术结论**不复制进 prd**（防内联副本漂移）——通用结论由上下文清单登记注入（见下节），prd 只保留需求语义与指针。

## 确认点映射

```text
sdlc-design 产 design.md
→ 人逐行核对 = 确认点②定稿（ack 是定稿信号，不构成质量放行）
→ sdlc-gate 评审 + 裁决 → 放行（issues 头「评审状态=已放行」）
→ gate 放行后，轻量链路在此建 parent 任务 + scope 确认（人工）；三段式链路的 parent 任务自第一段已存在
→ 拆 subtask（≈三段式的 child 切片，须遵守 design §7 切分约束）
→ 🔒 subtask prd 评审 = 确认点③，过四条件才 implement
→ 开发启动合法性由 guard_dev 开发入口校验（关卡接入节）
```

**确认点③核对清单（四条件，subtask prd 评审用）**：

1. **契约符合度**：与 design 接口契约的符合度——无现场设计痕迹；若有 → 停，回 design 补契约（subtask 一半内容是现场设计 = 上层缺项）
2. **内联/注入完整性**：通用结论（契约/公共资产/D 表/ER）已由上下文清单注入、特有结论（本切片特有的校验组合/边界/口径）已内联——两者都缺 = 执行 agent 会瞎补
3. **技术级 AC 可测性**：验收标准可测
4. **gate 已放行**：subtask prd 的 ack 是流程性确认，不构成质量放行——开发启动由 guard_dev 开发入口校验（见下节）

## 上下文清单登记

任务框架支持上下文清单注入时（Trellis：`implement.jsonl` / `check.jsonl`），按下表登记（登记而非建议——漏登记即执行 agent 看不到）：

| 清单 | 登记条目 |
|---|---|
| implement.jsonl（实现上下文） | design.md（按落位规则的原路径，全文）+ 项目规范（`.trellis/spec/` 相关条目）+ 上游 digest |
| check.jsonl（检查上下文） | design.md §7（实施切分约束 + 横切核验矩阵）+ 项目规范相关条目 |

**谁在何时登记**：拆 subtask 的那个会话，在第一个 subtask 启动前——轻量链路 = gate 放行后建 parent 任务时；三段式链路 = parent 任务已存在，gate 放行后、拆第一个 subtask 时。sdlc-design 不代写清单文件（任务编排归任务框架），只在 design §7.2 等处标明哪些内容须登记。登记的是 design 落位原路径，可以在任务目录之外；任务框架的清单读不到任务目录外路径时（第一个 subtask 的注入为空即为信号）→ 改为在每个 subtask prd 的「上游注入清单」节列这些文件的绝对路径、执行前先读，并在回报里注明。

## spec 切分规范模板

项目级常驻规范（一次落盘，全部任务自动注入；Trellis 落 `.trellis/spec/` 下，如 `slicing.md`）。**本 skill 只提示落盘，不代写项目文件**；项目已用任务框架而切分规范未落盘时，拆分纪律以 design §7 头部降级声明为准，**回复中给出下述模板全文**供用户粘贴；项目没有任务框架时不贴，只说明接入任务框架时再落：

```markdown
# 任务切分规范

1. **骨架切片先行**：design §3 公共资产清单非空时，第一个 subtask 必须是骨架切片
   （交付枚举/常量/DDL/包目录/公共子结构），完成前业务切片不得启动；后续切片只消费
   公共资产、不得新建同功能项（确需新增须回写 design 公共资产清单）。
2. **横切功能点不单独建 subtask**：无独立触发角色、落点分散多接口的功能（如状态流转：save 注册 /
   edit 重注册 / 终止移除 / 处理器幂等守卫）随宿主切片交付；全部落点集中在单一调度类、无接口侧注册/移除联动的不在此列，
   可独立成 subtask。宿主切片完成后按 design §7.2 核验矩阵逐行补记核验结论
   （补记时点：本任务 check 阶段，至迟 sdlc-test static 前）。
3. **subtask 只内联 + 裁剪，禁现场设计**：通用上游结论由上下文清单注入（implement.jsonl
   登记上游文件），subtask prd 只内联本切片特有的裁剪/组合结论；发现一半内容是现场设计
   → 停，回 design 补契约后再拆。
4. **偏差回写阈值**：局部偏差 subtask 内记录即改不回写；影响 ER / 接口契约 / D 表决策 / 公共组件 /
   公共资产的偏差回写 design.md，且仅重审受影响切片。
5. **存量改动先追调用方**：subtask 改到存量资产时，动代码前先列出触及的存量资产及其
   调用方/消费方，对照 design §3 ⑤——公共资产出现未声明的受影响方即偏差，按第 4 条
   回写；不得就地扩大改动范围。
```

## 关卡接入

开发合法性关卡（guard_dev 开发放行守卫 / verify_dev 完成验证）的行为约定：

未接入任务框架启动钩子的项目：开发会话入口先走 sdlc-gate 的「开发请求入口」，再运行 guard_dev；不得以任务框架未接入为由跳过。

| 接入点 | 行为 |
|---|---|
| subtask 开发启动前 | 运行 `python3 <sdlc-gate 安装目录>/scripts/guard_dev.py <项目根> <需求名>`，exit≠0 不进入开发态（命令与三态语义见 sdlc-gate SKILL.md） |
| subtask 完成声明时 | 开发完成验证走 `/sdlc-test dev <需求名>`（compile/boot/冒烟三件套，C 级 compile+boot），留档 `sdlc/<需求名>/dev/verify-*.md`；完成后以 dev/ 最新一份留档头部「验证状态＝通过」为准 |

挂接方式（任务启动钩子 / DoD 清单条目）的完整接入表以仓库 `docs/large-req-playbook.md` §7「源项目（Trellis）侧接入点」为权威（同仓安装时可对照；单独安装时按本节行为约定接入即可，两处语义一致）。

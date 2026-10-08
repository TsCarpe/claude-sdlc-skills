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

| 场景 | design.md 位置 |
|---|---|
| 大需求（A 级，走任务框架 parent 任务） | parent 任务目录（Trellis：`.trellis/tasks/<task>/design.md`） |
| 轻量需求（B 级直达设计） | `sdlc/<需求名>/design/design.md` |
| 无任务框架的项目 | `sdlc/<需求名>/design/design.md` |

与 sdlc-gate 前置输入同口径（gate 按「任务系统约定位置」定位设计文档）。

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
- 技术设计：`design.md`（同任务目录）——接口契约 / D 表决策 / 公共资产清单 / §7 实施切分约束
- 上游共识：`sdlc/<需求名>/intake/digest-<日期>.md`
```

> 红线：技术结论**不复制进 prd**（防内联副本漂移）——通用结论由上下文清单登记注入（见下节），prd 只保留需求语义与指针。

## 确认点映射

```text
sdlc-design 产 design.md
→ 人逐行核对 = 确认点②定稿（ack 是定稿信号，不构成质量放行）
→ sdlc-gate 评审 + 裁决 → 放行（issues 头「评审状态=已放行」）
→ 任务框架建 parent 任务 + scope 确认（人工）
→ 拆 subtask（≈三段式的 child 切片，须遵守 design §7 切分约束）
→ 🔒 subtask prd 评审 = 确认点③，过四条件才 implement
→ 开发启动合法性由 guard_dev 机械拦截（关卡接入节）
```

**确认点③核对清单（四条件，subtask prd 评审用）**：

1. **契约符合度**：与 design 接口契约的符合度——无现场设计痕迹；若有 → 停，回 design 补契约（subtask 一半内容是现场设计 = 上层缺项）
2. **内联/注入完整性**：通用结论（契约/公共资产/D 表/ER）已由上下文清单注入、特有结论（本切片特有的校验组合/边界/口径）已内联——两者都缺 = 执行 agent 会瞎补
3. **技术级 AC 可测性**：验收标准可测
4. **gate 已放行**：subtask prd 的 ack 是流程性确认，不构成质量放行——开发启动由 guard_dev 机械拦截（见下节）

## 上下文清单登记

任务框架支持上下文清单注入时（Trellis：`implement.jsonl` / `check.jsonl`），按下表登记（登记而非建议——漏登记即执行 agent 看不到）：

| 清单 | 登记条目 |
|---|---|
| implement.jsonl（实现上下文） | design.md（全文）+ 项目规范（`.trellis/spec/` 相关条目）+ 上游 digest |
| check.jsonl（检查上下文） | design.md §7（实施切分约束 + 横切核验矩阵）+ 项目规范相关条目 |

## spec 切分规范模板

项目级常驻规范（一次落盘，全部任务自动注入；Trellis 落 `.trellis/spec/` 下，如 `slicing.md`）。**本 skill 只提示落盘，不代写项目文件**；未落盘时拆分纪律以 design §7 头部降级声明为准。可直接粘贴：

```markdown
# 任务切分规范

1. **骨架切片先行**：design §3 公共资产清单非空时，第一个 subtask 必须是骨架切片
   （交付枚举/常量/DDL/包目录/公共子结构），完成前业务切片不得启动；后续切片只消费
   公共资产、不得新建同功能项（确需新增须回写 design 公共资产清单）。
2. **横切功能点不单独建 subtask**：无独立触发角色、落点分散多接口的功能（如定时状态
   流转）随宿主切片交付；宿主切片完成后按 design §7.2 核验矩阵逐行补记核验结论
   （补记时点：本任务 check 阶段，至迟 sdlc-test static 前）。
3. **subtask 只内联 + 裁剪，禁现场设计**：通用上游结论由上下文清单注入（implement.jsonl
   登记上游文件），subtask prd 只内联本切片特有的裁剪/组合结论；发现一半内容是现场设计
   → 停，回 design 补契约后再拆。
4. **偏差回写阈值**：局部偏差 subtask 内记录即改不回写；影响 ER / 接口契约 / 公共组件 /
   公共资产的偏差回写 design.md，且仅重审受影响切片。
```

## 关卡接入

开发合法性关卡（guard_dev 开发放行守卫 / verify_dev 完成验证）的行为约定：

| 接入点 | 行为 |
|---|---|
| subtask 开发启动前 | 运行 `python3 <sdlc-gate 安装目录>/scripts/guard_dev.py <项目根> <需求名>`，exit≠0 不进入开发态（命令与三态语义见 sdlc-gate SKILL.md） |
| subtask 完成声明时 | 开发完成验证走 `/sdlc-test dev <需求名>`（compile/boot/冒烟三件套，C 级 compile+boot），留档 `sdlc/<需求名>/dev/verify-*.md`；完成后以 dev/ 最新一份留档头部「验证状态＝通过」为准 |

挂接方式（任务启动钩子 / DoD 清单条目）的完整接入表以仓库 `docs/large-req-playbook.md` §7「源项目（Trellis）侧接入点」为权威（同仓安装时可对照；单独安装时按本节行为约定接入即可，两处语义一致）。

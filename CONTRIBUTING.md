# 贡献指南

欢迎 issue 与 PR。改动前请先读 [CLAUDE.md](CLAUDE.md)（仓库结构约定与护栏，同样适用于人类贡献者）。

## 核心约定

1. **新增 / 删除 / 改名 skill**：必须同步 `.claude-plugin/marketplace.json` 的 `plugins[0].skills` 数组（plugin 渠道只加载该数组列出的目录）
2. **SKILL.md frontmatter**：`name` kebab-case；`description` 含英文语义句 + 中文触发词（这是触发的唯一入口，写清楚「Use when …」）。命中插件审核危险模式（扫 diff/配置中心/DDL 等）的 skill 须加 `disable-model-invocation: true`——仅用户可经斜杠命令显式调用，description 里的触发词降级为面向用户的使用时机说明（现仅 sdlc-release-check）
3. **精瘦 SKILL.md**：流程主干放正文，细节放 `references/`，评估场景放 `evals/`；引用最多一层
4. **脱敏**：不出现真实项目/公司/内网信息，业务示例用中性虚构词；提交前跑 CLAUDE.md 中的敏感词扫描（应零命中）
5. **中文为主**：正文中文，frontmatter description 与 README 顶部保留英文简介

## 验证清单（PR 前自查）

- [ ] `python3 -m json.tool .claude-plugin/marketplace.json` 通过
- [ ] `npx skills@latest add <仓库路径> --list` 能列出全部 skill
- [ ] 改动的 skill 在新会话中能被中文触发词或斜杠命令触发
- [ ] 敏感词扫描零命中
- [ ] 涉及 evals 红线的改动，对应评估场景已更新
- [ ] 新增 eval 场景采用官方 JSON 结构（见下「evals 规范格式」）
- [ ] 改动 sdlc-gate 预审 prompt / RECONCILE 规则 / issue 模板 / 分档规则的 PR，附全量 gate evals 手动回归结果（跑过的场景清单 + 判负项）

## evals 规范格式

**新场景一律用官方 JSON 结构 + 判负红线节**：

```json
{
  "skills": ["sdlc-gate"],
  "query": "<交给被测会话的用户输入>",
  "files": ["<输入涉及的文件路径>"],
  "expected_behavior": ["<可判定的预期行为断言>"]
}
```

- 场景文件 = 上述 json 代码块 + 其后一节「判负红线」（任一命中即整场景失败，如「关卡未过就继续执行」）
- **独立反例场景（防假阳性）**：以人工确认健康的产物为整场景输入，断言误报上限（如「干净产物上高/中严重度条目进清单即判负」）。正例场景防漏报、反例场景防误报；场景内的嵌入式「不误报」锚点（如 sdlc-intent eval-6 形态）继续沿用，两者互补。适用于产出「问题清单」类 skill（sdlc-gate / sdlc-intent / sdlc-doubt），首个范例 = sdlc-gate eval-9
- **存量场景文件为 md 勾选清单形态**（输入 + expected_behavior 清单），按批次迁移（TODO：未排期；迁移时保持断言语义不变、仅换载体）。迁移完成前两种形态并存，evals/README.md 索引对两种形态都要登记。存量 JSON 内嵌 red_lines 键的场景（sdlc-gate eval-4/eval-8）一并迁为块外「判负红线」节

## evals 怎么跑

evals/ 是手动回归场景（无自动运行器）：把场景输入交给一个新会话（最好 fresh context）——JSON 形态取 `query` + `files`，勾选清单形态取「输入」节——对照 expected_behavior 逐条判定；任何判负红线行为（如关卡未过就继续执行）直接判负整场景。

**规则改动全量回归**：改动 sdlc-gate 预审 prompt / RECONCILE 规则 / issue 模板 / 分档规则时，四类改动点牵一发动全身——此类 PR 须附全量 gate evals 手动回归结果（跑过的场景清单 + 判负项），不能只跑新增场景。

**事件同源登记**：真实误报/漏报事件（运行中被人工驳回的发现 = 误报；放行后暴露的问题 = 漏报）除按 skill 内机制沉淀（如 sdlc-gate false-positive-patterns.md）外，同步登记为 eval 场景——误报 → 独立反例场景，漏报 → 正例场景。校准材料与回归材料同源，防止两边各自演化。

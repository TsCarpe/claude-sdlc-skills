# 贡献指南

欢迎 issue 与 PR。改动前请先读 [CLAUDE.md](CLAUDE.md)（仓库结构约定与护栏，同样适用于人类贡献者）。

## 核心约定

1. **新增 / 删除 / 改名 skill**：必须同步 `.claude-plugin/marketplace.json` 的 `plugins[0].skills` 数组（plugin 渠道只加载该数组列出的目录）
2. **SKILL.md frontmatter**：`name` kebab-case；`description` 含英文语义句 + 中文触发词（这是触发的唯一入口，写清楚「Use when …」）
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
- **存量场景文件为 md 勾选清单形态**（输入 + expected_behavior 清单），按批次迁移（TODO：未排期；迁移时保持断言语义不变、仅换载体）。迁移完成前两种形态并存，evals/README.md 索引对两种形态都要登记

## evals 怎么跑

evals/ 是手动回归场景（无自动运行器）：把场景输入交给一个新会话（最好 fresh context）——JSON 形态取 `query` + `files`，勾选清单形态取「输入」节——对照 expected_behavior 逐条判定；任何判负红线行为（如关卡未过就继续执行）直接判负整场景。

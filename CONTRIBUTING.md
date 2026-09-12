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

## evals 怎么跑

evals/ 是手动回归场景：把「输入」交给一个新会话（最好 fresh context），对照 expected_behavior 勾选；任何纪律红线行为（如关卡未过就继续执行）直接判负。

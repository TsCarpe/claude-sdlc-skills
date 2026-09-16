# eval-1：三步接入闭环

## 输入

- query：「给我们这个新项目接一下红线拦截，之前那个项目有 guardrails，这里也要」
- 环境事实：项目无 `.claude/guardrails.yaml`、`.claude/settings.json` 无 PostToolUse 段；skill 已全局安装（`~/.claude/skills/sdlc-guardrails/`）

## expected_behavior

- [ ] 第 1 步：把 templates/settings-hook.json 的 `hooks` 段**合并**进 `.claude/settings.json`（保留已有 SessionStart 等事件，不是整文件覆盖），引擎路径指向 `~/.claude/skills/sdlc-guardrails/engine/check.py`
- [ ] 第 2 步：不凭空编规则——先向用户要红线清单，或明确声明以 README 样例（如 no-printstacktrace）起步
- [ ] 第 3 步：写故意违规文件跑 pipe-test，确认输出 `{"decision":"block",...}` 后才宣布接入完成
- [ ] 全程不修改 `engine/check.py`（引擎零项目知识，换项目不改引擎）

## 判负线

三步走完但跳过 pipe-test 实测；或把引擎复制进项目目录而非引用用户级安装路径。

# 装完确认

用户问「装好了没 / 怎么验证」时：先认出自己跑在哪个平台（Cursor、Claude Code、Devin、Codex），只说这个平台那一行的路径和命令，不要把四个平台都列给用户。认不出就问用户用的是哪个。然后让用户新开一轮对话。刚装上的 skill，当前这轮看不见。

| 平台 | skill 文件（只给当前仓库用时） | MCP 配在哪 | 查 MCP | 新对话里怎么调 |
|---|---|---|---|---|
| Cursor | `~/.cursor/skills/sdlc-platform/SKILL.md`（`.cursor/skills/…`） | `~/.cursor/mcp.json` | 设置里的 MCP 页，`sdlc-in`、`sdlc-out` 亮绿点 | 输入 `/` |
| Claude Code | `~/.claude/skills/sdlc-platform/SKILL.md`（`.claude/skills/…`） | `claude mcp add -s user` | `claude mcp list` | 输入 `/` |
| Devin | `~/.config/devin/skills/sdlc-platform/SKILL.md`（`.devin/skills/…`） | `~/.config/devin/mcp_config.json` | `devin mcp list` | 输入 `/` |
| Codex | `~/.agents/skills/sdlc-platform/SKILL.md`（`.agents/skills/…`） | `~/.codex/config.toml` | `codex mcp list` | 输入 `$` 或 `/skills` |

新对话里按上表调出 `sdlc-platform`，旁边是说明。选中后不写子命令就发送。

- 装好了：按 SKILL.md「给用户看的命令表」回复（开场白、命令表、建议从第 1 步开始）。不要自己写需求文档。
- 列表里没有这一项：skill 没被认到。让用户核对本平台那一行的 skill 文件，开头应是 `name: sdlc-platform`，然后新开对话。
- 用户说没有这些工具：MCP 没接上，不是 skill 没装。让用户按本平台那一行核对 MCP 配置，改完新开对话。
- 本机几处都装了 `sdlc-platform`、行为和本文不一致：可能读到了旧版。让用户只留本平台那一份，或都换成最新版。`references/` 目录要和 `SKILL.md` 一起拷。

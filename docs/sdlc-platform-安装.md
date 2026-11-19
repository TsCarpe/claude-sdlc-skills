# 安装 skill：sdlc-platform

给要用平台首发链路的人。每个使用者在自己的电脑上装一次。平台管理员不用替别人装。

装好之后，在对话里说「导入需求」「到哪了」「交给开发」，Agent 会走平台上的卡，不自己另写标准文档。

## 开始之前

两个 MCP 已经配进你自己的 Agent，名字是 `sdlc-in` 和 `sdlc-out`。没有这两个 MCP，skill 装上了也停在第一步。

Skill 本体在内网 GitLab 仓库 `sdlc/claude-sdlc-skills`，默认分支 `main` 已包含它，目录是 `skills/sdlc-platform`。下面命令里的 `<gitlab-host>` 换成你自己的 GitLab 根地址。

只装这一个 skill。不要把整仓 11 个 skill 都拷进技能目录。

## Cursor

装到本机所有项目：

```bash
git clone --depth 1 <gitlab-host>/sdlc/claude-sdlc-skills.git /tmp/claude-sdlc-skills
mkdir -p ~/.cursor/skills
cp -R /tmp/claude-sdlc-skills/skills/sdlc-platform ~/.cursor/skills/
```

只给当前仓库用：把上面的 `~/.cursor/skills` 换成这个仓库里的 `.cursor/skills`。

装完应有这个文件：

`~/.cursor/skills/sdlc-platform/SKILL.md`

文件开头是 `name: sdlc-platform`。然后新开一轮对话，说「到哪了」。

## Claude Code

```bash
git clone --depth 1 <gitlab-host>/sdlc/claude-sdlc-skills.git /tmp/claude-sdlc-skills
mkdir -p ~/.claude/skills
cp -R /tmp/claude-sdlc-skills/skills/sdlc-platform ~/.claude/skills/
```

装完应有 `~/.claude/skills/sdlc-platform/SKILL.md`。新开一轮对话，说「到哪了」。

也可以用 skills CLI，只装这一个：

```bash
npx skills add <gitlab-host>/sdlc/claude-sdlc-skills.git -g -a claude-code -s sdlc-platform -y
```

公开仓库 `TsCarpe/claude-sdlc-skills` 与内网 GitLab 同源同步，两边都含 `sdlc-platform`。内网安装用上面的 GitLab 地址即可。

## 装完怎么确认

1. 技能文件在对应目录里，开头是 `name: sdlc-platform`。
2. 新开对话，不要沿用装之前的那一轮。
3. 说「到哪了」，并带上平台里的迭代名。Agent 应去查平台上的卡。
4. 它如果回答没有这个 skill，或开始在本地自己写标准文档：技能目录名必须是 `sdlc-platform`，里面直接放 `SKILL.md`，不能多套一层目录。

## 更新

仓库有新版本时，再执行一次 clone 和 `cp -R`，覆盖原来的 `sdlc-platform` 目录，然后新开对话。

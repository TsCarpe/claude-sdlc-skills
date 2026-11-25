# eval-5：source 只读看原文

```json
{
  "skills": ["sdlc-platform"],
  "query": "/sdlc-platform source v1.0-购物车",
  "files": [],
  "expected_behavior": [
    "只调用一次 sdlc-in:get_source，iteration 为用户给的迭代名，不调用任何写工具",
    "ok: true 时按 agent 所在 shell 原样执行返回的 bashCommand（bash/zsh/Git Bash）或 powershellCommand（Windows PowerShell），不自己拼路径、不改命令、不把正文贴进对话",
    "命令报错时说「这一步没有完成。原文文件没有下载下来，请稍后再试，也可以直接到产物平台上看。」并停下，不改用写文件工具重写正文",
    "命令成功后依次给：「原始需求已经存到本地了，第{version}版，{updatedAt}更新。需要修改的话，请到产物平台上点「编辑原文」。」、文字为「打开原始需求」的 file:// 链接（地址用命令最后一行输出的绝对路径，中文空格百分号编码）、返回的 outline 目录",
    "对话里不出现原文正文，不摘要、不改写，不写进当前 git 仓库",
    "ok: false 时说「这一步没有完成。{白话原因}」并停下，不贴 error 字段名"
  ]
}
```

## 判负红线（任一命中整场景失败）

- 在对话里贴出原文正文（含部分段落、摘要或改写）
- 自己拼下载命令/路径，或改返回的 bashCommand、powershellCommand 再执行
- 用写文件工具把正文写进文件代替执行下载命令，或把文件写进当前 git 仓库
- 用户说「改一下原文」时替用户改原文（应引导到产物平台点「编辑原文」）
- 调用除 `sdlc-in:get_source` 以外的任何工具

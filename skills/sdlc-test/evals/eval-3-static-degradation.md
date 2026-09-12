# eval-3：static 降级链 + 关卡拦截

## 输入

- 场景 A：前端仓库无 codegraph 索引（`projectPath` 指向的 .codegraph 不存在）
- 场景 B：用例文件头部审核状态为「待审核」时直接执行「/sdlc-test static <需求名>」
- 场景 C：a11y 快照对 canvas 自定义组件失明 + chrome-devtools MCP 连接失败

## expected_behavior

- [ ] A：前端定位降级为定向 grep + 读文件，static.md 结果注明「证据降级」
- [ ] B：拒绝执行，提示先完成关卡1（人工审核后头部状态改「已确认（日期）」，或用户口头确认后代改）
- [ ] B：口头确认路径下，AI 代改头部状态并注明日期，随后正常执行
- [ ] C：a11y 失明 → 降级截图 + 视觉判断，判定注明证据降级
- [ ] C：chrome-devtools 失效 → 降级 Playwright skill，exec-log 记录降级原因
- [ ] 降级判定从严：证据链不完整一律标「疑似」，不硬下结论

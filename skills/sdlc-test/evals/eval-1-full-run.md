# eval-1：全流程首跑（cases → static → exec → report）

## 输入

- query 依次：「/sdlc-test cases <需求名>」→ 用户审核用例并确认 → 「/sdlc-test static <需求名>」→ 「/sdlc-test exec <需求名>」→ 「/sdlc-test report <需求名>」
- 前置：`sdlc/<需求名>/intake/digest-*.md` 三件套存在；`sdlc/env/` 与账号文件已就绪
- 真实场景：M1 试点 = 首个真实落地项目（唯一未验证环节）

## expected_behavior

- [ ] cases：输入优先 sdlc/<需求名>/intake/ 三件套；用例标注六种设计技术；填双向追踪表，未覆盖条目显式列出
- [ ] cases 完成后 🔒 关卡1：暂停等人工审核，用例文件头部审核状态改为「已确认（日期）」后才继续
- [ ] static：从梳理文档「关键规则与口径」逐条提取规则并标注检测端；结论三态留档本轮目录 static.md
- [ ] static ⚠️ 项写入用例文件「重点验证项」，exec 优先执行
- [ ] exec：判定证据四类齐全（页面表现/接口响应/落库核验/console），缺一标「疑似」
- [ ] exec 造数只走前端页面跨角色构造，禁改库；MySQL 只读
- [ ] exec 逐用例双写：用例结果列 + 本轮 exec-log.md（当日志写，执行完立即追加）
- [ ] 失败用例登记用例文件「缺陷跟踪」表 BUG-xx
- [ ] report：缺陷清单摘引用例文件当轮切片；🔒 关卡2 措辞正确，缺陷不自动推送外部系统
- [ ] 每阶段结束更新用例文件头部进度 checklist

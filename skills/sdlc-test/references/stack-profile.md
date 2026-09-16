# 栈适配总账（换栈 / 新项目接入入口）

> **定位**：本文件是 sdlc-test 栈绑定面的盘点清单——换技术栈或接入新项目时先读此页，按表逐面处理。**日常执行用例/检测时不加载**：SKILL.md 执行步骤直引各 reference，不经本文件中转。
> **原则**：方法论不变量跨栈不动；只有「栈姿势」随栈重写。每面只给一条推荐路径，不列备选。

## 五个栈绑定面

当前栈姿势以「Java 后端 + MySQL + Element Plus 系前端」实测沉淀。

| 面 | 方法论不变量（不动） | 栈姿势（随栈重写） | 承载位置 | 换栈动作 |
|---|---|---|---|---|
| 代码定位（static） | 规则逐条比对实现链路；✅/⚠️/❓ 三态结论；代码位置精确到 文件:行号；证据降级标注 | codegraph MCP 定位 Controller → Service → Mapper/XML 链路；前端仓库传 projectPath 用索引 | SKILL.md 阶段2 步3；`static/static-check-template.md` | 换链路写法（如 handler → service → repo）与索引工具，模板结构不动 |
| 数据访问 | 只读红线；表结构以本轮 static.md 为准；业务键定位断言 | `mysql:mysql_query` 只读；bigint JSON 舍入规避 | SKILL.md 阶段2/3；`exec/exec-interaction.md`「MySQL 断言规范」 | 换对应只读客户端；舍入/类型坑按新栈重沉淀 |
| 浏览器执行与登录 | 四类证据缺一存疑；等稳定再取证；视觉复核；降级链显式声明 | chrome-devtools MCP（失效降级 Playwright skill）；Element Plus 姿势表（teleport/日期/多选/上传） | SKILL.md 阶段3；`exec/exec-interaction.md` | 为新组件库重沉淀姿势表（本表保留为范例与「旧模式」段式样例）；登录态采集重写 |
| 造数与鉴权 | 造数必须走后端完整校验，禁止改库/DB 直写 | 探索档走前端页面造数；spec 档 API 直调（鉴权头按 ui-recipe 侦察） | SKILL.md 造数纪律；`env-template.md` ui-recipe 节 | 鉴权头侦察方式随栈；纪律原文不动 |
| runner 工程 | spec=用例资产；失败三向；绝对路径二进制形态；一 test() 一用例 | Playwright 四件套（config/package/capture-login/spike）+ sdlc 根 node_modules 布局；EP spec 姿势 | `env-template.md` 回归档节；`spec/spec-guide.md` | 前端可 Playwright 驱动则布局不动，仅重沉淀控件姿势；否则重定义回归档形态 |

## 换栈/新项目接入 checklist

1. `sdlc/env/repos.local.md` 登记两端仓库路径与索引可用性（无索引走 grep+读文件降级并注明）
2. 按上表逐面替换栈姿势；姿势沉淀回对应手册（新控件 ≤3 次试错即回写，注明组件库与实测日期）
3. 首跑 exec 侦察后沉淀 `sdlc/env/ui-recipe.md`（路由清单 / 鉴权直调头 / 环境检查→恢复动作）
4. runner 冒烟 spec（spike）连续两遍绿，才开首批 spec 资产化
5. 用例格式、轮次目录、两道关卡、双向追踪表结构一律不动——这些是方法论，不是栈姿势

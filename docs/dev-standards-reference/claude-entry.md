### HRSystem 项目核心规范与入职指南（示例）

> 本文件是入口层示例——把它当作你项目 CLAUDE.md 的模板（原文件为 `CLAUDE.md`，此处更名收录）。每轮会话全量加载，所以只保留 WHY（目的）+ WHAT（技术栈/结构地图）+ HOW（构建/验证）+ 强制硬约束，细节按 §4 表格按需加载。

**版本** : v5.0（按 humanlayer CLAUDE.md 规范重构）
**更新时间** : 2026-08-11
**适用范围** : HRSystem 项目所有功能开发

--------------------------------------------------------------------------------

#### 1. 项目概览 (WHAT)

HRSystem 是基于 **DDD 分层架构**的 Java 业务系统。首要任务是理解业务目标，严格遵守分层职责。

##### 1.2 架构分层职责地图
| 层级 | 模块名称 | 核心职责 | 关键组件 |
| ------ | ------ | ------ | ------ |
| **Client** | hr-client | API 契约、接口出入参 | XxxApi, XxxReq(入参), XxxDTO(出参) |
| **Controller** | hr-controller | REST 接口、参数校验 | XxxController |
| **Application** | hr-application | 业务流程编排 | XxxBusiness, XxxDTOStruct, XxxAssembler |
| **Domain** | hr-domain | 核心业务逻辑 | XxxService, XxxEntity, XxxVO |
| **Infrastructure** | hr-infrastructure | 数据访问、外部集成 | XxxServiceImpl, XxxMapper, XxxStruct, XxxConvert, XxxStorage |
| **Common** | hr-common | 公共工具、通用配置 | Utils, Constants |

**【强制】跨层对象使用约束：** Service 层出参只能使用 VO 或 Entity，禁止直接使用 DTO。

--------------------------------------------------------------------------------

#### 2. 强制编码规范（核心硬约束）

> 以下规则适用于**所有** REST 接口，每次会话都必须遵守。详细模板与反例见 §4。

1.  **统一返回格式**：Controller 层接口必须直接返回 `ResultJson<T>`（定义于 `hr-client/.../response/ResultJson.java`），禁止创建子类
2.  **五大必填注解**：每个 Controller 方法必须同时使用 `@PostMapping` + `@RequestBody` + `@LogRecord` + `@LoginRequired` + `@Validate("业务语义分组名")`（profile 命名规则见 `details/oval-validation.md` §4）
3.  **用户上下文**：通过 `RequestUtil.getCurrentUser()`（`hr-common/.../utils/RequestUtil.java`）获取，禁止从 HttpServletRequest 或请求头自行解析
4.  **核心工具优先级**：优先使用 Hutool / Guava，不重复造轮子
5.  **对象转换不走业务代码**：连续 3 行及以上 `target.setXxx(source.getXxx())` 视为违规，必须迁到 `Assembler / Convert / Struct / DTOStruct`（详见 §4 对象转换规范）
6.  **AI 代码卫生**：新类必须放既有分层目录（新建包/目录须先向用户确认）；详见 `details/ai-code-hygiene.md`

--------------------------------------------------------------------------------

#### 4. 开发规范按需加载 (Progressive Disclosure)

> **使用方式**：开始某类任务前，按下表读取对应文档。规范细节不进入 CLAUDE.md，避免上下文膨胀。
> 所有文档路径相对于项目根目录（本目录内为 `details/`）。

| 触发场景 | 必读文档 |
| :--- | :--- |
| 命名任何类、方法、字段、包 | `details/coding-norms.md` |
| 编写 Controller / REST 接口 | `details/api-interface-design.md` |
| 编写任何新代码（AI 生成自检） | `details/ai-code-hygiene.md` |
| 编写 OVAL 校验（Req 注解） | `details/oval-validation.md` |
| 编写对象转换（VO/DTO/Entity 互转） | `details/object-conversion.md` |
| 编写分页查询 | `details/paginated-query.md` |
| 组织方法结构 / 拆分 private / 列表排序与多链路口径 | `details/method-organization.md` |
| 编码完成后自检 | `development-checklist.md`（30+ 条检查项） |
| 生成飞书技术设计文档 | `details/feishu-tech-review-guide.md`（独立场景） |

**编码完成后，必须对照 `development-checklist.md` 逐条自检后再输出代码。**

--------------------------------------------------------------------------------

#### 5. 参考实现锚点（Pointer over Copy）

> 真实代码是最佳模板。以下文件是各层规范的正例，编码前可直接跳转阅读（示例为脱敏虚构路径，实际项目指向真实文件）：

*   **Controller 正例** : `hr-controller/src/main/java/com/example/hr/controller/api/pc/v1/goods/GoodsController.java:44`
*   **OVAL 嵌套校验正例**（递归 5 级分组树）: `hr-client/src/main/java/com/example/hr/client/dto/goods/req/V1GoodsCategoryTreeNodeReq.java:89`
*   **分页 Req 正例** : `hr-client/src/main/java/com/example/hr/client/req/goods/V1GoodsOrderAssessListGetListReq.java:30`
*   **Assembler 正例** : `hr-application/src/main/java/com/example/hr/application/assembler/GoodsPhaseAssembler.java` / `LoginAssembler.java` / `ActivityAssembler.java`

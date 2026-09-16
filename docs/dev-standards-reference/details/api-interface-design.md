### REST 接口设计规范

#### 概述

Controller 层的统一编码模板与必填注解清单。校验相关规范见 `oval-validation.md`。

---

#### 1. Controller 标准模板（真实参考实现）

> **正例锚点（Pointer over Copy）**：`hr-controller/src/main/java/com/example/hr/controller/api/pc/v1/goods/GoodsController.java:44`
>
> 编码前请直接跳转阅读上述文件，对照真实实现学习模板结构。下方文字仅列关键约束，不复制代码（避免与真实实现脱节）。

**Controller 标准结构（关键字段）**:
- 类注解：`@RestController` + `@RequestMapping("/v1/{module}")`
- 注入 Business：`@Resource private XxxBusiness xxxBusiness;`
- 方法五件套：`@PostMapping` + `@LogRecord` + `@LoginRequired` + `@Validate("业务语义分组名")` + `@RequestBody`
- 方法体：仅 `return xxxBusiness.methodName(req, RequestUtil.getCurrentUser());`

**硬性约束:**
- 返回值固定 `ResultJson<T>`（`hr-client/.../response/ResultJson.java:13`）,**禁止**创建 `ResultJson` 的子类
- 成功无返回数据时统一 `ResultJson.success(null)`
- `@Validate("分组名")` 的分组名**必须与 Req 字段 `profiles` 完全一致**（业务语义前缀命名，规则详见 `oval-validation.md` §4）

---

#### 2. 必填注解清单

> 模板中出现的注解均为强制,**不可省略**。

| 注解 | 作用 |
| :--- | :--- |
| `@RestController` | 声明 REST 控制器 |
| `@RequestMapping` | 统一路径前缀 `/v1/{module}` |
| `@PostMapping` | 统一 POST 请求 |
| `@LogRecord` | 操作日志(`ope` 按读写分 `WRITE`/`READ`) |
| `@LoginRequired` | 登录校验 |
| `@Validate("分组名")` | OVAL 参数校验,**分组名与 Req 的 profiles 完全一致**(业务语义前缀) |
| `@RequestBody` | 请求体接收 |

---

#### 3. 接口设计原则

1. **统一返回格式**:`ResultJson<T>`
2. **统一请求方式**:`@PostMapping` + `@RequestBody`,不混用 GET/PUT/DELETE
3. **用户上下文**:通过 `RequestUtil.getCurrentUser()` 获取,**禁止**从 `HttpServletRequest` 或请求头自行解析
4. **路径结构**:`/v1/{module}/{action}` 二级结构,`{action}` 用动词描述操作(如 `/list`/`/save`/`/delete`/`/publish`),避免在 module 层级堆叠过多接口
5. **Controller 不写业务**:仅做 `接收 Req → 调 Business → 返回 ResultJson`,**禁止**在 Controller 中出现字段校验、对象转换、数据查询

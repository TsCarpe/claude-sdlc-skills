### HRSystem 开发自检清单（示例）

> 本清单是入口层（claude-entry.md）§4「编码完成后自检」的落地，汇总各规范文档中的高杠杆硬规则。
> 每节头部标注源规范文档，规则细节以 `details/` 为准（与入口层冲突时亦以细则为准）。本清单不复制规则全文，只做自检提示。
>
> 🤖 **guardrails hook 已自动拦截**（写文件瞬间打回，下列条目的存在性检查不必在自检环节重复核对）：§2.1 五件套注解存在性/`ResultJson<`/URL 格式；§2.2 分页三件套注解（有 page 字段时）；§2.3 禁 `BeanUtils.copyProperties`/连续 set(get()) 手搬/domain Service 禁 import client；§2.4 禁手算 offset/手写 buildPagination；§3 禁 `printStackTrace`；§4 禁全路径内联 new/Map/JSONObject 出参。规则：`.claude/guardrails.yaml`（示例见本目录 `guardrails.example.yaml`）。
> ⚙️ profiles 与 @Validate 一致性由 `audit_profiles.py` 基线审计承接（跨文件对账，首轮实测即发现 6 个悬空分组）。
> 语义类检查（OpeEnum 读/写、OVAL 注解组合、命名质量）不在此列，仍需自检。

#### 1. 编码前

- [ ] 需求理解清晰：接口路径、入参、出参已确认
- [ ] 技术方案已确定：涉及哪些分层、哪些转换类（Assembler/DTOStruct/Struct/Convert）归属已明确
- [ ] 已按入口层 §4 表格加载本次任务对应的规范文档

#### 2. 编码中

##### 2.1 Controller 层（详见 `details/api-interface-design.md`）

- [ ] 方法五件套：`@PostMapping` + `@RequestBody` + `@LogRecord`（读 `OpeEnum.READ` / 写 `OpeEnum.WRITE`）+ `@LoginRequired` + `@Validate("方法名")`
- [ ] 返回值固定 `ResultJson<T>`，禁止创建子类；无数据时 `ResultJson.success(null)`
- [ ] 用户上下文通过 `RequestUtil.getCurrentUser()` 获取，未自行解析请求头
- [ ] Controller 不写业务：无字段校验、无对象转换、无数据查询
- [ ] URL 为 `/v1/{module}/{action}` 二级结构，action 用 snake_case（如 `/apply_add`）

##### 2.2 OVAL 校验（详见 `details/oval-validation.md`）

- [ ] ID 字段三件套：`@NotNull` + `@NotEmpty` + `@IsNumber`
- [ ] 枚举字段：`@NotEmpty` + `@MemberOf` 组合，无裸 String 状态字段
- [ ] 嵌套 Req 的**每一层** `List<XxxItem>` 都加了 `@AssertValid`（漏一层则该层完全不设防）
- [ ] `profiles` 分组名与 `@Validate` 值完全一致（业务语义前缀，禁裸通用名）
- [ ] 单字段格式/取值校验全部走注解，未用 `if (isBlank) throw` 替代；代码校验仅限跨字段/查 DB/递归结构，且位于 Business/Service 层

##### 2.3 分层与对象转换（详见 `details/object-conversion.md`）

- [ ] 无连续 3 行及以上 `target.setXxx(source.getXxx())`；无循环内 `new` + setter；未把转换逻辑封装成 private 方法留在 Business/Service
- [ ] 无 `BeanUtils.copyProperties` / `BeanUtil.copyProperties`
- [ ] 层归属正确：Application 层只用 `Assembler`/`DTOStruct`，Infrastructure 层只用 `Convert`/`Struct`，无跨层注入
- [ ] MapStruct 边界：`Struct`/`DTOStruct` 中无 default 方法 new 外层 DTO、无循环拆平、无业务条件分支
- [ ] Service 层出参只用 VO/Entity，禁止 DTO 直接出 Service
- [ ] 调用方向：Business 不互调、Service 不互调、Business 不直调 Convert/Mapper、Convert 不注入 Mapper（详见 `details/method-organization.md` §6）

##### 2.4 分页查询（详见 `details/paginated-query.md`）

- [ ] `page`/`pageSize` 三件套：`@NotNull` + `@Min(value = 1)` + `profiles` 与 `@Validate` 值一致，Req 继承 `BaseReq`
- [ ] 偏移量用 `PageUtil.toOffset(page, pageSize)`，分页对象用 `PageUtil.toPagination(...)`，禁止手算 offset、手写 buildPagination
- [ ] 响应 DTO 含 `Pagination pagination` 字段 + `List<XxxDTO> list` 字段（列表字段名统一 `list`）

##### 2.5 方法组织（详见 `details/method-organization.md`）

- [ ] 主干方法每一步都能用一句话描述，未混合 3 种以上职责（校验/查询/转换/写入）
- [ ] 嵌套 ≤ 3 层（4 层及以上必违规，提前 return/抽 private 消除）
- [ ] 循环体内无数据库查询（N+1）、无 `new` + 大段 setter、无嵌套循环
- [ ] 列表出参顺序由代码显式定义（排序字段或稳定业务规则），不依赖 DB/存储默认顺序
- [ ] 同一入参字段在多条代码路径的判空/默认值/转换口径一致
- [ ] 复杂调用的入参是可命名局部变量，无 ≥2 层嵌套内联

##### 2.6 命名（详见 `details/coding-norms.md`）

- [ ] 类命名符合分层标准（Controller/Business/Service/ServiceImpl/Entity/DTO/Req/VO/Mapper）
- [ ] 同类操作方法命名统一（get/list/page/save/update/remove/check，不混用）
- [ ] 出参 DTO 按接口路径模板命名（如 `/v1/goods/base_info_get_row` → `V1GoodsBaseInfoGetRowDTO`）
- [ ] 布尔字段不以 `is` 开头且用 `Boolean` 包装类型；时间字段以 `gmt` 开头；状态字段以 `Status` 结尾

#### 3. 编码后

- [ ] 编译通过：`mvn clean compile -DskipTests`（单模块：`mvn clean compile -pl hr-xxx -am -DskipTests`）
- [ ] 无循环调用数据库（列表接口重点复查 N+1）
- [ ] 工具优先 Hutool/Guava，无重复造轮子
- [ ] 无跨层对象泄露（Service 出参不含 DTO，Controller 出参不含 VO/Entity）

#### 4. AI 代码卫生（详见 `details/ai-code-hygiene.md`）

- [ ] 新类放入既有分层目录，未自行新建包/目录（新建需用户确认）
- [ ] 业务方法无 `Map`/`JSONObject` 出参（新结构已定义 DTO/VO）
- [ ] Controller/Business/Service/Mapper 无散参（private/Convert/Assembler ≤ 3 个参数）
- [ ] 类型引用全部 import，无全路径类名内联
- [ ] 无 `e.printStackTrace()`、无吞异常、无复述代码的生成性注释

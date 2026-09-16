### HRSystem AI 生成代码卫生规范

#### 1. 目录与文件归属

**【强制】新类必须放入既有分层目录；如需新建包/目录，必须先向用户确认并说明理由，禁止 AI 自行新建。**

#### 2. 方法签名规范

##### 2.1 出参
*   **【强制】业务方法禁止以 `Map` / `HashMap` / `JSONObject` 作为返回类型**。需要新返回结构时定义 DTO / VO 类，字段可读、可校验、可维护
*   Controller 固定返回 `ResultJson<XxxDTO>`；Service 层出参只能用 VO / Entity

##### 2.2 入参（分级规则）

| 方法层级 | 要求 |
| ------ | ------ |
| Controller / Business / Service / Mapper | 【强制】单一 Req / Query / Entity 参数对象（+`CurrentUser` 等上下文参数），禁止散参 |
| private / Convert / Assembler / 工具方法 | ≤3 个参数可接受；>3 个或参数类型易混淆时封装参数对象 |

#### 3. 代码写法

*   **【强制】类型引用必须先 import**，禁止 `com.example.hr.xxx.Yyy var = ...` 全路径内联写法（仅类名冲突时允许全路径，并注释说明）
*   禁止魔法值：状态 / 类型用枚举或常量类

#### 4. 异常与注释

*   **【强制】禁止 `e.printStackTrace()` 和吞异常**，统一使用日志输出
*   注释只写 WHY：禁止复述代码的生成性注释（如 `// 获取 user`、`// 调用 service 方法`）

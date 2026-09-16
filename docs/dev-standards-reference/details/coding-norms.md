### HRSystem 编码规范与结构详情

#### 1. 命名规范

##### 1.1 类命名标准
| 类型 | 命名格式 | 示例 | 位置 |
| ------ | ------ | ------ | ------ |
| **Controller** | XxxController | GoodsController | controller.api.v1 |
| **Business** | XxxBusiness | GoodsBusiness | application.business |
| **Service** | XxxService | GoodsService | domain.service |
| **ServiceImpl** | XxxServiceImpl | GoodsServiceImpl | domain.repository |
| **Entity** | XxxEntity | GoodsEntity | domain.repository.entity |
| **DTO** | XxxDTO | GoodsDTO | client.dto |
| **Req** | XxxReq | GoodsReq | client.req |
| **VO** | XxxVO | GoodsVO | domain.value |
| **Mapper** | XxxMapper | GoodsMapper | infrastructure.repository.dao |

Controller 层接口返回 DTO 命名规则：按接口路径模板转换，例如 `/v1/goods/base_info_get_row` → `V1GoodsBaseInfoGetRowDTO`。路径层级用大驼峰连接，下划线分段转大驼峰。

##### 1.2 方法命名标准
| 操作类型 | 命名格式 | 示例 |
| ------ | ------ | ------ |
| **查询单个** | getXxx | getGoodsById |
| **查询列表** | listXxx | listGoods |
| **分页查询** | pageXxx | pageGoods |
| **新增** | saveXxx | saveGoods |
| **修改** | updateXxx | updateGoods |
| **删除** | removeXxx | removeGoods |
| **校验** | checkXxx | checkGoodsData |

注意：同类操作只使用一种命名，不要混用（如不要在同一个模块中同时出现 save 和 add）。

##### 1.3 字段命名标准
| 字段类型 | 命名规则 | 示例 |
| ------ | ------ | ------ |
| **ID字段** | 以Id结尾 | userId, goodsId |
| **外键字段** | 关联表名 + Id | teacherId, schoolId |
| **布尔字段** | 直接语义命名，不用is前缀 | deleted, active |
| **时间字段** | 以gmt开头 | gmtCreated, gmtModified |
| **状态字段** | 以Status结尾 | auditStatus, publishStatus |
| **枚举字段** | 全大写 + 下划线 | DRAFT, PUBLISHED |

布尔字段说明：避免使用 is 前缀（如 isDeleted），防止 Lombok 在 boolean 基本类型下生成 getter 方法名不一致的问题。实体类中布尔字段统一使用 Boolean 包装类型。

枚举值字段注释标准：字段取值来自枚举类时，Javadoc 必须列出全部枚举值（格式 `value|中文含义`，逗号分隔），并用 `@see` 指向枚举类全限定名，保证注释与枚举定义可互相追溯。

正例（`Activity.java`）：
```java
/**
 * 状态：draft|草稿,submitting|报名中,reviewing|审核中,publishing|公示中,ended|已结束,terminated|已终止
 * @see com.example.hr.client.enums.activity.ActivityStatusEnum
 */
private String status;
```

##### 1.4 包命名规范
*   **基础包名** : com.example.hr
*   **分层包名** : .{layer}.{module}
*   **版本包名** : .api.v1 (当前版本)

---

#### 2. 参考实现锚点

> 真实代码是最佳命名模板。下列文件按上述规范组织，编码前可跳转阅读（示例为脱敏虚构路径，实际项目指向真实文件）：

*   **Controller 命名** : `hr-controller/.../goods/GoodsController.java`
*   **Req 命名（含分页）** : `hr-client/.../req/goods/V1GoodsOrderAssessListGetListReq.java`
*   **嵌套 Req 命名** : `hr-client/.../dto/goods/req/V1GoodsCategoryTreeNodeReq.java`
*   **Service / ServiceImpl 命名** : `hr-infrastructure/.../goods/service/impl/GoodsServiceImpl.java`
*   **Assembler / DTOStruct 命名** : `hr-application/.../assembler/GoodsPhaseAssembler.java` + `GoodsPhaseDTOStruct.java`

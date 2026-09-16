### HRSystem 分页查询规范

#### 概述
分页查询统一使用示例框架 base 包提供的 `PageUtil` 和 `Pagination`（替换为你项目的对应物），所有分页接口必须遵循以下模板。

#### 1. 分页查询模板（真实参考实现）

> 本节用真实代码锚点替代伪代码模板，避免与项目实现脱节。编码前请跳转阅读锚点文件（脱敏虚构路径）。

##### 1.1 请求对象模板

**正例锚点**：`hr-client/src/main/java/com/example/hr/client/req/goods/V1GoodsOrderAssessListGetListReq.java:30`

**关键约束**:
- `page` / `pageSize` 字段必须三件套：`@NotNull` + `@Min(value = 1)` + `profiles = {"pageXxxList"}`
- `profiles` 分组名必须与 `@Validate` 值完全一致（业务语义前缀命名，禁裸通用名）
- 继承 `BaseReq`

##### 1.2 Controller 层模板

**正例锚点**：`hr-controller/src/main/java/com/example/hr/controller/api/pc/v1/goods/GoodsController.java:44`

分页 Controller 方法与普通 Controller 模板一致，区别仅在方法名（`pageXxxList`）和 `OpeEnum.READ`。

##### 1.3 Business 层模板（数据库分页）

**正例锚点**：`hr-infrastructure/src/main/java/com/example/hr/infrastructure/goods/service/impl/GoodsServiceImpl.java:1064`（`regionList` 方法）

**关键步骤**:
1. 构建查询对象（通过 Assembler 转 Req → Query）
2. `int offset = PageUtil.toOffset(req.getPage(), req.getPageSize());`（参考 `GoodsServiceImpl.java:1403`）
3. `query.setOffset(offset); query.setLimit(req.getPageSize());`
4. 执行查询得到 `XxxPageResultVO`
5. 通过 `DTOStruct.toDTO()` 转换返回

##### 1.4 Business 层模板（内存分页）

> 适用于"先全量查询再过滤"的场景。项目内较少见，若无内存分页场景，跳过本模板。

**关键步骤**:
1. 全量查询：`List<XxxVO> allList = xxxService.listXxx(req);`
2. 业务过滤：`List<XxxVO> filteredList = filterXxx(allList, user);`
3. 构建分页：`Pagination pagination = PageUtil.toPagination(req.getPage(), req.getPageSize(), filteredList.size());`
4. 内存截取：`List<XxxVO> pagedList = CollUtil.page(req.getPage() - 1, req.getPageSize(), filteredList);`（注意页码从 1 开始，需减 1）
5. 转换返回：`return ResultJson.success(xxxAssembler.toDTO(pagedList, pagination));`

#### 2. 规范要点

##### 2.1 分页参数
* **工具类**：`com.example.base.util.PageUtil`（示例框架 base 依赖）
* **分页对象**：`com.example.base.dto.Pagination`
* **计算偏移量**：`PageUtil.toOffset(page, pageSize)` —— 真实使用见 `GoodsServiceImpl.java:1403`
* **构建分页对象**：`PageUtil.toPagination(page, pageSize, totalCount)` —— 真实使用见 `GoodsServiceImpl.java:1076`（数据库分页、内存分页均适用）
* **内存分页截取**：`CollUtil.page(page - 1, pageSize, list)`（注意页码从 1 开始，需减 1）

##### 2.2 响应 DTO 结构
分页响应 DTO 必须包含 `Pagination` 字段和列表字段：
```java
@Data
public class V1XxxPageListDTO {
    private Pagination pagination;
    private List<XxxDTO> list;
}
```

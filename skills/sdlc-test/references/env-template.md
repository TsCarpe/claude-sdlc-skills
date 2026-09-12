# 环境配置模板

## sdlc/env/test.md（入库）

```markdown
# test 环境说明

## 访问

- URL：<https://test.xxx.com>
- 登录方式：账号密码直登

## 角色说明

| 角色名 | 说明 | 用例中引用名 |
|---|---|---|
| 平台管理员 | … | 管理员 |
| 业务运营人员 | … | 运营 |

## 前置数据说明

（每类前置数据：构造方式（前端页面哪个角色操作）、依赖、构造一次可复用次数）
例：已上架商品 → 由管理员/运营走创建审核流程构造，一次构造全程可复用。

## 数据核验入口

- MySQL（只读）：库名、核心表清单
- 接口网关/YApi 项目 ID：…
```

## sdlc/env/accounts.local.md（gitignore，本机供给）

```markdown
# 角色 → 账号密码（不入库）

| 角色 | 账号 | 密码 |
|---|---|---|
| 管理员 | … | … |
```

## sdlc/env/repos.local.md（gitignore，本机供给）

```markdown
# 代码仓库本地路径（static 阶段静态检测用，不入库）

| 端 | 路径 | 索引 |
|---|---|---|
| backend | /path/to/<backend-repo> | codegraph ✅ |
| frontend | /path/to/<frontend-repo> | codegraph ✅／无（降级 grep+读文件） |
```

## sdlc/env/ui-recipe.md（环境配方，入库口径同 test.md）

（exec 首跑侦察后按本模板沉淀，跨需求复用；组件库通用交互姿势不在本文件——见 SKILL.md 引用的交互姿势手册 exec-interaction.md，此处只记项目特有内容）

```markdown
# <项目> UI 环境配方

## 环境检查（exec 前置）
- 浏览器/页面存活：chrome-devtools:list_pages
- 登录方式：<SSO 跳转用户辅助登录 / 账密直登，失效表现>
- MySQL 连通：SELECT 1
- 上传目录：<项目根>/.tmp-upload/

## 页面路由清单（侦察时逐页补充）
| 页面 | 路由 | 关键组件/已知交互坑 |
|---|---|---|

## 鉴权直调头（evaluate fetch 接口用）
<例：localStorage['<app>-Authorization'] 取 JSON.parse(...).data，组装 `authorization` / `<app>-token` / `<app>-staff-id` / `<app>-tenant-id` 头——按项目实际字段侦察填写>

## 项目特有坑
| 现象 | 规避做法 |
|---|---|
```

## 纪律

- `accounts.local.md`、`repos.local.md` 必须加入 `.gitignore`（含 `sdlc/env/*.local.md`）
- 前置数据一律通过前端页面构造，禁止直接改库
- ui-recipe.md 只记项目特有内容，通用姿势回写交互姿势手册，不放本文件

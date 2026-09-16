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

## 回归档 Playwright runner（接入 + 标准布局 2026-09-14 试点定型）

runner 基础设施五件从**本 skill 安装目录 `templates/`** 复制到项目（项目级安装 `<项目根>/.claude/skills/sdlc-test/templates/`，全局安装 `~/.claude/skills/sdlc-test/templates/`）：

| 模板 | 复制到 | 占位符/适配点 | 就绪判据 |
|---|---|---|---|
| `runner/package.json` | `sdlc/package.json` | 无（@playwright/test 锁定版本，直接可用） | 在 sdlc/ 根 `npm install` 成功 |
| `runner/playwright.config.ts` | `sdlc/playwright.config.ts` | 1 处：baseURL → test 环境地址 | 与 spike 联合判据（下） |
| `runner/capture-login.mjs` | `sdlc/env/runner/capture-login.mjs` | 3 处：TARGET 默认值 / AUTHED_URL_PREFIX / AUTHED_KEY_RE（鉴权键特征） | `node capture-login.mjs` 弹 Chrome 完成 SSO 后自动落 browser-state.json |
| `runner/spike.spec.ts` | `sdlc/env/runner/spike.spec.ts` | 3 处：`<list-api>` / `/<app>/<目标页路径>` / `<登录后可见按钮文案>` | spike 全绿 = 基础设施就绪 |
| `run_regression.sh` | `sdlc/env/runner/run_regression.sh` | 无占位符（路径硬编码 sdlc/ 布局约定，布局变更需同步改脚本） | `./run_regression.sh` 阶段① 输出「环境就绪」 |

- 配置两件（package.json / playwright.config.ts）必须落 **sdlc 根**，`npm install` 也在 sdlc/ 根执行——模块解析红线（原因见下 tree 注释）
- spike 冒烟（cwd 无关，绝对路径二进制形态）：`<项目根>/sdlc/node_modules/.bin/playwright test --config <项目根>/sdlc/playwright.config.ts spike`
- 一键回归：`sdlc/env/runner/run_regression.sh [<需求名>]`——纯 runner、不回填 cases.md、不占轮次号（报告落 `<日期>-manual` 目录）；登录态失效先 `node capture-login.mjs` 重采
- 项目 `.gitignore` 三条：`sdlc/env/*.local.md`、`sdlc/env/runner/browser-state.json`（含会话凭据）、`sdlc/env/runner/test-results/`
- 首建参考（源项目实测）：channel:'chrome' 走系统 Chrome；若对齐 `~/Library/Caches/ms-playwright` 既有 build 可免 channel，均不可行才 `npx playwright install chromium`

标准布局（tree 注释即红线依据）：

```text
sdlc/
├── package.json          # @playwright/test（版本锁定）——必须在 sdlc 根
├── playwright.config.ts  # testDir:'.'、channel:'chrome'（系统 Chrome 零下载）、workers:1、storageState/outputDir 以 __dirname 绝对化
├── node_modules/         # 依赖必须装 sdlc 根：装在 env/runner/ 子目录时 specs 模块解析会命中项目根另一份库 → 双树冲突
└── env/runner/
    ├── capture-login.mjs     # 登录态采集：node capture-login.mjs —— 弹 Chrome 用户辅助登录，自动检测鉴权键并保存（勿用 codegen）
    ├── browser-state.json    # 登录态（含会话凭据，.gitignore 强制；失效表现=runner 重定向「欢迎登录」）
    ├── spike.spec.ts         # runner 健康检查（登录态+环境连通）
    └── test-results/         # 失败留痕（error-context.md 含 ARIA 快照 / trace.zip / 截图）
```

- 调用（cwd 无关，绝对路径二进制形态）：`<项目根>/sdlc/node_modules/.bin/playwright test --config <项目根>/sdlc/playwright.config.ts <需求名>`
- 详见 skill `references/spec/spec-guide.md`（含 EP spec 姿势表）

## sdlc/env/ui-recipe.md（环境配方，入库口径同 test.md）

（exec 首跑侦察后按本模板沉淀，跨需求复用；组件库通用交互姿势不在本文件——见 SKILL.md 引用的交互姿势手册 references/exec/exec-interaction.md，此处只记项目特有内容）

```markdown
# <项目> UI 环境配方

## 环境检查（exec 前置）
（每条附「→ 恢复：」失败恢复动作，无法自愈的写「报用户」）
- 浏览器/页面存活：chrome-devtools:list_pages → 恢复：<…>
- 登录方式：<SSO 跳转用户辅助登录 / 账密直登，失效表现> → 恢复：<…>
- MySQL 连通：SELECT 1 → 恢复：<…>
- 上传目录：<项目根>/.tmp-upload/ → 恢复：<…>

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

- `accounts.local.md`、`repos.local.md` 必须加入 `.gitignore`（含 `sdlc/env/*.local.md`）；`runner/browser-state.json` 含会话凭据同样必须 gitignore
- 前置数据：探索档通过前端页面构造；spec 档允许 API 直调（走后端完整校验）；**任何档禁止直接改库**
- ui-recipe.md 只记项目特有内容，通用姿势回写交互姿势手册，不放本文件

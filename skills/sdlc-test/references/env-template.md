# 环境配置模板

## 目录

> 本目录是 env-template.md 自身的导航（本文 >100 行，供部分读取时预览范围），非产物内容；按模板创建的 sdlc/env/ 各文件不复制此目录。

- [sdlc/env/test.md（入库）](#sdlcenvtestmd入库)
- [sdlc/env/accounts.local.md（gitignore，本机供给）](#sdlcenvaccountslocalmdgitignore本机供给)
- [sdlc/env/repos.local.md（gitignore，本机供给）](#sdlcenvreposlocalmdgitignore本机供给)
- [sdlc/env/dev.md（开发验证档，入库）](#开发验证档sdlcenvdevmd入库)
- [sdlc/env/dev-auth.local.md（gitignore，本机供给）](#sdlcenvdev-authlocalmdgitignore本机供给)
- [回归档 Playwright runner 接入](#回归档-playwright-runner接入--标准布局-2026-09-14-试点定型)
- [sdlc/env/ui-recipe.md（环境配方）](#sdlcenvui-recipemd环境配方入库口径同-testmd)

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

## 开发验证档（sdlc/env/dev.md，入库）

开发完成验证（`/sdlc-test dev` → `scripts/verify_dev.py`）的项目级配置——五节结构固定，键名勿改（脚本按「节/键」解析）。

```markdown
# 开发验证环境配置

## 模式
- 启动模式: local

## 构建
- 命令: mvn clean package -DskipTests
- 超时秒: 600

## 启动
- 命令: java -jar <module>/target/app.jar --spring.profiles.active=dev
- 健康探测: http://127.0.0.1:8080/actuator/health
- 最大等待秒: 120

## 冒烟
- base URL: http://127.0.0.1:8080
- 鉴权: 免鉴权

## 回归
- 命令: mvn test -pl <module>
- 超时秒: 600
```

| 项 | 说明 |
|---|---|
| 启动模式 | `local`＝验证器本地起服务并负责停止（启动命令勿自行 nohup/disown 后台化）；`unmanaged`＝服务由外部供给（用户手起/IDE/远程 dev 环境），验证器跳过起停、只做健康探测+冒烟+回归——本地起不了服务时的一等公民路径，仍是机器验证而非人工声明 |
| 构建命令 | 前后端双仓写单条复合命令（`cd <前端仓库> && npm run build && cd <后端仓库> && mvn package`） |
| 健康探测 | 就绪判据 = HTTP 2xx；单次 5s 超时、间隔 2s 轮询至「最大等待秒」 |
| 回归命令 | A/B 级必填，**须为真实测试套件入口**（单测 / 既有 runner）；占位命令（如 echo）＝空转，判负 |
| 冒烟鉴权 | `免鉴权` 或 `dev-auth.local.md`（需鉴权时头值从该文件读取，真值不入库） |
| 超时覆盖 | 默认构建/回归 600s、启动等待 120s，可在对应节用「超时秒 / 最大等待秒」覆盖 |

## sdlc/env/dev-auth.local.md（gitignore，本机供给）

冒烟需鉴权时（dev.md「冒烟/鉴权」= dev-auth.local.md）的本机头值供给，逐行「头名: 值」：

```markdown
# 冒烟鉴权头（不入库）
authorization: Bearer <本机供给>
<x-app>-token: <本机供给>
```

依赖项目 `.gitignore` 含 `sdlc/env/*.local.md`（与 accounts/repos.local 同一条，缺失先补）。

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
- 冒烟鉴权真值只进 `dev-auth.local.md`——`dev.md` 与冒烟清单 `smoke.md` 禁写鉴权真值与内网域名
- 开发完成验证留档（`dev/verify-*.md`）正文含命令输出尾部与响应片段，对外分享前脱敏（去手机号/token 类字段）
- 前置数据：探索档通过前端页面构造；spec 档允许 API 直调（走后端完整校验）；**任何档禁止直接改库**
- ui-recipe.md 只记项目特有内容，通用姿势回写交互姿势手册，不放本文件

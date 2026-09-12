# 交互姿势手册（exec 阶段浏览器/数据库操作）

> 组件库通用交互姿势，跨项目共享。项目特有细节（登录/路由/鉴权头）在 `sdlc/env/ui-recipe.md`。条目按「现象→做法」书写，附实测锚点。

## 总则

- 优先 take_snapshot 拿 uid 直接交互；浮层类组件快照失明时降级 evaluate_script 执行真实 DOM click（走组件事件系统，不算绕过校验）
- **evaluate_script 一律同步执行、立即返回**：禁止 Promise/setTimeout 等待链（浮层关闭导致死等，MCP 120s 挂起）。需要等待用 `chrome-devtools:wait_for`
- 侦察先行：进入新页面类型先 snapshot + 一次 evaluate 摸清表单组件清单（控件类型/浮层结构/file input/富文本），再开始操作

## Element Plus 姿势表（2026-09 真实项目实测）

| 控件 | 现象 | 做法 |
|---|---|---|
| el-select 单选 | 选项渲染在 teleport popper，take_snapshot 无选项 uid | click 输入框 → evaluate 同步执行：`document.querySelectorAll('.el-select-dropdown__item')` 过滤 `offsetParent !== null` 后按文本匹配 `.click()` |
| el-date-picker | `fill` 只写 input.value 不触发解析（blur 后值丢失） | evaluate `focus()+select()` → type_text `yyyy-MM-dd` + Enter → evaluate 复核 input.value |
| el-select 多选（远程搜索） | 同单选失明；selected class 点击后不更新；过滤词变更可能清空已选；同步连点两目标会因引用 detach 只生效一个 | evaluate 逐个点：**每次点击前重新查询可见选项+按文本去重**（点过不再点），点后以「已选 N 人」计数核对递增，不足换下一个目标；搜索框残留过滤词用 `InputEvent('input',{inputType:'deleteContentBackward'})` 清空并等 ~1s 远程刷新（2026-09-12 补充实测） |
| el-upload | upload_file 拒绝 workspace root 外路径（如 /tmp） | 上传文件预置 `<项目根>/.tmp-upload/` 后再 upload_file |
| 富文本 contenteditable | 快照仅见 generic 容器无输入框 | click 容器 → type_text |

## MySQL 断言规范

- bigint 主键经 JSON 往返会舍入（…848 → …800）：**禁止**用接口返回的数字 ID 直接回查——一律用业务键（name 等唯一字段）子查询定位，如 `WHERE relation_id = (SELECT activity_id FROM activity WHERE name='xx')`
- 表名/列名以本轮 static.md 记录为准，不现场猜测（猜错一次浪费一轮 SHOW COLUMNS）
- 多表 COUNT 断言聚合成一条 SQL，减少往返

## 证据采集

- 判定证据三连在同一条消息并行发出：take_screenshot + list_network_requests + list_console_messages

## 失败归因

姿势失效时按三类归因，每类一行判定线索：

- **组件库升级**（同控件现象全项目复现、官方 changelog 有对应变更）→ 本表条目移入「旧模式」段并重测新姿势
- **项目二次封装**（仅单项目失效，DOM 结构与原生组件不同）→ 记入该项目 `sdlc/env/ui-recipe.md` 坑表
- **姿势过期**（现象描述与实测不符，无法归类上两类）→ 直接更新本表条目

## 维护

- 新控件姿势 ≤3 次试错后回写本表，注明组件库 + 实测日期；组件库升级后失效条目移入下方「旧模式」段而非删除

## 旧模式

（暂无）

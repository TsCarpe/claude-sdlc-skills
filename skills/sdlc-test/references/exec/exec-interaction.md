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
| el-date-picker 非法值拒绝判定 | 已有合法值时键入违反 disabledDate 的日期（含面板禁选日），框内短暂显示原始连字符文本（未格式化 yyyy/MM/dd=解析失败特征），blur 后回退旧值、下一步照常放行（模型未变）——**「文本进框但模型回退」=组件在输入层整体拒绝，不是「可输入待校验」**（2026-09-15 实测：比赛时间链相邻相等场景，面板 td.disabled + 键入回退双保险） | 拦截类用例判定口径：非法状态不可构造时按「天然满足」处理并留档，勿反复重试键入 |
| el-select 多选（远程搜索） | 同单选失明；selected class 点击后不更新；过滤词变更可能清空已选；同步连点两目标会因引用 detach 只生效一个 | evaluate 逐个点：**每次点击前重新查询可见选项+按文本去重**（点过不再点），点后以「已选 N 人」计数核对递增，不足换下一个目标；**计数核对可能滞后——点后必读已选 tags 明细逐项核对，点前待一拍等过滤刷新完成再点**（2026-09-15 补充实测：参与学校多选 3 连点仅落 1 次+点错目标各 1 次）；搜索框残留过滤词用 `InputEvent('input',{inputType:'deleteContentBackward'})` 清空并等 ~1s 远程刷新（2026-09-12 补充实测） |
| el-upload | upload_file 拒绝 workspace root 外路径（如 /tmp） | 上传文件预置 `<项目根>/.tmp-upload/` 后再 upload_file |
| 富文本 contenteditable | 快照仅见 generic 容器无输入框 | click 容器 → type_text |

## MySQL 断言规范

- bigint 主键经 JSON 往返会舍入（…848 → …800）：**禁止**用接口返回的数字 ID 直接回查——一律用业务键（name 等唯一字段）子查询定位，如 `WHERE relation_id = (SELECT activity_id FROM activity WHERE name='xx')`
- 表名/列名以本轮 static.md 记录为准，不现场猜测（猜错一次浪费一轮 SHOW COLUMNS）
- 多表 COUNT 断言聚合成一条 SQL，减少往返

## 证据采集

- 判定证据三连在同一条消息并行发出：take_screenshot + get/list_network_requests + list_console_messages
- **接口响应定向获取**：已知目标请求 URL 时直接 `get_network_request` 按 URL/请求 ID 取响应；`list_network_requests` 仅在定位不到目标请求时使用（全量列表是 token 大头）
- **截图先落盘后查看**：take_screenshot 落本轮 screenshots/ 即算采集完成；仅展示类断言或异常疑点时 Read 查看，其余情况不以图片进上下文为默认

## 表单推进与静默拦截排障（2026-09-13 R2 沉淀）

点「下一步/提交」无反应时按以下顺序排查（按命中率排序，禁止跳步乱猜）：

1. **空必填项优先**：静默拦截的第一大原因是隐藏的空必填（如奖项名额默认空、介绍未填）——表单对空必填可能**不显示任何错误提示**、按钮也不报错。逐项读输入值与计数器（`0/100` 类），空值补齐后重试
2. **toast 抓取**：提示文案是瞬态（~1.5s 消失），动作前先挂 MutationObserver 缓冲（evaluate_script 同步执行），动作+等待后立即读取：
   ```js
   // 挂（动作前）
   window.__toasts=[];const o=new MutationObserver(()=>{[...document.querySelectorAll('.el-message__content')].forEach(m=>{if(!window.__toasts.includes(m.textContent.trim()))window.__toasts.push(m.textContent.trim())})});o.observe(document.body,{childList:true,subtree:true});window.__obs=o;
   // 读（动作后，读完断开）
   window.__obs.disconnect();JSON.stringify(window.__toasts)
   ```
   表单行内错误用 `.el-form-item__error` 查（常驻不消失，可直接读）
3. **网络层**：确认校验/保存请求是否真的发出、请求体是否符合预期（`get_network_request` 按 URL 定向）

配套纪律——**步骤推进「动作+验证」配对**：点下一步后立即验证当前步骤（步骤标题/区块特征文本，如"审核步骤/评分标准"），验证不过先原地排查，不带病前进（否则后续断言全部作废）。注意步骤标题的匹配文本要从快照取实词，不要凭用例措辞猜（如步骤二标题是"比赛介绍"还是"介绍内容"以页面为准）。

## 失败归因

姿势失效时按三类归因，每类一行判定线索：

- **组件库升级**（同控件现象全项目复现、官方 changelog 有对应变更）→ 本表条目移入「旧模式」段并重测新姿势
- **项目二次封装**（仅单项目失效，DOM 结构与原生组件不同）→ 记入该项目 `sdlc/env/ui-recipe.md` 坑表
- **姿势过期**（现象描述与实测不符，无法归类上两类）→ 直接更新本表条目

## 维护

- 新控件姿势 ≤3 次试错后回写本表，注明组件库 + 实测日期；组件库升级后失效条目移入下方「旧模式」段而非删除

## 旧模式

（暂无）

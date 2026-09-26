# PoC：jev-ultrafast 接入 sdlc-test exec 阶段的可行性评估

> 一次性评估目录，**不是 skill，不注册 marketplace**。评估出结论后本目录归档，结论回写 `docs/`。

## 决策问题

[jev-ultrafast](https://github.com/browser-use/jev-ultrafast)（browser-use 家族的目标驱动浏览器 agent，元素表 + 小模型决策，单任务秒级）是否值得作为 `sdlc-test exec` 阶段的**首轮执行降本通道**接入：

```
用例（步骤+预期） → 编译为 goal(操作段) + verify(断言段) → jev 执行 → 通过则照旧 spec 资产化
                                                  ↘ BLOCKED/超时/DOM盲区 → fallback 现有 agent 驱动路径
```

spec 资产化路线（Playwright 回归零 token）不变；jev 只加速首轮。**任一判定标准不过 → 不接入**，不引入 TypeSafe 依赖。

## 两阶段评估

| 阶段 | 脚本 | 需要 API key | 回答的问题 |
|---|---|---|---|
| A 静态 DOM 覆盖 | `check_dom.py` | 否（只要 Chrome + browser-harness） | jev 的元素表能收录目标页面多少可见可交互控件 |
| B 动态任务走通 | `run_tasks.py` | 是（TypeSafe + 文本模型） | 真实用例能走通多少、误判多少、多快 |

先跑 A：A 不过连 key 都不用申请。

## 指标定义

| 指标 | 定义 | 来源 |
|---|---|---|
| DOM 覆盖率 | jev 元素表收录数 / 独立控件普查数（分类近似口径） | `check_dom.py` |
| 真通过率 | `done 且 verify 通过` 的任务数 / 总任务数 | `run_tasks.py` |
| 误判率 | `done 但 verify 不通过` 的任务数 / done 总数 | `run_tasks.py` |
| 平均耗时 | 各任务 `elapsed_ms` 均值 | state.json |
| fallback 率 | 1 − 真通过率 | 推导 |

> 覆盖率为计数近似（jev 按 DOM 节点去重，普查按选择器计数）；精确差集靠脚本输出的两侧 label 清单人工/模型目检。

## 判定标准（阈值定死，脚本程序化执行）

**阶段 A（静态）**

| 编号 | 标准 | 阈值 |
|---|---|---|
| S1 | 总体 DOM 覆盖率 | ≥ 80% |
| S2 | 关键控件类（select / textbox）| 无整类归零 |
| S3 | 日期类（input[type=date] 等）覆盖情况 | 人工确认（jev 对日期控件的处理方式本身是观察点）|

**阶段 B（动态，任务数 ≥ 10 才判定，不足只出参考值）**

| 编号 | 标准 | 阈值 |
|---|---|---|
| D1 | 真通过率 | ≥ 60% |
| D2 | 误判率 | ≤ 10%（静默假阳性最危险，单独设卡） |
| D3 | 平均耗时 | ≤ 30s / 任务 |

**S1、S2、D1、D2 任一不满足 → 不接入。**

## 准备与运行

```bash
# 0) clone jev-ultrafast 并装依赖（Python ≥3.12，uv）
git clone https://github.com/browser-use/jev-ultrafast.git ~/tmp/jev-ultrafast
cd ~/tmp/jev-ultrafast && uv sync
cp .env.example .env   # 填 TYPESAFE_API_KEY / TEXT_MODEL_API_KEY（阶段 B 才需要）
uv run browser-harness --doctor   # 确认本机 Chrome 远程调试连通

# 1) 阶段 A：静态覆盖率（可批量查多个页面）
cd ~/tmp/jev-ultrafast
uv run --env-file .env python /path/to/this/poc/check_dom.py \
  --url 'https://<test环境页面>' --wait 3 --out artifacts/dom

# 2) 阶段 B：复制任务清单模板，填真实 test 环境 URL 与预期（本地文件，不进 git）
cp tasks_example.py tasks_local.py   # 编辑后
uv run --env-file .env python /path/to/this/poc/run_tasks.py --tasks tasks_local --out artifacts/run
```

任务清单是 Python 模块（`TASKS` 列表），每项含 `id / url / goals / verify(page) / tags`；`verify` 负责独立断言终态——**jev 的 DONE 不可信**（官方示例同款姿势），预期结果必须编译成代码。

## 任务集设计要求（阶段 B）

≥10 个任务，覆盖以下控件/场景矩阵（对照中后台盲区）：

| 类别 | 至少覆盖 | 备注 |
|---|---|---|
| 导航 | 菜单进入指定页面 | 基线 |
| 文本表单 | 必填文本、搜索框 | fill 通道 |
| 下拉 | native select **和** 组件库自定义 Select | jev 明说只保证 native |
| 日期 | DatePicker（组件库） | 已知盲区，重点观察 |
| 列表 | 筛选 + 分页 + 查看详情 | |
| 提交反馈 | 新建/编辑提交后 toast/消息断言 | 验证 verify 通道 |

## 结论记录表（跑完填写）

| 日期 | 目标系统/页面 | 任务数 | S1 | S2/S3 | D1 | D2 | D3 | 结论 | 备注 |
|---|---|---|---|---|---|---|---|---|---|
| 2026-09-20 | 评选活动管理后台（本地 test，列表页+创建表单页） | — | 100% PASS | 关键类无归零；组件库 DatePicker 以 fill+Open click 双通道收录 | — | — | — | 阶段 A 通过 | ①视口必须自适应：系统需 1280 宽，jev 硬编码 1120 会裁掉右侧操作列 ②Element UI 全量采集 OK，含图标按钮 |
| 2026-09-20 | 同上（12 条改编自真实用例的页面层任务） | 12 | — | — | 66.7% PASS | 原始 11.1% / 加置信门槛后 0% | 6.5s PASS | 阶段 B 有条件通过 | 盲区规则化可预测；详见下方阶段 B 发现 |

### 阶段 A 补充发现（2026-09-20）

1. **视口适配是接入必办项**：jev `browser.py` 硬编码 `1120×780`，宽版中后台（内容宽 ~1280）的右侧操作列（创建/详情/分页）会整体落在视口外导致漏采。`check_dom.py` 已内置自适应（observe 前按 `scrollWidth` 调宽）；接入 sdlc-test 时需改 jev 源码一行或在外层做同样适配。
2. **jev 采集比朴素语义普查更严谨/更全**：会正确过滤 disabled 按钮、忽略横向越界元素，并额外收录纯图标按钮（如搜索展开钮，朴素 text 选择器会漏）。
3. **组件库日期控件**：Element UI DatePicker（`年/月/日 时:分:秒`）静态识别为 `fill 输入框 + Open 展开按钮`双通道；本系统无原生 `input[type=date]`，S3 的原生 date 观察点不适用。弹层面板内的实际选取（含时间子面板/确认按钮）是否可走通留给阶段 B。

### 阶段 B 发现（2026-09-20，12 条任务，改编自真实用例的页面层子集）

**逐条结果**：导航/取消返回/必填阻断/文本输入/搜索命中/搜索空态/分页/菜单切换 8 条 `done_verified`；组件库下拉、日期面板选取、图标返回按钮 3 条 `blocked`；1 条低置信 DONE 被 verify 正确拦截。另有 1 条网络抖动 error（复跑通过，按通过计），1 条日期 fill 复测因 TypeSafe 限流未完成（待配额窗口恢复后补测，见下）。

1. **盲区是规则化的、可静态预判的，不是随机失败**：
   - 组件库 Select 弹层选项无 `role` 属性 → 选项不进元素表 → 必 blocked（官方 limitation 预告的 native-only 下拉，在中后台组件库上坐实）
   - DatePicker 日历面板可见（面板 tab「选择日期/选择时间」能被识别）但日期格子无 role → 选不了具体日期
   - 详情页图标型「返回」按钮（无文字无 role）不可见
   - **接入含义**：任务编译时可先扫目标页元素表，含无 role 弹层控件的任务直接分诊到 fallback 通道，不必试跑
2. **决策模型的置信度可用作误判防线**：唯一的假 DONE 置信度仅 0.34，两个真实盲区 BLOCKED 置信 0.98/0.39。建议接入规则：`DONE 且 confidence < 0.5 → 转 fallback`，可将 D2 从 11.1% 压到 0（本组合此轮实测）。
3. **verify 拦截有效**：低置信 DONE 被页面层断言拦下记 `done_unverified`，未漏过——「用例预期编译成 verify」的架构方向得到验证。
4. **速度**：均 6.5s/任务（含模型往返），远优于 D3 阈值；与 agent 驱动（分钟级）是量级差。
5. **TypeSafe 限流是运维约束**：连续 13 任务后触发 429，冷却 >3 分钟未恢复（窗口长度未探明）。接入需配额规划 + 任务间 pacing/重试退避。
6. **待复测**：`create-date-fill`（日期不走面板、直接 fill 输入文本）因限流未跑；若可行则日期盲区可绕（该系统 Picker 对键盘输入有校验回退，预期不容乐观）。

**阶段 B 总判定：有条件通过**——D1 66.7%（≥60%）、D3 6.5s（≤30s）达标；D2 原始 11.1% 略超 10%，但置信门槛规则可消除（0%）。结合盲区可预判、verify 拦截有效，**建议接入为 exec 双通道（jev 主跑 + agent fallback + 置信/盲区分诊）**，不建议单通道替代。

## 已知风险（评估时留意）

- TypeSafe API key 为硬依赖（决策模型无替代；文本模型可换 GLM/DeepSeek，OpenAI-compatible 端点）
- jev 共享本机 Chrome profile：test 环境登录态方便，但用例间状态污染需人工清理
- jev 自身标注 MVP：shadow DOM / iframe / canvas / 上传 / 键盘控件不在支持范围
- `MAX_STEPS` 步数预算有限，长链路用例可能被截断（计入 blocked）

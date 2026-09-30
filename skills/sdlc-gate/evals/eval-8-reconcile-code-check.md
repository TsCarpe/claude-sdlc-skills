# eval-8：RECONCILE 代码核对（定向只读 + 三向落点 + 触发边界 + 分歧例外）

```json
{
  "skills": ["sdlc-gate"],
  "query": "<需求名> 四个子代理预审都回传了，开始 RECONCILE 和汇总 issues 文件",
  "files": [
    "sdlc/<需求名>/intake/ 三件套（digest §7 规则含 FR-08 驳回理由必填；audit、pm-checklist——全文无 WorkQueryRepository、无 activity_work 软删列、无定时清理任务、无列表排序口径的任何信息）",
    "sdlc/<需求名>/design/design.md（§3.2 作品列表按创建时间倒序分页；§4 公共资产：作品列表查询复用现有 WorkQueryRepository 并依赖其分页；§2.4 下架对账沿用 activity_work 表 soft_delete 标记；§5 对账兜底疑似依赖定时清理任务）",
    "sdlc/<需求名>/test/cases.md（TC-12 断言：提交成功后列表新记录置顶展示）",
    "预审回传五条候选：架构 A-11「设计称复用 WorkQueryRepository 做作品列表查询，该组件是否存在、是否带分页未验证——公共资产断言悬空」＋数据 S-12「activity_work.soft_delete 列是否存在未验证，下架对账口径悬空」＋可测性 T-15「驳回理由必填口径疑似与规则清单冲突」＋架构 A-13「对账兜底依赖的定时清理任务是否存在未验证」＋交叉分歧 D-03「设计 §3.2 写列表按创建时间倒序，用例.TC-12 断言新记录置顶——两边口径不一致，存量排序行为无从判断」",
    "代码侧（codegraph 索引在、mysql MCP 在）：WorkQueryRepository.java:47 findByEntrantId 已带分页参数（A-11 涉及的设计断言成立）；WorkQueryRepository.java:31 列表当前按创建时间倒序（D-03 涉及的存量排序行为）；库表 activity_work 实体 ActivityWorkDO.java 全字段无 soft_delete（仅 status 硬状态）；A-13 点名的定时清理任务类检索未命中"
  ],
  "expected_behavior": [
    "A-11/S-12/A-13 判定为 CONTRACT 仲裁不了（三件套无对应信息），触发代码核对：只读定向检索条目点名的 WorkQueryRepository / activity_work 表结构 / 定时清理任务（codegraph 可用走 codegraph:codegraph_explore，缺失降级定向 grep+读文件；表结构可用 mysql:mysql_query 只读核对），不做开放探索",
    "A-11 坐实契约误读（上游代码已带分页，审查者缺的上下文在代码里）→ 不进清单、不进备案区、零留痕（与契约误读同处置）",
    "S-12 坐实问题真实（实体无软删字段，设计口径悬空坐实）→ 进清单：摘引列照引 design §2.4 原句（hard），代码定位 ActivityWorkDO.java 作问题列证据附注；hard/soft 不因代码证据改变",
    "T-15 CONTRACT 可直接仲裁（digest §7 FR-08 驳回理由必填且设计一致）→ 直接判契约误读不进清单，不发起任何代码检索",
    "A-13 定位不到 → 仍按四分类归类（如 有效可行动·soft，写一句依据链），issues 头「证据降级」行点名条目编号注明（如：代码核对定位不到 A-13）",
    "D-03 分歧条目不被代码核对消解：仍进分歧清单交人裁决（按三类口径不一致建议升级用户），分歧点/后果列附代码定位（WorkQueryRepository.java:31——存量按创建时间倒序）作裁决证据，不适用坐实误读零留痕落点",
    "其余流程不受影响：同根因合并、issues 模板、check_trace 机械校验照常执行"
  ],
  "red_lines": [
    "该核对未核对：对 CONTRACT 仲裁不了的候选（A-11/S-12/A-13）未做定向代码/表结构核对就直接拍四分类",
    "乱核对：对 CONTRACT 可仲裁的 T-15 发起代码检索，或检索范围越出条目点名对象（通读模块/全库扫描等开放探索）",
    "坐实误读的 A-11 进清单或备案区（应零留痕）；代码定位改写 hard/soft 判定（如缺失型条目因代码坐实升 hard）",
    "分歧条目 D-03 被代码核对零留痕消解——分歧必须人裁决，代码只作裁决证据"
  ]
}
```

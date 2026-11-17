# flow-viz 图协议（仓库级共享规范）

> 产物 markdown 中流程图/状态机的统一表达载体。消费方是 SDLC 平台 web 端的通用图渲染器
> （Vue Flow + ELK 自动布局，HTML 节点卡）。任何 skill 产物需要画业务流程图或状态机图时
> 引用本协议，不另造格式。协议契约只描述现行行为；格式演进历史归各仓 CHANGELOG。

## 载体

markdown fenced 代码块，语言标记 `flow-viz`，内容为单个 JSON 对象（完整合法示例见下两节）。
每张图**必须带图题行**（加粗独立行，置于块上方），图题规范由引用方（如 digest-template.md）
约定，形如 `**图 N：<图题>**`。

JSON 纪律：键名固定小写驼峰、**禁止注释与尾逗号**、字符串一律双引号（中文内容直接写，
无需转义处理）；块内 JSON 不合法时平台按原始代码块降级展示并提示——生成后必须机检
（仓根 `scripts/check_flowviz.py`）。

## kind=flow（业务流程图，泳道可选）

```flow-viz
{
  "kind": "flow",
  "dir": "TD",
  "lanes": [{ "id": "L1", "label": "角色A·场景" }, { "id": "L2", "label": "角色B·场景" }],
  "nodes": [
    { "id": "A1", "lane": "L1", "type": "step", "no": 1, "label": "操作1", "src": "详述1·1" },
    { "id": "A2", "lane": "L1", "type": "decision", "no": 2, "label": "是否具备权限" },
    { "id": "A2X", "lane": "L1", "type": "end", "label": "无入口提示", "gap": true,
      "note": "原文未给其他入口", "src": "详述1·1", "pids": ["P12"] },
    { "id": "B1", "lane": "L2", "type": "step", "no": 3, "label": "审核", "src": "详述2·1" },
    { "id": "C1", "lane": "L2", "type": "end", "no": 4, "label": "归档完成", "src": "详述2·2" }
  ],
  "edges": [
    { "from": "A1", "to": "A2" },
    { "from": "A2", "to": "A2X", "label": "否" },
    { "from": "A2", "to": "B1", "label": "是" },
    { "from": "B1", "to": "C1", "dashed": true }
  ]
}
```

- `lanes`：泳道（角色/系统分区），`id` 唯一、`label` 为泳道标题。**页面级操作流程（表单/
  向导步骤）不设泳道**：省略 `lanes` 且节点不带 `lane` 字段
- `dir`：`TD`（自上而下，缺省）/ `LR`（自左向右，横向主链长流程用）
- 节点 `type`：`step`（缺省，普通步骤）/ `decision`（判定分支）/ `end`（终止/出口）
- 节点字段：`no` 步骤序号（主链 1 起连续）、`label` 节点文本（短句，细则写 note 或表）、
  `src` 出处（条款级出处列口径同表格）、`gap:true` 原文未定义断点（渲染为 ❓ 虚线卡）、
  `note` 附注便签、`pids` 关联澄清题编号（仅 digest 场景使用）
- 边字段：`label` 分支条件（是/否、成功/失败等）、`dashed:true` 依赖/弱关联虚线
- 宽容规则（消费端）：未知字段忽略；重复 id、悬空边（端点不在 nodes）、自环边丢弃并提示

## kind=state（状态机图）

```flow-viz
{
  "kind": "state",
  "nodes": [
    { "id": "s0", "type": "start" },
    { "id": "s1", "type": "state", "label": "待审核", "src": "详述2·1",
      "note": "状态展示类说明（非流转）写这里" },
    { "id": "s2", "type": "state", "label": "已通过", "src": "详述2·2" },
    { "id": "sT", "type": "state", "label": "超时态未定义", "gap": true, "src": "详述2·3" }
  ],
  "edges": [
    { "from": "s0", "to": "s1", "label": "提交（原文未定义入口 ❓）" },
    { "from": "s1", "to": "s2", "label": "审核通过" },
    { "from": "s1", "to": "sT", "label": "超时" }
  ]
}
```

- 入口用 `type:"start"` 节点表达（无 label 时渲染「开始」）；原文未定义入口时 start 首边
  label 带 ❓ 说明，不得从中间态起笔
- **自环不表达**：协议与渲染器均不支持 `A→A`；原文明说的自迁移（重试/重新提交类）在
  相关状态节点的 `note` 中说明；「显示××」「按钮置灰」「文案××」是状态展示不是流转，
  同样写 `note` 或图后边表
- 未定义的状态/流转：`gap:true` 入图（❓ 标记）并在图后边表以 `?` 行双呈现
- 每条流转边须能在原文找到出处（`src` 字段或图后边表出处列）

## 机检

仓根 `scripts/check_flowviz.py`：对产物 markdown 的全部 ```flow-viz 块校验 JSON 可解析、
kind 合法、id 唯一、边端点存在、lane 引用存在、无自环。exit 非 0 时 stderr 带块位置与
修复建议，处置后重跑至通过。

<!-- 以下 fv-mirror 标记段是 sdlc-platform-server agent/prompts.py 速查卡的镜像引用段：
     两处内容必须逐字节同步，scripts/check_digest_mirror.py 逐字节比对（改任何一侧必须同步另一侧）。 -->
<!-- fv-mirror-start -->
5 业务主流程 flow-viz JSON 图（fenced 块语言标 flow-viz；泳道图 kind:"flow"+lanes[{id,label}]，节点带 lane 归属、type step/decision/end、no 主链序号、src 条款级出处、gap:true=原文断点❓、note 附注、边 label 分支条件/dashed 虚线依赖；页面级流程省略 lanes 不泳道化；长主链可 dir:"LR"；图题行加粗置于块上方：图 1：<流程名>（主流程，跨角色泳道），页面级流程续编号）｜
6 状态机(每个带状态对象一张 kind:"state" JSON 图+流转边表；入口 type:"start" 节点，原文未定义入口时首边 label 带 ❓；自环不表达——原文自迁移/状态展示类写节点 note 或图后表；未定义流转 gap:true 入图并在边表以?行双呈现；图题固定 图 N：<对象名> 状态机——对象名是 states.obj 的唯一载体；边表：从|触发|至|出处)｜
flow-viz JSON 纪律（§5/§6 全部图，落盘前逐块复读，违反即返工）：单一 JSON 对象、键名固定、禁止注释与尾逗号、字符串双引号内中文直接写；id 全图唯一、边 from/to 必须指向已声明节点、无自环；节点 label 写短句（细则写 note 或图后表）、断点一律 gap:true（不手打 ❓ 进 label）；块过不了仓根 scripts/check_flowviz.py 机检即返工重写。
<!-- fv-mirror-end -->

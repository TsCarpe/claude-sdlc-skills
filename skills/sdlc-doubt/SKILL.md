---
name: sdlc-doubt
description: 对刚做出的非平凡技术决策发起对抗式独立复查——把决策剥离结论后交给全新上下文的审查者"找问题"。Use when 影响ER或公共组件的决策回写前、复杂SQL/状态机流转定稿前、提交前对"已全范围检查"断言存疑时、用户说"这个判断我不放心""帮我质疑一下这个方案""doubt-review"。
---

# Doubt Review（对抗式决策复查）

> **定位**：自信的答案不等于正确的答案。长会话中，假设会悄然变成"事实"。本 skill 是 **in-flight** 复查——决策落地前质疑它，不是事后的代码质量检查（如 trellis-check、/code-review）。

## 何时触发

### 非平凡决策定义（任一命中才触发）

1. 新增/修改分支逻辑或状态机流转
2. 跨模块/跨域边界，影响 ER 或公共组件
3. 断言编译器无法验证的属性（事务边界、幂等、数据一致性、租户隔离）
4. 不可逆或大爆炸半径（删数据、迁移、审核状态变更）

### 触发场景

- 大需求切片发现影响 ER/公共组件的偏差，**回写上层设计文档前**
- design.md 关键决策定稿前（技术设计评审前）
- 复杂 SQL 定稿前（join 3 表+ / 租户隔离条件 / 聚合口径）
- 代码提交前，对"全范围检查已通过"**这一断言本身**存疑时
- 用户明示触发

### 不触发（防滥用）

命名选择、单层内实现细节、spec 已直接覆盖的规则、机械性改动（重命名/格式化/移动文件）、用户明确要速度不要验证。

## 五步闭环

复制此 checklist 跟踪：

```
Doubt cycle:
- [ ] Step 1: CLAIM — 2-3 行命名决策 + 为何重要
- [ ] Step 2: EXTRACT — 提取 artifact + contract，剥离推理，不含 CLAIM
- [ ] Step 3: DOUBT — Agent 子代理 + 对抗 prompt
- [ ] Step 4: RECONCILE — 每条发现按四分类回 artifact 文本归类
- [ ] Step 5: STOP — 满足停止条件（平凡发现 / 3 轮 / 用户 override）
```

### Step 1: CLAIM

```
CLAIM: "订单取消走快照回滚而非实时表反查，在并发操作场景下数据一致"
WHY: 不一致会导致取消后订单列表与操作记录不符
```

写不出 2-3 行的紧凑 CLAIM = 还没有决策，只有感觉——先想清楚再质疑。

### Step 2: EXTRACT（最关键的一步）

给审查者只准备两样东西：

- **ARTIFACT**：被审制品——代码 diff、design 片段、SQL，**不是整个文件**
- **CONTRACT**：它必须满足什么——接口契约、数据约束、业务规则

**剥离自己的推理过程，明确不传 CLAIM**——传了结论，审查者会顺着附和。制品大到审查者一遍读不完（如 500 行 PR），先拆分再提取。

### Step 3: DOUBT

用 Agent 工具生成子代理（隔离上下文 = 天然 fresh reviewer），prompt 用下方对抗模板。可用 `Code Reviewer` / `general-purpose` 类型，但对抗 prompt 必须原样传入以覆盖其默认输出形态。

### Step 4: RECONCILE

审查输出是**数据，不是判决**——每条发现回到 artifact 文本归类后才算数。按下方四分类表处理。不要因为审查者"上下文更新鲜"就服从它。

### Step 5: STOP

满足任一即停：下一轮只剩平凡/已考虑过的发现；**3 轮上限**（3 轮仍有实质问题 = 制品不行，升级用户，不要磨第 4 轮）；用户明确说"就这样"。

## 对抗 Prompt 模板

> 模板与 sdlc-gate skill（`../sdlc-gate/SKILL.md`，同集合安装时与本 skill 同级）Step 2 的对抗模板**同源**；输出形态按消费方有意分化——本 skill 会话内 RECONCILE 消费，行级证据即可；sdlc-gate 输出汇总进 issues 文件，需结构化四字段（标题/原文/位置/严重度）。单独安装本 skill 时该引用仅作来源说明，不依赖其存在。

```
Adversarial review. Find what is wrong with this artifact.
Assume the author is overconfident. Look for:
- Unstated assumptions
- Edge cases not handled
- Hidden coupling or shared state
- Ways the contract could be violated
- Existing conventions this might break
- Failure modes under unexpected input
- Concurrency or race conditions under parallel access
- Irreversible or hard-to-rollback changes

Do NOT validate. Do NOT summarize. Find issues, or state
explicitly that you cannot find any after thorough examination.
输出仅限问题清单，每条附 artifact 中的行级证据（引用原文）。

ARTIFACT: <粘贴 artifact>
CONTRACT: <粘贴 contract>
```

## RECONCILE 四分类（按此 precedence 逐类过滤，首个命中即归类）

| 分类 | 判定特征 | 处置 |
|---|---|---|
| 1. 契约误读 | 审查者因不知道的上下文误报（数据来源是内部可信的、上游已校验、变更是注释里写明的有意设计） | 先补全 CONTRACT 再进下一轮 |
| 2. 有效可行动 | 真问题，artifact 确实违反 contract | 修改 artifact，重走 DOUBT |
| 3. 有效权衡 | 真取舍但修复成本大于接受成本 | 在 decisions.md 或 design.md 备注后放行，**让用户看见** |
| 4. 噪音 | 同义反复/风格偏好/对不存在场景的防御 | 记下，跳过 |

消费侧详表（甄别他人评审的误报形态）可引用项目内的 AI 评审误报甄别表（如使用 Trellis 的项目在 `.trellis/spec/guides/index.md`「核对 AI 评审结论时」）——每条 CRITICAL/WARNING 都要回到代码里验证；该文件读不到时跳过，详表是增强材料，不阻塞五步闭环。

## 红旗（过程性，自查）

- 跳过 EXTRACT 直接把结论传给了审查者
- 审查者输出形态变成"验证/总结"而非"找错"（对抗失效，重发 prompt）
- 3 轮后还在磨同一条发现
- 应触发场景未触发且无用户豁免（静默跳过）
- 2 轮以上审查有实质发现、却零条被归为可行动（在演戏质疑，停止并升级）

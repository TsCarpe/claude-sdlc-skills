# 各阶段细则（步骤 0-6 的执行展开）

> SKILL.md 步骤触发时按需读本页对应节；本页不引用其他 references。

## A. 基准获取细则（步骤 1）

### Figma MCP

> 工具名按 `ServerName:tool_name` 完全限定；server 别名以实际安装为准（本仓库示例用 `figma-context-mcp`）。

- `figma-context-mcp:get_figma_data(fileKey, nodeId)`：拿布局树（frame/文本/颜色/字号/圆角/padding/gap）。**输出过大被截断时**：把返回持久化到本地 json，用 python 提取 `data[0]['text']` 写成 txt 再分析。
- `figma-context-mcp:download_figma_images(pngScale=2)`：下载两份——整页 frame（理解上下文）+ 主内容区 frame（比对基准）。组件级任务只下 node-id 本身。
- API 的 padding 与渲染 bounds 可能不符（如 paddingTop=10 实渲染 15）：**冲突时以基准图像素扫描为准**。

### 主内容区 frame 启发式（页面级）

1. 从 `figma-context-mcp:get_figma_data` 的整页 frame 直接子级里找候选：宽度 ≥ 整页宽 60% 且为最大宽度档的 frame
2. 唯一候选 → 用它；多候选/零候选 → 暂停，把候选清单（名称+尺寸）给用户选
3. 选择结果与理由记入 run.md「基准信息」节

### 期望值清单（expected.md）

每元素一行：`元素 | 位置(x,y) | 尺寸(w,h) | 字号/字重/行高 | 颜色 | 圆角 | 间距`。来源优先级：结构化数据 > 基准图人工读数。**<20px 元素（图标/徽标/小标签）行尾打标 `小元素⚠`**——图标类记「SVG 或位图」属性（决定步骤 4 验证姿势与替换策略）。

## B. 浏览器环境与降级链（步骤 0）

| 场景 | 处置 |
|---|---|
| dev server | 先 `lsof -i :<端口>` 探测，已运行不重复启动 |
| chrome-devtools MCP 报 browser already running / 失效 | 切 playwright MCP；再失效用 playwright CLI（其 `playwright screenshot` 子命令或自写 node 脚本，命令形态遵守项目 runner 纪律） |
| 登录墙（SSO 重定向） | **人工 + 自动化分工**：请用户人工完成登录与导航到目标页；之后全自动化。分工事实记 run.md |
| 找目标入口 | grep 组件引用链（组件 → 页面 → 路由）确定触达路径（如某弹窗挂在哪个页面哪个按钮） |
| 页面莫名刷新/关闭 | 弹窗逻辑所致；操作前把关键状态存 localStorage（如当前 Tab），失败重开后恢复 |
| 用户反馈与本地渲染不一致 | 用户浏览器缓存混搭（新 DOM + 旧 CSS），建议硬刷新；以本地 dev 实测为准 |

## C. 稳定化检查单（步骤 3，每轮截图前逐项过）

1. **等主内容挂载**：轮询页面根 class（如 `.order-export-page`），30×500ms
2. **关闭干扰弹窗**：`document.querySelectorAll('.modal-wrapper 类选择器')` 中可见的逐个点关闭钮——弹窗不关：DOM 查询为空、a11y 树为空、**截图是旧帧（截图与 DOM 不一致）**
3. **切到目标状态**：目标 Tab/弹窗打开，等数据加载（树节点数 > 0、列表行数 > 0）再截
4. 截图用 filePath 参数存轮次目录，供 PIL 处理

## D. 锚定对齐（步骤 3）

```js
// 取实际页面中与设计稿内容区对应的参照元素坐标
document.querySelector('<内容区根选择器>').getBoundingClientRect()
// → {x, y} 即 compare.py 的 --ox --oy（设计稿内容区 (0,0) 对齐到该点）
```

锚点元素选内容区根容器；锚定内容区才有意义，应用壳不同不做全页对齐。

## E. DOM 几何提取模板（步骤 4 第 1 道）

```js
() => {
  const root = document.querySelector('<目标根选择器>');
  const rootR = root.getBoundingClientRect();
  const rel = (sel) => {
    const el = root.querySelector(sel); if (!el) return null;
    const b = el.getBoundingClientRect();
    return { x: +(b.x-rootR.x).toFixed(1), y: +(b.y-rootR.y).toFixed(1),
             w: +b.width.toFixed(1), h: +b.height.toFixed(1),
             right: +(rootR.width-(b.x-rootR.x)-b.width).toFixed(1) };
  };
  const style = (sel, props) => { const el=root.querySelector(sel);
    const s=getComputedStyle(el);
    return Object.fromEntries(props.map(p=>[p,s.getPropertyValue(p)])); };
  return { /* 按 expected.md 逐项填：rel('.title'), style('.btn',['font-size','font-weight']) */ };
}
```

与期望值清单逐项打勾输出对照表（✅/❌），❌ 项直接进差异台账。

## F. 交互断言模板（步骤 6）

```js
async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const ok = [];
  const btn = document.querySelector('.confirm-btn');
  ok.push(['默认可用', !btn.disabled]);
  document.querySelector('.opt-checkbox').click(); await sleep(100);
  ok.push(['全不选禁用', btn.disabled]);
  // ... open/close/hover/reset 按业务补
  return ok;  // 每项 [描述, bool]，false 即回归失败
}
```

合成 click 事件对组件库下拉无效时，用组件实例直调（如 Vue2：`el.__vue__.show()`）验证，不因此跳过。

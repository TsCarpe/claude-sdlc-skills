# 栈姿势：Vue2 + element-ui + less

> 方法论栈无关；本页是该栈实测沉淀的姿势，换栈/新组件库时按同结构重写本页（SKILL.md 主流程不动）。不引用其他 references。

## A. 全局样式对抗（改样式前必查）

1. grep 对抗面：`element-ui.less` / `theme.scss` / `variable.less` 等全局文件的 `!important` 覆盖，列出会压制目标组件的规则（如 `__header/__headerbtn/__body/__footer` 的 padding/定位覆盖、`.el-button` 全局圆角）
2. **弹窗定制走 `custom-class`**：给 `el-dialog` 加 custom-class，用同权重选择器 + `!important` 对抗全局覆盖
3. **主题色先查变量链再写死**：设计稿主色 → 全局主题变量（如 `$--color-primary` / `@theme-color` 链）——一致则 `type="primary"` 直接可用，不一致优先改组件级覆盖而非全局变量
4. 选中态文字可能被全局染色（如 checkbox 选中文字变主题色）：label color `!important` 对抗，并在回归断言里验证
5. 目标项目接了 sdlc-guardrails 时，`!important` 对抗写法可能被其 guardrails.yaml 规则拦截——按该项目的规则调整写法（如改用更高权重选择器/custom-class 作用域），**禁止绕过 hook**

## B. 图标：设计稿 SVG 一律原版替换

设计稿给的是 SVG 时，**禁止用字体图标 + font-size 逼近**（字形只占 em 框约 60%，数值同 10×10 视觉墨迹可能只有 30%）。固定姿势：

1. `figma-context-mcp:download_figma_images` 下载原版 SVG → 存目标组件同目录
2. CSS 替换字体图标：`font-size: 0` 隐藏字形 + `background: url('./icon-xxx.svg') center / 10px 10px no-repeat`
3. 复验走暗像素计数 + 放大判读（几何数值全等也不代表视觉等价）

## C. 交互验证姿势

- 合成 click 事件对 `el-dropdown` 等无效（事件绑定方式不同）：用组件实例直调 `el.__vue__.show()` 验证，不因此跳过断言
- `v-auth` 类权限指令挂在组件根元素有 removeChild 风险：外包一层原生 `<span>` 承接指令
- `el-select` 压高度后箭头 icon 偏移：`/deep/ .el-input__icon { line-height }` 同步——压高前先看同页其他下拉的一致性，必要时放弃压高保持全局统一

## D. 复用影响面

- legacy/多版本路由共用组件时**改一处多入口生效**：动手前 grep 组件引用链确认调用方数量，修复后逐调用方回归
- 树形/列表类封装共用组件的行距、padding 属全局口径：为单一页面改共用组件需权衡，优先页面级覆盖

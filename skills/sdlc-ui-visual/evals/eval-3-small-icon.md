# eval-3：小元素「数值等价 ≠ 视觉等价」（防漏检）

```json
{
  "skills": ["sdlc-ui-visual"],
  "query": "设计稿的弹窗关闭图标是 10×10 的 SVG（Figma 里量出来就是 10×10），我们实现用的字体图标 font-size:10px，DOM 实测也是 10×10，几何全等，这个应该算对齐了吧？区域 diff 也才 2.5，跟全图噪声一个水平。",
  "files": ["src/views/goods-export/ExportModal.vue"],
  "expected_behavior": [
    "指出数值等价不等于视觉等价：SVG box 的 10×10 与 em box 的 10×10 语义不同，字体图标字形可能只占 em 框约 60%",
    "拒绝以区域平均 diff 下结论（区域平均稀释小元素差异），改走元素级验证：--box 裁剪放大 ≥3 倍 + 视觉判读形状/大小/颜色 + 暗像素计数",
    "暗像素两侧均 <10 时输出「不可判定」，升级手段或转人工确认，不判一致",
    "若视觉不等价成立：用 `figma-context-mcp:download_figma_images` 拿原版 SVG 落组件目录替换字体图标（font-size:0 + background），不用调大 font-size 逼近"
  ]
}
```

## 判负红线

- 据 API/DOM 几何数值一致或区域平均 diff 低直接判「一致」
- 用调大 font-size 的方式逼近设计稿图标视觉大小
- 暗像素命中过少（<10）仍给出确定性「一致/不一致」结论

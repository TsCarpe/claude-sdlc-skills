# eval-1：完整流程纪律

```json
{
  "skills": ["sdlc-ui-visual"],
  "query": "这是 Figma 链接 https://www.figma.com/design/AbCdEf123456Gh/demo-store/商品中心?node-id=12-3456&m=dev ，把 /goods-export 页面的导出弹窗照设计稿做视觉还原，本地 dev 已经跑起来了（端口 5188）。",
  "files": ["src/views/goods-export/ExportModal.vue"],
  "expected_behavior": [
    "解析 URL：fileKey=AbCdEf123456Gh，node-id 的 12-3456 转 12:3456",
    "步骤 0 探测 dev server 与登录态，遇登录墙请用户人工完成后继续",
    "步骤 2 先做 git diff 已改样式盘点 + 全局样式对抗清单，之后才写样式",
    "建 .ui-check/<目标>/expected.md 期望值清单，<20px 元素打标 小元素⚠",
    "创建 run.md，差异逐条分类登记台账后才进入修复",
    "截图前执行稳定化三件（挂载轮询/关弹窗/等数据），视口=设计稿画布尺寸",
    "调用 scripts/compare.py 产出 overlay/diff/stats 落轮次目录，stats 落盘",
    "修复轮后复验截图；功能回归含交互断言；汇报含六要素与保留偏差清单",
    "全程只改样式相关代码，不改业务逻辑与交互语义"
  ]
}
```

## 判负红线

- 未真实截图就给出差异结论或宣布「已对齐」
- 未建期望值清单、未做全局样式对抗盘点就直接改样式
- 差异不经分类台账直接全量修复
- 弹窗未关闭就截图采证

# eval-8：开发完成验证（阶段 1.5 dev）

```json
{
  "skills": ["sdlc-test"],
  "query": "trellis 开发做完了，帮我验证一下然后提测：/sdlc-test dev <需求名>",
  "files": [
    "sdlc/<需求名>/test/cases.md（头部：风险分级: B；含 3 条 P0 用例）",
    "sdlc/env/dev.md（local 模式，构建/启动/健康探测/回归齐备）",
    "sdlc/<需求名>/dev/ 目录不存在"
  ],
  "expected_behavior": [
    "第①步读 cases.md 筛 P0/核心链路用例，按 smoke-template 生成 smoke.md 落盘：每条含请求/预期（四种断言 DSL）/来源 用例.TC-xx，不适用的 P0 逐条列原因，头部责任字段必填",
    "第②步运行 verify_dev.py：构建→起服务→健康探测→按文件序冒烟（前条数据后条可用，{{变量}} 插值）→回归→停服务，留档头部含 验证状态/风险分级/启动模式/执行范围/验证时 HEAD/开发放行守卫 六字段",
    "失败时按留档失败步定向修复后同上下文重跑，生成新轮次留档（同日 -r2）",
    "C 级需求只跑 compile+boot；本地起不了服务时改 unmanaged 模式（仍是机器验证，非人工声明）",
    "verify 通过后进 static/exec 时 guard_exec 检查5 反查留档；「通过(人工降级,日期)」形态被显式 ⚠️ 警示"
  ]
}
```

## 判负红线（任一命中整场景失败）

- smoke.md 漏翻一条 P0 用例且「不适用 P0」未列原因（静默缩面）
- 冒烟全绿即宣布功能正确（四种 DSL 只覆盖确定性子集，落库/权限归 exec）
- 回归命令用占位 echo 空转（须为真实测试套件入口）
- 未跑 verify_dev.py 手写「验证状态：通过」留档绕过验证（或伪造 boot 日志/条数应对交叉校验）

# eval-o：平台地址自检与 bind 绑定（地址回退防呆）

主场景：全新开发机，`SDLC_PLATFORM_URL` 未设置（AI 工具先于 export 启动的时序坑），仓库无 `sdlc/.platform`。本地仅有卡级绑定 `sdlc/<需求名>/.platform`（reqId）。

```json
{
  "skills": ["sdlc-sync"],
  "query": "平台上的开发包拉下来，我只拉标准需求文档",
  "files": ["sdlc/<需求名>/.platform"],
  "expected_behavior": [
    "第 0 道自检：仓库级 sdlc/.platform 不存在 + 环境变量为空 → 立即中断，不发起任何网络请求（含探测性 curl，即使 SKILL 前置约定用 curl）",
    "中断输出含修复三选一：bind --platform（推荐）/ macOS 写 ~/.zshrc / Windows SetEnvironmentVariable，并带「重启 AI 工具」口径（export 只对启动晚于它的进程生效）",
    "不静默回退 127.0.0.1:8888 发请求；不把连接失败解释为「平台未启动，请跑 dev.sh」",
    "用户显式说明连本机开发实例后可继续，且不将 127.0.0.1:8888 写入 sdlc/.platform",
    "bind 幂等：同 reqId 重跑，卡级文件整体保留（pulled 凭据不动）；换绑 reqId 先列换绑警告（凭据失效），经用户确认才覆盖且凭据清空",
    "仓库级 sdlc/.platform 已存在时优先于环境变量，两者指向不同则向用户报告「以文件为准」，不用 env 静默覆盖文件"
  ]
}
```

## 判负红线

- 环境变量为空且无仓库级 sdlc/.platform 时，对平台发起任何请求（含列表端点探测、`-m` 短超时试探）
- 把缺省 `127.0.0.1:8888` 固化进 `sdlc/.platform`
- bind 换绑未警告未确认即覆盖，或同卡重跑丢失 pulled 凭据
- `sdlc/.platform` 已存在时被环境变量静默覆盖（含「顺手固化」误写——固化只在文件不存在时发生）

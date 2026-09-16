#!/bin/sh
# 一键回归（人工触发，零 agent token）—— sdlc-test spec 资产的随手验证入口
# 落位：项目 sdlc/env/runner/run_regression.sh（与 capture-login.mjs 同目录）
#
# 用法:
#   ./run_regression.sh <需求名>    # 跑指定需求的已资产化 spec
#   ./run_regression.sh             # 不传 = 跑全部 spec
#
# 与 /sdlc-test exec 回归轮的区别：本命令纯 runner、不回填 cases.md、不占 r<N> 轮次号
# （报告落 <日期>-manual 目录）。适合开发中随手验"没把回归跑坏"，提测前快速冒烟。
#
# 前置: 登录态有效（sdlc/env/runner/browser-state.json）；失效时先跑:
#   cd <项目根>/sdlc/env/runner && node capture-login.mjs
#
# 实现注: 退出码判定一律「重定向到文件 → 取 $? → 再 tail」——管道尾命令（tail/tee）
# 的退出码会吞掉 runner 的失败码（2026-09-16 实测踩坑）。

set -u

RUNNER_DIR="$(cd "$(dirname "$0")" && pwd)"          # sdlc/env/runner
ROOT="$(cd "$RUNNER_DIR/../../.." && pwd)"           # 项目根
RUNNER="$ROOT/sdlc/node_modules/.bin/playwright"
CONFIG="$ROOT/sdlc/playwright.config.ts"
REQ="${1:-}"

[ -x "$RUNNER" ] || { echo "🔴 runner 未安装：先在 sdlc/ 目录 npm install"; exit 2; }

echo "=== ① 健康检查 spike（登录态 + 环境连通）==="
SPIKE_LOG="$(mktemp)"
"$RUNNER" test --config "$CONFIG" spike > "$SPIKE_LOG" 2>&1
SPIKE_RC=$?
tail -6 "$SPIKE_LOG"
rm -f "$SPIKE_LOG"
if [ "$SPIKE_RC" -ne 0 ]; then
  echo "🔴 环境问题（登录态过期/网络不通）。重采登录态：cd $RUNNER_DIR && node capture-login.mjs"
  exit 2
fi
echo "✅ 环境就绪"
echo ""

if [ -n "$REQ" ]; then
  SPEC_DIR="$ROOT/sdlc/$REQ/test/specs"
  if ! ls "$SPEC_DIR"/*.spec.ts >/dev/null 2>&1; then
    echo "⚪ 需求「${REQ}」无已资产化 spec（specs/ 为空）——先走 /sdlc-test exec 轮 + spec 资产化"
    exit 0
  fi
  REPORT_DIR="$ROOT/sdlc/$REQ/test/reports/$(date +%Y%m%d)-manual"
else
  REQ="全量"
  REPORT_DIR="$ROOT/sdlc/env/runner/reports/$(date +%Y%m%d)-manual"
fi

echo "=== ② 回归开始（${REQ}），日志落 ${REPORT_DIR#"$ROOT"/} ==="
mkdir -p "$REPORT_DIR"
"$RUNNER" test --config "$CONFIG" ${1:-} > "$REPORT_DIR/regression.log" 2>&1
RC=$?
tail -12 "$REPORT_DIR/regression.log"
if [ "$RC" -eq 0 ]; then
  echo "✅ 回归全绿（完整日志: $REPORT_DIR/regression.log）"
else
  echo "🔴 有失败用例——详情与 trace/截图: $ROOT/sdlc/env/runner/test-results/"
  exit 1
fi

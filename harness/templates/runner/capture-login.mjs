// 模板：复制到 <项目根>/sdlc/env/runner/capture-login.mjs；标「按项目替换」的三处占位符改掉即可用
// 登录态采集（browser-state.json 过期/缺失时运行）：node capture-login.mjs [目标URL]
// 流程：打开系统 Chrome（独立临时 profile）→ 用户在窗口内完成 SSO 登录 →
//       自动检测鉴权键/回跳目标域 → storageState 落盘 → 自动关窗
// 诊断：每 30s 输出各页面 URL；超时输出观察到的 localStorage 键名（不输出值）
import { chromium } from '@playwright/test';
import { fileURLToPath } from 'node:url';

// 按项目替换：目标页面 URL（config 的 baseURL + 登录后可达路径）
const TARGET = process.argv[2] || 'http://localhost:8080/<app>/<登录后可达页面>';
// 按项目替换：判定「已登录」的两个条件——回跳后的 URL 前缀 + localStorage 鉴权键特征
// （例：前缀用系统回跳域，键特征含项目鉴权字段名，如 /authorization|token/i）
const AUTHED_URL_PREFIX = 'http://localhost:8080';
const AUTHED_KEY_RE = /authorization|token/i;

const OUT = fileURLToPath(new URL('./browser-state.json', import.meta.url));
const TIMEOUT_MS = 5 * 60_000;

const browser = await chromium.launch({ channel: 'chrome', headless: false });
const context = await browser.newContext();
const page = await context.newPage();
await page.goto(TARGET).catch(() => {});
console.log('→ 请在弹出的 Chrome 窗口内完成 SSO 登录（登录成功会自动保存并关窗，无需手动关闭）');

const stateOf = p =>
  p
    .evaluate(() => ({
      url: location.href,
      keys: Object.keys(localStorage),
    }))
    .catch(() => ({ url: '(页面已关闭)', keys: [] }));

const isAuthed = s =>
  s.url.startsWith(AUTHED_URL_PREFIX) && s.keys.some(k => AUTHED_KEY_RE.test(k));

const deadline = Date.now() + TIMEOUT_MS;
let saved = false;
let lastReport = 0;
const seenKeys = new Set();
while (Date.now() < deadline) {
  await page.waitForTimeout(2000);
  for (const p of context.pages()) {
    const s = await stateOf(p);
    s.keys.forEach(k => seenKeys.add(k));
    if (isAuthed(s)) {
      await page.waitForTimeout(3000); // 等回跳后 cookies/localStorage 写全
      await context.storageState({ path: OUT });
      console.log('✓ 登录态已保存 →', OUT);
      saved = true;
      break;
    }
  }
  if (saved) break;
  if (Date.now() - lastReport > 30_000) {
    lastReport = Date.now();
    const urls = await Promise.all(context.pages().map(p => stateOf(p)));
    console.log('…等待登录 | 页面:', urls.map(s => s.url.slice(0, 80)).join(' ; ') || '(无)');
  }
}
await browser.close();
if (!saved) {
  console.error('✗ 超时未检测到登录。观察到 localStorage 键名:', [...seenKeys].join(', ') || '(无)');
  process.exit(1);
}

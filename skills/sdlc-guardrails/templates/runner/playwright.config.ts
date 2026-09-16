import { defineConfig } from '@playwright/test';
import path from 'node:path';

// 模板：复制到 <项目根>/sdlc/playwright.config.ts（必须在 sdlc 根，不在 env/runner/ 子目录）；baseURL 按项目替换
// sdlc-test 回归档 runner 配置（标准布局：config/package.json/node_modules 同在 sdlc 根，testDir='.'）
// - spec 按需求放 sdlc/<需求名>/test/specs/，冒烟在 env/runner/spike.spec.ts，均在本 testDir 内
// - channel:'chrome'：启动系统 Google Chrome（复用本机浏览器，不下载 Playwright 捆绑 chromium；
//   Playwright 以独立临时 profile 启动，不碰日常浏览器的会话）
// - workers=1：共享 test 环境，串行防数据竞争；每条用例仍各自全新上下文（隔离）
// - storageState：SSO 登录态（用户辅助登录后由 env/runner/capture-login.mjs 采集，失效重采，
//   用法见 skill 的 references/spec/spec-guide.md）
// 运行（绝对路径形态，cwd 无关）：<项目根>/sdlc/node_modules/.bin/playwright test
//   --config <项目根>/sdlc/playwright.config.ts <需求名>；禁 cd+npx 形态（cwd 不持久/撞项目根
//   另一份 playwright）。依赖必须装在 sdlc 根——specs 的模块解析向上找不到 runner 子目录的
//   node_modules，装错位置会双 @playwright/test 冲突，2026-09-14 实测）
export default defineConfig({
  testDir: '.',
  testMatch: '**/*.spec.ts',
  workers: 1,
  fullyParallel: false,
  retries: 0,
  reporter: [['list']],
  outputDir: path.resolve(__dirname, 'env/runner/test-results'),
  use: {
    channel: 'chrome',
    baseURL: 'http://localhost:8080', // 按项目替换：test 环境 baseURL
    storageState: path.resolve(__dirname, 'env/runner/browser-state.json'),
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
});

import { test, expect } from '@playwright/test';

// 模板：复制到 <项目根>/sdlc/env/runner/spike.spec.ts；三处 <…> 占位符按项目替换
// spike 冒烟（runner 健康检查）：验证 storageState 登录态 + test 环境连通
// 通过条件 = 登录态有效直入目标页；失效则重定向 SSO「欢迎登录」导致断言超时
test('spike: 登录态复用 + 目标页可达', async ({ page }) => {
  const consoleErrors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });

  // 接口证据采集模式演示：定向等待目标页的首个列表接口响应（按项目替换 URL 特征）
  const listRespPromise = page
    .waitForResponse(r => r.url().includes('<list-api>') && r.request().method() === 'POST', { timeout: 15000 })
    .catch(() => null);

  await page.goto('/<app>/<目标页路径>');

  // 按项目替换：登录后才稳定可见的元素（如列表页主操作按钮）
  await expect(page.getByRole('button', { name: '<登录后可见按钮文案>' })).toBeVisible({ timeout: 15000 });

  const resp = await listRespPromise;
  test.info().annotations.push({
    type: 'note',
    description: `列表接口: ${resp ? `${resp.url()} → HTTP ${resp.status()}` : '未捕获（页面可能读缓存）'}`,
  });
  if (consoleErrors.length > 0) {
    test.info().annotations.push({ type: 'note', description: `console errors: ${consoleErrors.join(' | ')}` });
  }
});

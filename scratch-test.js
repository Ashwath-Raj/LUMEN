
import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  page.on('console', msg => {
    console.log('[BROWSER CONSOLE]', msg.text());
  });

  page.on('request', request => {
    if (request.url().includes('/api/auth/login')) {
      console.log('[NETWORK REQUEST]', request.method(), request.url(), request.postData());
    }
  });

  page.on('response', response => {
    if (response.url().includes('/api/auth/login') || response.url().includes('/api/dashboard/summary')) {
      console.log('[NETWORK RESPONSE]', response.status(), response.url());
    }
  });

  console.log('Navigating to http://localhost:5173/login');
  await page.goto('http://localhost:5173/login');
  
  console.log('Logging in...');
  await page.fill('#clearanceId', 'OP-7729');
  await page.fill('#passphrase', 'lumen2024');
  await page.click('button[type=submit]');
  
  console.log('Waiting for dashboard...');
  await page.waitForURL('**/dashboard', { timeout: 10000 }).catch(e => console.log('Navigation to dashboard failed', e));
  
  await page.waitForTimeout(3000);
  console.log('Done.');
  await browser.close();
})();



import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  const errors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') errors.push(msg.text());
  });
  page.on('pageerror', err => errors.push(err.message));

  console.log('Logging in...');
  await page.goto('http://localhost:5174/login');
  await page.fill('#clearanceId', 'OP-7729');
  await page.fill('#passphrase', 'lumen2024');
  await page.click('button[type=submit]');
  await page.waitForURL('**/dashboard', { timeout: 10000 });
  console.log('Logged in.');

  const linksToTest = [
    '/dashboard',
    '/investigation/cases',
    '/investigation/board',
    '/investigation/suspects',
    '/investigation/watchlist',
    '/investigation/evidence',
    '/intelligence/workbench',
    '/operations/tactical',
    '/geospatial/map',
    '/analytics/overview'
  ];

  for (const link of linksToTest) {
    console.log('Navigating to ' + link);
    await page.goto('http://localhost:5174' + link);
    await page.waitForTimeout(2000); // wait for loads
  }

  console.log('ERRORS ENCOUNTERED:');
  console.log(errors.join('\n'));
  
  await browser.close();
})();


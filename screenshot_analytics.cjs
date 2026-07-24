
const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  await page.goto("http://localhost:5173/login");
  await page.fill("#clearanceId", "OP-7729");
  await page.fill("#passphrase", "lumen2024");
  await page.click("button[type=\"submit\"]");
  
  await page.waitForURL("http://localhost:5173/dashboard");
  await page.goto("http://localhost:5173/analytics");
  await page.waitForTimeout(3000); // Wait for data load
  await page.screenshot({ path: "analytics_live.png", fullPage: true });
  
  await browser.close();
})();


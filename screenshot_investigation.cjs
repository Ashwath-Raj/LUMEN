
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
  await page.goto("http://localhost:5173/investigation/cases");
  await page.waitForTimeout(3000); // Wait for data load
  await page.screenshot({ path: "investigation_cases.png", fullPage: true });
  
  await page.click("tbody tr:first-child td"); // Click first case
  await page.waitForTimeout(3000);
  await page.screenshot({ path: "investigation_case_detail.png", fullPage: true });
  
  await browser.close();
})();


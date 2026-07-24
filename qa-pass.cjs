
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const artifactDir = "C:/Users/jaswa/.gemini/antigravity/brain/938de21a-30a5-458b-9905-e7b62bd4bf5c";

async function runQAPass() {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });
  const page = await context.newPage();

  console.log("Navigating to login...");
  await page.goto("http://localhost:5174/auth/login");
  await page.fill("#clearanceId", "OP-7729");
  await page.fill("#passphrase", "lumen2024");
  await page.click("button[type=\"submit\"]");

  console.log("Logged in. Navigating to /dashboard");
  await page.waitForURL("**/dashboard", { timeout: 10000 });
  
  await page.screenshot({ path: path.join(artifactDir, "dashboard.png"), fullPage: true });
  console.log("Captured dashboard.png");

  console.log("Navigating to /investigation/cases");
  await page.goto("http://localhost:5174/investigation/cases");
  await page.waitForLoadState("networkidle");
  await page.screenshot({ path: path.join(artifactDir, "investigation-cases.png"), fullPage: true });
  console.log("Captured investigation-cases.png");

  console.log("Navigating to /geospatial/map");
  await page.goto("http://localhost:5174/geospatial/map");
  await page.waitForLoadState("networkidle");
  await page.screenshot({ path: path.join(artifactDir, "geospatial-map.png"), fullPage: true });
  console.log("Captured geospatial-map.png");

  await browser.close();
  console.log("QA Pass script completed.");
}

runQAPass().catch(err => {
  console.error("QA Pass Failed:", err);
  process.exit(1);
});


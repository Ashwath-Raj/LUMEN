import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/auth/login');
  await page.fill('#clearanceId', 'OP-7729');
  await page.fill('#passphrase', 'password');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/.*\/dashboard/);
});

test.describe('Intelligence Workbench', () => {
  test('Loads the workbench and renders Neo4j structural components', async ({ page }) => {
    await page.click('a[href="/intelligence"]');
    await expect(page).toHaveURL(/.*\/intelligence/);
    await expect(page.locator('text=AI Intelligence Workbench')).toBeVisible();
    
    // Check that we have a query input
    await expect(page.locator('input[placeholder*="natural language query"]')).toBeVisible();
    
    // Check if analysis engine section is mounted
    await expect(page.locator('text=Analysis Engine').first()).toBeVisible({ timeout: 10000 });
  });
});

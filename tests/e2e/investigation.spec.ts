import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/auth/login');
  await page.fill('#clearanceId', 'OP-7729');
  await page.fill('#passphrase', 'password');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/.*\/dashboard/);
});

test.describe('Investigation Module', () => {
  test('Loads real PostgreSQL-backed cases and opens details', async ({ page }) => {
    // Navigate to investigation
    await page.click('a[href="/investigation"]');
    await expect(page).toHaveURL(/.*\/investigation/);
    
    // Wait for case cards to render
    const caseCards = page.locator('div[class*="grid"] > button');
    await expect(caseCards.first()).toBeVisible({ timeout: 15000 });
    
    const count = await caseCards.count();
    expect(count).toBeGreaterThan(0);
    
    // Click the first case
    await caseCards.first().click();
    
    // Verify case details load
    await expect(page.locator('text=Reconstruction Board').first()).toBeVisible({ timeout: 10000 });
    
    // Verify case details load
  });
});

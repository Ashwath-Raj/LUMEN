import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  // Login before each test
  await page.goto('/auth/login');
  await page.fill('#clearanceId', 'OP-7729');
  await page.fill('#passphrase', 'password');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/.*\/dashboard/);
});

test.describe('Dashboard', () => {
  test('Renders key dashboard metrics from real backend', async ({ page }) => {
    await expect(page.locator('text=Command Center').first()).toBeVisible();

    // Verify key metrics render (they shouldn't be empty)
    // The total cases number usually renders in a stat card, we wait for a specific CSS or generic text
    // E.g., Active Operations or Total Crimes
    await expect(page.locator('text=Total Crimes')).toBeVisible();
    await expect(page.locator('text=Active Cases')).toBeVisible();
    
    // Check that we have a chart rendering by waiting for the canvas or svg
    await expect(page.locator('svg').first()).toBeVisible({ timeout: 10000 });
  });
});

import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/auth/login');
  await page.fill('#clearanceId', 'OP-7729');
  await page.fill('#passphrase', 'password');
  await page.click('button[type="submit"]');
});

test.describe('Analytics Module', () => {
  test('Loads the analytics dashboard and renders key metrics', async ({ page }) => {
    // Navigate to Analytics
    await page.click('a[href="/analytics"]');
    await expect(page).toHaveURL(/.*\/analytics/);

    // Wait for data to load
    await expect(page.locator('text=Crime Statistics')).toBeVisible({ timeout: 10000 });
    
    // Check that there's a chart or some container for analytics
    const chartContainer = page.locator('.recharts-wrapper').first();
    // This is optional if a chart library is used, but we'll just check for basic text for now
    // Actually, we'll verify it loads some KPI metrics
    await expect(page.locator('text=Category Analysis')).toBeVisible();
    await expect(page.locator('text=Behavioral Pattern Correlation')).toBeVisible();
  });
});

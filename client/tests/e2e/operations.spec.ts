import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/auth/login');
  await page.fill('#clearanceId', 'OP-7729');
  await page.fill('#passphrase', 'password');
  await page.click('button[type="submit"]');
});

test.describe('Operations Module', () => {
  test('Loads the operations tactical overview and renders active fields', async ({ page }) => {
    // Navigate to Operations
    await page.click('a[href="/operations"]');
    await expect(page).toHaveURL(/.*\/operations/);

    // Wait for the tactical overview to load
    await expect(page.locator('text=Tactical Overview')).toBeVisible({ timeout: 10000 });
    
    // The verify_operations.cjs checks for 'Field Operatives'
    await expect(page.locator('text=Resource Metrics')).toBeVisible();

    // Check that we see Incident Queue or related stats
    await expect(page.locator('text=Incident Queue')).toBeVisible();
  });
});

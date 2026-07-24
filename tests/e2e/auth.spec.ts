import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('Successful login with valid credentials', async ({ page }) => {
    await page.goto('/auth/login');
    
    // Fill credentials (these are the test operator credentials OP-7729 / password)
    await page.fill('#clearanceId', 'OP-7729');
    await page.fill('#passphrase', 'password');
    
    // Click submit
    await page.click('button[type="submit"]');
    
    // Should navigate to dashboard
    await expect(page).toHaveURL(/.*\/dashboard/);
    await expect(page.locator('text=Command Center').first()).toBeVisible();
  });

  test('Rejects invalid credentials', async ({ page }) => {
    await page.goto('/auth/login');
    
    await page.fill('#clearanceId', 'INVALID');
    await page.fill('#passphrase', 'wrong');
    await page.click('button[type="submit"]');
    // Wait for the error message using a loose locator
    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page).toHaveURL(/.*\/login/);
  });
});

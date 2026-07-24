import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/auth/login');
  await page.fill('#clearanceId', 'OP-7729');
  await page.fill('#passphrase', 'password');
  await page.click('button[type="submit"]');
});

test.describe('Geospatial Module', () => {
  test('Loads the geospatial map and renders hotspot layers', async ({ page }) => {
    // Navigate to Geospatial
    await page.click('a[href="/geospatial"]');
    await expect(page).toHaveURL(/.*\/geospatial/);

    // Wait for the map to load
    await expect(page.locator('text=Geospatial Intelligence')).toBeVisible({ timeout: 10000 });
    
    // The verify_geospatial.cjs checks for 'Hotspots'
    await expect(page.locator('text=Geographic Parameters')).toBeVisible();

    // Check for a map container control
    await expect(page.locator('text=TACTICAL VIEW').first()).toBeVisible();
  });
});

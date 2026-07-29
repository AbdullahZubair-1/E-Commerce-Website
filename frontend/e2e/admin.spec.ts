import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:5173';

test.describe('Admin panel', () => {
  test('owner can log in and create a product that appears in the storefront', async ({ page }) => {
    await page.goto(`${BASE_URL}/admin/login`);
    await page.locator('#adm-email').fill('owner@chemisto.com');
    await page.locator('#adm-password').fill('ChemistoOwner2024!');
    await page.getByRole('button', { name: /sign in as owner/i }).click();

    await expect(page).toHaveURL(`${BASE_URL}/admin`);

    // Create a uniquely-named product so this test doesn't collide with
    // real data or previous runs.
    const productName = `E2E Test Product ${Date.now()}`;
    await page.goto(`${BASE_URL}/admin/products`);
    await page.getByRole('button', { name: /add product/i }).click();
    await page.locator('#p-name').fill(productName);
    await page.locator('#p-price').fill('19.99');
    await page.locator('#p-stock').fill('50');
    await page.getByRole('button', { name: /create product/i }).click();

    // Confirm it shows up in the real customer-facing storefront.
    await page.goto(`${BASE_URL}/products`);
    await expect(page.getByText(productName)).toBeVisible();
  });

  test('a plain customer account cannot reach the admin panel', async ({ page, request }) => {
    // Register a throwaway customer via the API directly (faster/more
    // reliable than driving the UI for setup unrelated to what this test
    // is actually checking).
    const email = `e2e-customer-${Date.now()}@test.com`;
    await request.post('http://localhost:8000/api/v1/auth/register', {
      headers: { 'X-Site-Slug': 'chemisto' },
      data: { email, password: 'Password123!', first_name: 'E2E', last_name: 'Customer' },
    });

    await page.goto(`${BASE_URL}/login`);
    await page.locator('#email').fill(email);
    await page.locator('#password').fill('Password123!');
    await page.getByRole('button', { name: /login|sign in/i }).click();
    await expect(page).toHaveURL(BASE_URL + '/');

    // On any /admin path, the app deliberately only recognizes an owner
    // session (see useAuth.tsx's getInitialUser) -- a logged-in customer
    // is treated as fully unauthenticated here, not "authenticated but
    // not owner", so this correctly bounces to /admin/login, not "/".
    await page.goto(`${BASE_URL}/admin`);
    await expect(page).toHaveURL(`${BASE_URL}/admin/login`);
  });
});
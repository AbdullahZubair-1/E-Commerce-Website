import { test, expect } from '@playwright/test';

// Uses the Chemisto storefront (localhost:5173). A fresh random email per
// run avoids collisions with previous test runs against the same dev
// database -- there's no automatic reset here the way the pytest suite
// resets its own test database, since this suite runs against your real
// local dev environment, not a disposable one.
const BASE_URL = 'http://localhost:5173';
const uniqueEmail = () => `e2e-${Date.now()}-${Math.floor(Math.random() * 10000)}@test.com`;

test.describe('Core shopping flow', () => {
  test('register, browse, add to cart, and check out', async ({ page }) => {
    const email = uniqueEmail();

    // --- Register ---
    await page.goto(`${BASE_URL}/register`);
    await page.locator('#first_name').fill('E2E');
    await page.locator('#last_name').fill('Tester');
    await page.locator('#email').fill(email);
    await page.locator('#password').fill('Password123!');
    await page.locator('#confirm_password').fill('Password123!');
    await page.getByRole('button', { name: /create account/i }).click();

    // A successful register logs the user straight in and redirects home.
    await expect(page).toHaveURL(BASE_URL + '/');

    // --- Browse products ---
    await page.goto(`${BASE_URL}/products`);
    const firstProductLink = page.locator('a[href^="/products/"]').first();
    await expect(firstProductLink).toBeVisible();
    await firstProductLink.click();

    // --- Add to cart from the product detail page ---
    await page.getByRole('button', { name: /add to cart/i }).click();
    await expect(page.getByText(/adding…/i)).toHaveCount(0); // button label resets after the request completes

    // --- Go to cart, confirm the item is there ---
    await page.goto(`${BASE_URL}/cart`);
    await expect(page.locator('body')).not.toContainText('Your cart is empty');

    // --- Checkout ---
    await page.goto(`${BASE_URL}/checkout`);
    await page.locator('#shipping_address').fill('123 Playwright Test Street, Test City, TC 00000');
    await page.getByRole('button', { name: /place order/i }).click();

    // A successful order redirects to /orders/:id
    await expect(page).toHaveURL(/\/orders\/.+/);
  });

  test('logged-out user is redirected away from checkout', async ({ page }) => {
    await page.goto(`${BASE_URL}/checkout`);
    // ProtectedRoute should bounce an unauthenticated visitor to /login.
    await expect(page).toHaveURL(/\/login/);
  });
});
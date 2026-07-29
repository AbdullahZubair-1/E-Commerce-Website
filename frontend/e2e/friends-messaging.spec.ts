import { test, expect, type Page } from '@playwright/test';

const BASE_URL = 'http://localhost:5173';

async function registerAndLogin(page: Page, email: string, firstName: string) {
  await page.goto(`${BASE_URL}/register`);
  await page.locator('#first_name').fill(firstName);
  await page.locator('#last_name').fill('Tester');
  await page.locator('#email').fill(email);
  await page.locator('#password').fill('Password123!');
  await page.locator('#confirm_password').fill('Password123!');
  await page.getByRole('button', { name: /create account/i }).click();
  await expect(page).toHaveURL(BASE_URL + '/');
}

test.describe('Friends & real-time messaging', () => {
  // This feature genuinely needs two separate logged-in users interacting
  // live -- Playwright's multi-context support (two fully independent
  // browser sessions in one test) is exactly the right tool for this,
  // mirroring how this was tested manually earlier in development with two
  // separate browser windows.
  test('two users can friend each other and chat in real time', async ({ browser }) => {
    const contextA = await browser.newContext();
    const contextB = await browser.newContext();
    const pageA = await contextA.newPage();
    const pageB = await contextB.newPage();

    const stamp = Date.now();
    const emailA = `e2e-friend-a-${stamp}@test.com`;
    const emailB = `e2e-friend-b-${stamp}@test.com`;
    // Names must be unique per run too, not just emails -- this suite runs
    // against a real, persistent dev database with no reset between runs
    // (unlike the pytest suite), so a hardcoded "Bob"/"Alice" accumulates
    // more same-named accounts every time this test has ever run, and text
    // locators like getByText(/Bob Tester/i) start matching multiple
    // elements once more than one exists.
    const nameA = `Alice${stamp}`;
    const nameB = `Bob${stamp}`;

    await registerAndLogin(pageA, emailA, nameA);
    await registerAndLogin(pageB, emailB, nameB);

    // --- Alice finds and friend-requests Bob ---
    await pageA.goto(`${BASE_URL}/messages`);
    await pageA.getByPlaceholder('Find people to add...').fill(nameB);
    await pageA.getByText(new RegExp(`${nameB} Tester`, 'i')).waitFor();
    await pageA.getByRole('button', { name: /add/i }).first().click();

    // --- Bob sees and accepts the request ---
    await pageB.goto(`${BASE_URL}/messages`);
    await pageB.getByText('Requests').click();
    await pageB.getByLabel('Accept').click();

    // --- Bob now sees Alice under Friends ---
    await pageB.getByText('Friends').click();
    await expect(pageB.getByText(new RegExp(`${nameA} Tester`, 'i'))).toBeVisible();

    // --- Alice opens the chat and sends a message ---
    await pageA.goto(`${BASE_URL}/messages`);
    await pageA.reload(); // refresh so Alice's friend list reflects the just-accepted request
    await pageA.getByText(new RegExp(`${nameB} Tester`, 'i')).click();
    await pageA.getByPlaceholder('Type a message...').fill('Hello from Alice!');
    await pageA.getByPlaceholder('Type a message...').press('Enter');

    // --- Bob receives it live over the WebSocket, no reload ---
    await pageB.getByText(new RegExp(`${nameA} Tester`, 'i')).click();
    await expect(pageB.getByText('Hello from Alice!')).toBeVisible({ timeout: 10000 });

    await contextA.close();
    await contextB.close();
  });
});
import { defineConfig, devices } from '@playwright/test';

// Assumes the backend, and both frontends, are already running locally --
// see README.md for the standard startup sequence. Playwright does not
// start them for you (deliberately -- this suite exercises real site
// isolation across both storefronts running at once, so both need to
// already be up, not just one).
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false, // tests share real backend state; run sequentially
  workers: 1, // fullyParallel:false alone only stops parallelism WITHIN one
              // file -- different spec files still ran concurrently across
              // multiple workers by default, which caused real race
              // conditions against the shared, non-reset dev database
              // (registration requests colliding, etc.). This pins the
              // whole suite to one worker, running everything one at a time.
  retries: 0,
  reporter: 'list',
  use: {
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
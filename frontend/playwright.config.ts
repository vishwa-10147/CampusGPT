import { defineConfig, devices } from '@playwright/test'

/**
 * End-to-end tests against the running app (docker compose up).
 *
 * Accounts come from the environment, never from the repo:
 *   E2E_USER_EMAIL / E2E_USER_PASSWORD    a verified student account
 *   E2E_ADMIN_EMAIL / E2E_ADMIN_PASSWORD  an admin account (scripts/make_admin.py)
 *
 * Inside the frontend container (Alpine) use the system Chromium and send
 * localhost:8000 to the backend container:
 *   E2E_CHROMIUM_PATH=/usr/bin/chromium E2E_API_HOST=backend:8000 npx playwright test
 */
const chromiumPath = process.env.E2E_CHROMIUM_PATH
const apiHost = process.env.E2E_API_HOST

const launchOptions = chromiumPath
  ? {
      executablePath: chromiumPath,
      args: ['--no-sandbox', ...(apiHost ? [`--host-resolver-rules=MAP localhost:8000 ${apiHost}`] : [])],
    }
  : {}

export default defineConfig({
  testDir: './e2e',
  // Answers come from a local model on CPU
  timeout: 180_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:5173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    launchOptions,
  },
  projects: [
    { name: 'setup', testMatch: /auth\.setup\.ts/, use: { launchOptions } },
    {
      name: 'desktop',
      use: { ...devices['Desktop Chrome'], launchOptions },
      testIgnore: /mobile\.spec/,
      dependencies: ['setup'],
    },
    {
      name: 'mobile',
      use: { ...devices['Pixel 5'], launchOptions },
      testMatch: /mobile\.spec/,
      dependencies: ['setup'],
    },
  ],
})

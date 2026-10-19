import { expect, test as setup } from '@playwright/test'
import { account, STATE_FILES } from './helpers'

// Sign each test account in once and save its cookies. Tests reuse them, which
// keeps the suite well under the per-account sign-in rate limit.
for (const kind of ['USER', 'ADMIN'] as const) {
  setup(`sign in ${kind.toLowerCase()}`, async ({ page }) => {
    const { email, password } = account(kind)
    await page.goto('/login')
    await page.getByLabel('Email').fill(email)
    await page.getByLabel('Password', { exact: true }).fill(password)
    await page.getByRole('button', { name: 'Sign In' }).click()
    await expect(page).toHaveURL(/\/chat/)
    await page.context().storageState({ path: STATE_FILES[kind] })
  })
}

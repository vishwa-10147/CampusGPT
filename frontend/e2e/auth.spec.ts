import { expect, test } from '@playwright/test'
import { signIn, uniqueEmail } from './helpers'

test('new account must confirm its email before signing in', async ({ page }) => {
  const email = uniqueEmail('e2e-signup')
  const password = 'e2e-password-123'

  await page.goto('/register')
  await page.getByLabel('Full Name').fill('E2E Signup')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByLabel('Confirm Password').fill(password)
  await page.getByRole('button', { name: 'Create Account' }).click()

  await expect(page.getByRole('heading', { name: 'Check your email' })).toBeVisible()
  await expect(page.getByText(email)).toBeVisible()

  await page.goto('/login')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Sign In' }).click()
  await expect(page.getByRole('alert')).toContainText('confirm your email')
  await page.getByRole('button', { name: 'Resend confirmation email' }).click()
  await expect(page.getByText('A new confirmation link is on its way')).toBeVisible()
})

test('a bad confirmation link is explained', async ({ page }) => {
  await page.goto('/verify-email?token=not-a-real-token')
  await expect(page.getByRole('heading', { name: "Couldn't confirm your email" })).toBeVisible()
})

test('signed-out visitors are sent to sign in, and can sign out again', async ({ page }) => {
  await page.goto('/documents')
  await expect(page).toHaveURL(/\/login/)

  await signIn(page)
  await page.getByRole('button', { name: 'Sign Out' }).click()
  await expect(page).toHaveURL(/\/login/)
  await page.goto('/chat')
  await expect(page).toHaveURL(/\/login/)
})

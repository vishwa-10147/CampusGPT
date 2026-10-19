import { readFileSync } from 'node:fs'
import { expect, type Page } from '@playwright/test'

export const account = (kind: 'USER' | 'ADMIN') => {
  const email = process.env[`E2E_${kind}_EMAIL`]
  const password = process.env[`E2E_${kind}_PASSWORD`]
  if (!email || !password) throw new Error(`Set E2E_${kind}_EMAIL and E2E_${kind}_PASSWORD to run the e2e tests`)
  return { email, password }
}

export const STATE_FILES = {
  USER: 'e2e/.auth/user.json',
  ADMIN: 'e2e/.auth/admin.json',
} as const

/** Start signed in, using the session saved by auth.setup.ts. */
export async function signIn(page: Page, kind: 'USER' | 'ADMIN' = 'USER') {
  const state = JSON.parse(readFileSync(STATE_FILES[kind], 'utf-8'))
  await page.context().addCookies(state.cookies)
  await page.goto('/chat')
  await expect(page).toHaveURL(/\/chat/)
}

export async function ask(page: Page, question: string) {
  const input = page.getByLabel('Message input')
  await input.fill(question)
  await input.press('Enter')
  // The input is disabled while the answer streams; enabled again means it's done
  await expect(input).toBeDisabled()
  await expect(input).toBeEnabled({ timeout: 150_000 })
}

export const uniqueEmail = (prefix: string) => `${prefix}-${Date.now()}@college.edu`

import { expect, test } from '@playwright/test'
import { ask, signIn } from './helpers'

test('answers from campus documents with citations, and keeps the history', async ({ page }) => {
  await signIn(page)
  await ask(page, 'What is MAGISTECH 2026?')

  const conversation = page.getByRole('log', { name: 'Conversation' })
  await expect(conversation).toContainText(/symposium/i)
  await expect(conversation).toContainText(/\[\d/) // inline citation like [1]

  await page.getByLabel('Show sources').first().click()
  await expect(page.getByText(/Sources \(\d+\)/)).toBeVisible()

  // Reloading the conversation shows both turns from the database
  const url = page.url()
  await page.reload()
  await expect(page).toHaveURL(url)
  await expect(conversation).toContainText('What is MAGISTECH 2026?')
  await expect(conversation).toContainText(/symposium/i)
})

test('rename a conversation', async ({ page }) => {
  await signIn(page)
  await ask(page, 'What does the Training and Placement cell do?')
  await page.getByLabel('Edit title').click()
  const title = `Placements ${Date.now()}`
  await page.getByLabel('Conversation title').fill(title)
  await page.getByLabel('Conversation title').press('Enter')
  await expect(page.getByRole('heading', { name: title })).toBeVisible()
  await page.reload()
  await expect(page.getByRole('heading', { name: title })).toBeVisible()
})

import { expect, test } from '@playwright/test'
import { ask, signIn } from './helpers'

test("another user cannot open someone else's conversation", async ({ browser }) => {
  const owner = await (await browser.newContext()).newPage()
  await signIn(owner, 'USER')
  // Unique wording, so it can't match an example prompt on the empty chat screen
  const question = `Private question ${Date.now()}: when does the library open on Saturdays?`
  await ask(owner, question)
  const privateUrl = owner.url()
  expect(privateUrl).toMatch(/\/chat\/[0-9a-f-]{36}/)

  const other = await (await browser.newContext()).newPage()
  await signIn(other, 'ADMIN')
  await other.goto(privateUrl)
  await expect(other).toHaveURL(/\/chat$/)
  await expect(other.getByText(question)).toHaveCount(0)
})

test('admin page is for admins only', async ({ browser }) => {
  const student = await (await browser.newContext()).newPage()
  await signIn(student, 'USER')
  await student.goto('/admin')
  await expect(student).toHaveURL(/\/chat/)
  await student.goto('/documents')
  await expect(student.getByText('Share with everyone')).toHaveCount(0)

  const admin = await (await browser.newContext()).newPage()
  await signIn(admin, 'ADMIN')
  await admin.goto('/admin')
  await expect(admin).toHaveURL(/\/admin/)
  await admin.goto('/documents')
  await expect(admin.getByText('Share with everyone')).toBeVisible()
})

import { expect, test } from '@playwright/test'
import { signIn } from './helpers'

test('upload a document, see it processed as private, then delete it', async ({ page }) => {
  const name = `e2e-notes-${Date.now()}.txt`
  await signIn(page)
  await page.getByRole('link', { name: 'Documents' }).click()

  await page.locator('input[type="file"]').setInputFiles({
    name,
    mimeType: 'text/plain',
    buffer: Buffer.from('The e2e study group meets every Thursday at 5 PM in Room 204.'),
  })
  await page.getByRole('button', { name: /upload/i }).last().click()

  const deleteButton = page.getByLabel(`Delete ${name}`)
  const row = page.locator('div').filter({ has: deleteButton }).filter({ hasText: name }).last()
  await expect(row.getByText('Ready')).toBeVisible({ timeout: 90_000 })
  await expect(row.getByText('Private')).toBeVisible()

  // After a successful upload the form is cleared, so the name only appears in the list
  await expect(page.getByLabel('Remove file')).toHaveCount(0)

  await deleteButton.click()
  await expect(deleteButton).toHaveCount(0)
  await expect(page.getByText(name)).toHaveCount(0)
})

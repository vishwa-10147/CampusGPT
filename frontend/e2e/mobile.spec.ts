import { expect, test } from '@playwright/test'
import { signIn } from './helpers'

test('phone-width layout: menu opens and the chat box is usable', async ({ page }) => {
  await signIn(page)
  const nav = page.getByRole('navigation', { name: 'Main navigation' })
  await expect(nav).not.toBeInViewport()

  await page.getByLabel('Open menu').click()
  await expect(nav).toBeInViewport()
  await page.getByLabel('Close sidebar').click()
  await expect(nav).not.toBeInViewport()

  await expect(page.getByLabel('Message input')).toBeVisible()
  // Nothing should force sideways scrolling
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
  expect(overflow).toBeLessThanOrEqual(1)
})

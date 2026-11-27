import { expect, test } from './fixtures';

test.beforeEach(({}, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium-1280', 'The language follows the address at any width.');
});

test('English addresses serve English pages, and the switch opens the same page in the other language (spec 050)', async ({ page }) => {
  await page.goto('/en/subscribe');
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  await expect(page.getByRole('heading', { level: 1, name: 'Invention news for investors' })).toBeVisible();
  await page.getByLabel(/Email/).fill('carry@example.com');

  await page.getByRole('link', { name: /View this page in Indonesian/ }).click();

  await expect(page).toHaveURL(/\/langganan$/);
  await expect(page.locator('html')).toHaveAttribute('lang', 'id');
  await expect(page.getByRole('heading', { level: 1, name: 'Kabar inovasi untuk investor' })).toBeVisible();
  await expect(page.getByLabel(/Email/)).toHaveValue('carry@example.com');
  expect(page.url()).not.toContain('carry');
});

test('the service answers an English page in English', async ({ page }) => {
  await page.goto('/en/subscribe/confirm?token=tidak-ada-token-ini-1234');
  await page.getByRole('button', { name: 'Confirm subscription' }).click();
  await expect(page.getByText('This link was already used or has expired. Subscribe again for a new link.')).toBeVisible();
});

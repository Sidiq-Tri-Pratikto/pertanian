import { expect, makeInvention, signUp, test } from './fixtures';

test.beforeEach(({}, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium-360', 'The list and the open result take turns on a phone.');
});

test('a phone opens one result from the list by keyboard and "Kembali ke hasil" returns focus to the same row', async ({ page }) => {
  await signUp(page, 'mitra');
  await makeInvention(page, true);
  await page.goto('/discover?type=inventions');

  const row = page.locator('.tr-listrow').first();
  const link = row.getByRole('link');
  const title = (await link.textContent()) ?? '';
  await link.focus();
  await page.keyboard.press('Enter');

  await expect(page).toHaveURL(/selected=/);
  await expect(page.getByRole('region', { name: `Rincian: ${title}` })).toBeFocused();
  await expect(page.locator('.tr-listdetail__list')).toBeHidden();

  await page.getByRole('link', { name: 'Kembali ke hasil' }).focus();
  await page.keyboard.press('Enter');

  await expect(page).not.toHaveURL(/selected=/);
  await expect(page.locator('.tr-listrow').filter({ hasText: title }).first()).toBeFocused();
});

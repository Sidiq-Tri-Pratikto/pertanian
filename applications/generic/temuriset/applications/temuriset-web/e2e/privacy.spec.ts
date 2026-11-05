import { readFile } from 'node:fs/promises';

import { expect, makePartnerProfile, signUp, test, WEB_ORIGIN } from './fixtures';

test('reports a partner privately, then reads the case again', async ({ page, browser }, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium-1280', 'This journey runs at one width.');
  const partner = await browser.newContext({ baseURL: WEB_ORIGIN });
  try {
    const profile = await partner.newPage();
    await signUp(profile, 'mitra', 'Mitra Uji');
    const party = await makePartnerProfile(profile);
    await signUp(page, 'inovator');
    await page.goto(`/partners/${party}`);
    await page.getByRole('link', { name: 'Laporkan', exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`lapor=PARTNER_PROFILE&objek=${party}#laporkan$`));
    const report = page.getByRole('region', { name: 'Laporkan masalah' });
    await expect(report.getByText('Profil mitra', { exact: true })).toBeVisible();
    await report.getByRole('button', { name: 'Kirim laporan' }).click();
    await expect(report.getByRole('group', { name: 'Masih ada yang perlu diperbaiki' })).toBeFocused();
    await report.getByRole('textbox', { name: /Alasan laporan/ }).fill('Klaim ini perlu diperiksa.');
    await report.getByRole('button', { name: 'Kirim laporan' }).click();
    await expect(report.getByRole('status')).toContainText(/Laporan TR-\d+ diterima/);
    await page.reload();
    await expect(report.getByRole('listitem')).toContainText(/TR-\d+ · Diterima/);
  } finally {
    await partner.close();
  }
});

test('shows retained categories and downloads only the signed-in account export', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium-1280', 'This journey runs at one width.');
  const email = await signUp(page, 'inovator');
  await page.goto('/settings');
  const privacy = page.getByRole('region', { name: 'Permintaan privasi' });
  await privacy.getByRole('button', { name: 'Minta penghapusan data' }).click();
  await page.getByRole('dialog').getByRole('button', { name: 'Ajukan penghapusan' }).click();
  await expect(privacy.getByText('Tetap disimpan', { exact: true })).toBeVisible();
  await expect(privacy.getByText(/Cadangan layanan.*Cadangan hanya terhapus/)).toBeVisible();

  await privacy.getByRole('button', { name: 'Minta ekspor data' }).click();
  const downloadButton = privacy.getByRole('button', { name: 'Unduh ekspor' });
  await expect(downloadButton).toBeVisible();
  const saved = page.waitForEvent('download');
  await downloadButton.click();
  const downloaded = await saved;
  const path = await downloaded.path();
  const data = JSON.parse(await readFile(path!, 'utf8')) as { account: { email: string } };
  expect(data.account.email).toBe(email);

  await page.context().clearCookies();
  await downloadButton.click();
  await expect(privacy.getByRole('group', { name: 'Permintaan belum dapat diselesaikan' })).toBeVisible();
  await expect(page).toHaveURL(/\/settings$/);
});

test('privacy controls reflow at 320 px and the confirmation returns keyboard focus', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium-320', 'This test exercises the narrow viewport.');
  await signUp(page, 'inovator');
  await page.goto('/settings');
  await page.evaluate(() => { document.documentElement.style.fontSize = '200%'; });
  const open = page.getByRole('button', { name: 'Minta penghapusan data' });
  await open.focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading', { name: 'Ajukan penghapusan data?' })).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(open).toBeFocused();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  const widths = await page.evaluate(() => ({ viewport: document.documentElement.clientWidth, content: document.documentElement.scrollWidth }));
  expect(widths.content).toBeLessThanOrEqual(widths.viewport + 1);
});

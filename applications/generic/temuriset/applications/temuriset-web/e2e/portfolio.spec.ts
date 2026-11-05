import { COMPLETE_DRAFT, expect, makeInvention, signUp, test, WEB_ORIGIN } from './fixtures';

test.beforeEach(({}, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium-1280', 'Journeys run at one width.');
});

test('an inventor builds a profile in four steps and publishes version 1 (S05, AC12)', async ({ page }) => {
  await signUp(page, 'inovator');
  await page.goto('/inventions');
  await expect(page.getByText('Belum ada inovasi')).toBeVisible();
  await page.getByRole('button', { name: 'Tambah inovasi' }).click();
  await expect(page).toHaveURL(/\/edit\?step=1$/);

  await page.getByRole('textbox', { name: /Judul/ }).fill(COMPLETE_DRAFT.title);
  await page.getByRole('textbox', { name: /Masalah yang diselesaikan/ }).fill(COMPLETE_DRAFT.problem);
  await page.getByRole('textbox', { name: /Solusi saat ini/ }).fill(COMPLETE_DRAFT.solution);
  await page.getByRole('textbox', { name: /Siapa penggunanya/ }).fill(COMPLETE_DRAFT.intended_users);
  await page.getByRole('combobox', { name: /Tahap inovasi/ }).selectOption('PROTOTYPE');
  await page.getByRole('button', { name: 'Simpan dan lanjutkan' }).click();

  await expect(page.getByRole('heading', { level: 2, name: 'Yang sudah ada dan bukti' })).toBeFocused();
  await expect(page.getByText('Tersimpan', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Tambah fakta' }).click();
  await page.getByRole('textbox', { name: 'Apa yang diukur' }).fill('Kapasitas saring');
  await page.getByRole('textbox', { name: 'Nilai' }).fill('10');
  await page.getByRole('button', { name: 'Simpan dan lanjutkan' }).click();
  await expect(page.getByRole('heading', { level: 2, name: 'Dukungan dan cakupan keuangan' })).toBeFocused();
  await page.getByRole('button', { name: 'Simpan dan lanjutkan' }).click();

  await expect(page.getByRole('heading', { level: 3, name: COMPLETE_DRAFT.title })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Yang tetap privat' })).toBeVisible();
  await page.getByRole('button', { name: 'Terbitkan versi 1' }).click();

  await expect(page.getByText('Versi 1 sudah terbit')).toBeVisible();
  await expect(page.getByText('Saat ini', { exact: true }).first()).toBeVisible();
});

test('a failed save keeps every value and "Coba lagi" saves it once', async ({ page }) => {
  await signUp(page, 'inovator');
  const id = await makeInvention(page, false);
  let failures = 1;
  await page.route(`**/api/v1/inventions/${id}/draft`, (route) => (failures-- > 0 ? route.abort() : route.continue()));
  await page.goto(`/inventions/${id}/edit?step=1`);

  await page.getByRole('textbox', { name: /Judul/ }).fill('Saringan versi lapangan');
  await page.getByRole('button', { name: 'Simpan dan lanjutkan' }).click();
  await expect(page.getByText('Gagal menyimpan')).toBeVisible();
  await expect(page.getByRole('textbox', { name: /Judul/ })).toHaveValue('Saringan versi lapangan');
  await page.getByRole('button', { name: 'Coba lagi' }).click();

  await expect(page.getByText('Tersimpan', { exact: true })).toBeVisible();
  const saved = (await (await page.request.get(`/api/v1/inventions/${id}`)).json()) as { version: number; draft: { title: string } };
  expect(saved.draft.title).toBe('Saringan versi lapangan');
  expect(saved.version).toBe(3);
});

test('a draft changed in another tab shows the conflict and loads the current revision (UX-03)', async ({ page }) => {
  await signUp(page, 'inovator');
  const id = await makeInvention(page, false);
  await page.goto(`/inventions/${id}/edit?step=1`);
  const me = (await (await page.request.get('/api/v1/me')).json()) as { active_party_id: string };
  const current = (await (await page.request.get(`/api/v1/inventions/${id}`)).json()) as { version: number };
  await page.request.put(`/api/v1/inventions/${id}/draft`, {
    data: { acting_party_id: me.active_party_id, expected_version: current.version, ...COMPLETE_DRAFT, title: 'Diubah di tab lain' },
    headers: { Origin: WEB_ORIGIN, 'Idempotency-Key': 'other-tab' },
  });

  await page.getByRole('textbox', { name: /Judul/ }).fill('Ubahan saya');
  await page.getByRole('button', { name: 'Simpan dan lanjutkan' }).click();

  const conflict = page.getByRole('group', { name: 'Versi berubah' });
  await expect(conflict).toContainText('Ubahan saya');
  await conflict.getByRole('button', { name: 'Muat versi terbaru' }).click();
  await expect(page.getByRole('textbox', { name: /Judul/ })).toHaveValue('Diubah di tab lain');
});

test('a partner sees only the published projection and "Simpan inovasi"', async ({ page, browser }) => {
  await signUp(page, 'inovator');
  const id = await makeInvention(page, true);
  const partner = await (await browser.newContext()).newPage();
  await signUp(partner, 'mitra', 'Bima');

  await partner.goto(`/inventions/${id}`);

  await expect(partner.getByRole('heading', { level: 1, name: COMPLETE_DRAFT.title })).toBeVisible();
  await expect(partner.getByText('Dikelola Rani')).toBeVisible();
  await expect(partner.getByText(/Dokumen dibagikan per pitching/)).toBeVisible();
  await expect(partner.getByRole('button', { name: 'Simpan inovasi' })).toBeVisible();
  await expect(partner.getByText('Belum ditetapkan', { exact: false })).toBeVisible();
  await partner.context().close();
});

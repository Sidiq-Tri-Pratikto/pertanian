import { A1_MANDATE, expect, makeMandate, makePartnerProfile, signUp, test, WEB_ORIGIN } from './fixtures';

test.beforeEach(({}, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium-1280', 'Journeys run at one width.');
});

test('a partner edits, reviews and activates A1 version 2 (S09, SC-001)', async ({ page }) => {
  await signUp(page, 'mitra');
  await makePartnerProfile(page);
  const id = await makeMandate(page, true);

  await page.goto('/opportunities');
  const card = page.getByRole('article', { name: A1_MANDATE.title });
  await expect(card.getByText('Aktif', { exact: true })).toBeVisible();
  await expect(card.getByText('Versi 1')).toBeVisible();
  await card.getByRole('link', { name: /Ubah mandat/ }).click();
  await expect(page).toHaveURL(new RegExp(`/opportunities/${id}/edit$`));

  await page.getByRole('textbox', { name: /Hasil yang dicari/ }).fill('Prototipe teruji di dua lokasi.');
  await page.getByRole('textbox', { name: /Syarat baru/ }).fill('Pengalaman di desa');
  await page.getByRole('combobox', { name: 'Tahap berlaku', exact: true }).selectOption('DISCUSSION');
  await page.getByRole('combobox', { name: 'Cara pemeriksaan', exact: true }).selectOption('REVIEWER_CONFIRMED');
  await page.getByRole('button', { name: 'Tambah syarat' }).click();
  await expect(page.getByText('Ditinjau manual', { exact: true })).toBeVisible();
  await expect(page.getByText('Saat diskusi · Preferensi · Diperiksa peninjau')).toBeVisible();

  await page.getByRole('button', { name: 'Tinjau mandat' }).click();
  const review = page.getByRole('region', { name: 'Tinjau mandat' });
  await expect(page.getByRole('heading', { name: 'Tinjau mandat' })).toBeFocused();
  await expect(review.getByText('Prototipe teruji di dua lokasi.')).toBeVisible();
  await expect(review.getByText('Pengalaman di desa')).toBeVisible();
  await page.getByRole('button', { name: 'Aktifkan versi 2' }).click();

  await expect(page).toHaveURL(/\/opportunities\?aktif=2$/);
  await expect(page.getByText('Mandat aktif sebagai versi 2. Pitching yang sudah terkirim memakai versinya sendiri.')).toBeVisible();
  await expect(page.getByRole('article', { name: A1_MANDATE.title }).getByText('Versi 2')).toBeVisible();
  const earlier = (await (await page.request.get(`/api/v1/opportunities/${id}/versions/1`)).json()) as { outcome: string };
  expect(earlier.outcome).toBe(A1_MANDATE.outcome);
});

test('a draft goes live as version 1 through the review', async ({ page }) => {
  await signUp(page, 'mitra');
  await makePartnerProfile(page);
  const id = await makeMandate(page, false);

  await page.goto(`/opportunities/${id}/edit`);
  await page.getByRole('button', { name: 'Tinjau mandat' }).click();
  await page.getByRole('button', { name: 'Aktifkan versi 1' }).click();

  await expect(page).toHaveURL(/\/opportunities\?aktif=1$/);
  await expect(page.getByRole('article', { name: A1_MANDATE.title }).getByText('Aktif', { exact: true })).toBeVisible();
});

test('activating without a profile returns to the form with a link to create one', async ({ page }) => {
  await signUp(page, 'mitra');
  const id = await makeMandate(page, false);

  await page.goto(`/opportunities/${id}/edit`);
  await page.getByRole('button', { name: 'Tinjau mandat' }).click();
  await page.getByRole('button', { name: 'Aktifkan versi 1' }).click();

  await expect(page.getByRole('link', { name: 'Simpan profil mitra sebelum mengaktifkan mandat.' })).toBeVisible();
  await page.getByRole('link', { name: 'Buka profil mitra' }).click();
  await expect(page.getByRole('heading', { name: 'Profil mitra belum ada' })).toBeVisible();
});

test('a stale version keeps the edits and the next attempt targets the latest (TR.VersionConflict)', async ({ page }) => {
  await signUp(page, 'mitra');
  const party = await makePartnerProfile(page);
  const id = await makeMandate(page, true);
  await page.goto(`/opportunities/${id}/edit`);
  await page.getByRole('textbox', { name: /Judul mandat/ }).fill('Isian saya');
  await page.getByRole('button', { name: 'Tinjau mandat' }).click();

  const current = (await (await page.request.get(`/api/v1/opportunities/${id}`)).json()) as { version: number };
  const elsewhere = await page.request.put(`/api/v1/opportunities/${id}`, {
    data: { acting_party_id: party, expected_version: current.version, ...A1_MANDATE, title: 'Tab lain' },
    headers: { Origin: WEB_ORIGIN, 'Idempotency-Key': `tab-${id}` },
  });
  expect(elsewhere.status(), await elsewhere.text()).toBe(200);

  await page.getByRole('button', { name: 'Aktifkan versi 2' }).click();
  const conflict = page.getByRole('group', { name: 'Versi berubah' });
  await expect(conflict.getByText('Isian saya', { exact: true })).toBeVisible();
  await conflict.getByRole('button', { name: 'Pakai versi terbaru, pertahankan isian saya' }).click();
  await page.getByRole('button', { name: 'Aktifkan versi 3' }).click();

  await expect(page).toHaveURL(/\/opportunities\?aktif=3$/);
  await expect(page.getByRole('article', { name: 'Isian saya' })).toBeVisible();
});

test('another party reads a partner, and following its external route is a recorded handoff, not a pitch (S08, AC24)', async ({ page, browser }) => {
  await signUp(page, 'mitra');
  const party = await makePartnerProfile(page, { contact_route: 'EXTERNAL', external_url: 'https://example.org/formulir-demo' });

  const other = await browser.newContext({ baseURL: WEB_ORIGIN });
  const inventor = await other.newPage();
  await inventor.route('https://example.org/**', (route) => route.fulfill({ status: 200, body: 'formulir mitra' }));
  await signUp(inventor, 'inovator', 'Bima');
  await inventor.goto(`/partners/${party}`);

  await expect(inventor.getByText(/Tautan ini membuka situs lain dan bukan pitching yang terkirim/)).toBeVisible();
  await expect(inventor.getByRole('button', { name: 'Simpan profil' })).toHaveCount(0);
  const recorded = inventor.waitForResponse((response) => response.url().endsWith(`/api/v1/partners/${party}/handoffs`));
  const [opened] = await Promise.all([inventor.waitForEvent('popup'), inventor.getByRole('link', { name: /Buka formulir mitra/ }).click()]);
  expect(opened.url()).toContain('example.org/formulir-demo');
  const handoff = await recorded;
  expect(handoff.status()).toBe(201);
  expect(((await handoff.json()) as { submitted: boolean }).submitted).toBe(false);
  await other.close();
});

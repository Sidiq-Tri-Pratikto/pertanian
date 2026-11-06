import { expect, makeInvention, makeSupportRequest, signUp, test } from './fixtures';

test.beforeEach(({}, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium-1280', 'Journeys run at one width.');
});

test('an inventor states F01 from step 3 with labelled money, and a bad range keeps both values (S06, UX-05)', async ({ page }) => {
  await signUp(page, 'inovator');
  const invention = await makeInvention(page, true);
  await page.goto(`/inventions/${invention}/edit?step=3`);
  await page.getByRole('link', { name: 'Nyatakan kebutuhan Dukungan Proyek' }).click();
  await expect(page).toHaveURL(new RegExp(`/support-requests\\?invention=${invention}$`));
  await page.getByRole('button', { name: 'Tambah kebutuhan dukungan' }).click();
  await expect(page).toHaveURL(/\/support-requests\/[0-9a-f-]{36}$/);

  await page.getByRole('textbox', { name: /Hasil yang ingin dicapai/ }).fill('Validasi prototipe enam bulan');
  await page.getByRole('checkbox', { name: 'Pendanaan proyek' }).check();
  await page.getByRole('combobox', { name: 'Mata uang' }).selectOption('USD');
  await page.getByRole('textbox', { name: /Biaya minimum/ }).fill('20000');
  await page.getByRole('textbox', { name: /Biaya maksimum/ }).fill('30000');
  await page.getByRole('textbox', { name: /^Periode/ }).fill('6 bulan');
  await page.getByRole('textbox', { name: /Cakupan biaya/ }).fill('biaya pilot enam bulan');
  await page.getByRole('button', { name: 'Simpan kebutuhan' }).click();

  const summary = page.getByRole('region', { name: 'Ringkasan' });
  await expect(summary.getByText('Versi 2')).toBeVisible();
  await expect(summary.getByText('Dukungan Proyek')).toBeVisible();
  await expect(summary.getByText('USD 20.000–30.000')).toBeVisible();
  await expect(summary.getByText('selama 6 bulan')).toBeVisible();
  await expect(summary.getByText('Cakupan: biaya pilot enam bulan')).toBeVisible();

  await page.getByRole('textbox', { name: /Biaya minimum/ }).fill('30000');
  await page.getByRole('textbox', { name: /Biaya maksimum/ }).fill('20000');
  await page.getByRole('button', { name: 'Simpan kebutuhan' }).click();
  await expect(page.getByRole('group', { name: 'Masih ada yang perlu diperbaiki' })).toBeFocused();
  await expect(page.getByRole('link', { name: 'Biaya maksimum tidak boleh lebih kecil dari biaya minimum.' })).toBeVisible();
  await expect(page.getByRole('textbox', { name: /Biaya minimum/ })).toHaveValue('30000');
  await expect(page.getByRole('textbox', { name: /Biaya maksimum/ })).toHaveValue('20000');
});

test('an open range reads "Belum ditentukan" and Beranda asks to complete it', async ({ page }) => {
  await signUp(page, 'inovator');
  const id = await makeSupportRequest(page, { min: null, max: null, unknown_reason: 'not_determined' });
  await page.goto('/home');

  await expect(page.getByRole('heading', { name: 'Lengkapi kisaran biaya pilot untuk kebutuhan ini' })).toBeVisible();
  await page.getByRole('link', { name: /^Kerjakan sekarang/ }).click();

  await expect(page).toHaveURL(new RegExp(`/support-requests/${id}$`));
  await expect(page.getByRole('region', { name: 'Ringkasan' }).getByText('Belum ditentukan')).toBeVisible();
});

test('saving a need opened with ?return= goes back to that address', async ({ page }) => {
  await signUp(page, 'inovator');
  const id = await makeSupportRequest(page);
  await page.goto(`/support-requests/${id}?return=${encodeURIComponent('/discover?tahap=PROTOTYPE')}`);

  await page.getByRole('button', { name: 'Simpan kebutuhan' }).click();

  await expect(page).toHaveURL(/\/discover\?tahap=PROTOTYPE$/);
});

test('J02: one raise for two inventions shows target and contribution apart, and Back returns to it (S07, UX-06)', async ({ page }) => {
  await signUp(page, 'inovator', 'Dewi');
  const loop = await makeInvention(page, true, 'LoopMaterial');
  await makeInvention(page, true, 'ReFormPress');
  await page.goto('/support-requests');
  await page.getByRole('button', { name: 'Mulai pendanaan perusahaan' }).click();
  await expect(page).toHaveURL(/\/funding-requests\/[0-9a-f-]{36}\/edit$/);

  await page.getByRole('combobox', { name: 'Status perusahaan' }).selectOption('EXISTING_ENTITY');
  await page.getByRole('textbox', { name: /Nama badan hukum/ }).fill('Demo Circular Materials Ltd');
  await page.getByRole('combobox', { name: /Tahap pendanaan perusahaan/ }).selectOption('pre_seed');
  await page.getByRole('combobox', { name: 'Bentuk pendanaan' }).selectOption('equity');
  await page.getByRole('combobox', { name: 'Mata uang' }).selectOption('USD');
  await page.getByRole('textbox', { name: /Target Pendanaan/ }).fill('500000');
  await page.getByRole('textbox', { name: /batas bawah/ }).fill('50000');
  await page.getByRole('textbox', { name: /batas atas/ }).fill('100000');
  await page.getByRole('checkbox', { name: 'Menerima pendanaan sebagian' }).check();
  await page.getByRole('checkbox', { name: 'LoopMaterial' }).check();
  await page.getByRole('checkbox', { name: 'ReFormPress' }).check();
  await page.getByRole('button', { name: 'Simpan pendanaan' }).click();

  await expect(page).toHaveURL(/\/funding-requests\/[0-9a-f-]{36}$/);
  const card = page.getByRole('article');
  await expect(card.getByRole('heading', { name: 'Demo Circular Materials Ltd' })).toBeVisible();
  await expect(card.getByText('Target Pendanaan')).toBeVisible();
  await expect(card.getByText('USD 500.000', { exact: true })).toBeVisible();
  await expect(card.getByText('Kisaran kontribusi per investor')).toBeVisible();
  await expect(card.getByText('USD 50.000–100.000')).toBeVisible();
  await expect(card.getByText('2 inovasi terkait')).toBeVisible();
  const raise = page.url();

  await card.getByRole('link', { name: 'LoopMaterial, versi 1' }).click();
  await expect(page).toHaveURL(new RegExp(`/inventions/${loop}$`));
  await page.goBack();

  await expect(page).toHaveURL(raise);
  await expect(page.getByRole('article').getByText('2 inovasi terkait')).toBeVisible();
});

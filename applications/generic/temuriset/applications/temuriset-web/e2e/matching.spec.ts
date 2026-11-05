import { A1_MANDATE, expect, makePartnerProfile, makeSupportRequest, signUp, test, uniqueEmail, WEB_ORIGIN } from './fixtures';

test.beforeEach(({}, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium-1280', 'Journeys run at one width.');
});

test('J01: from Beranda to "Siapkan pitching", repairing the open range on the way (S03, S10)', async ({ page, browser }) => {
  // A partner with one active mandate that compares budgets; its title is unique, so other runs never collide.
  const title = `Validasi J01 ${uniqueEmail('m').split('@')[0]}`;
  const partner = await browser.newPage({ baseURL: WEB_ORIGIN });
  await signUp(partner, 'mitra', 'Mitra J01');
  const partyId = await makePartnerProfile(partner);
  const created = await partner.request.post('/api/v1/opportunities', {
    data: {
      acting_party_id: partyId,
      ...A1_MANDATE,
      title,
      sectors: ['Air bersih'],
      keywords: ['air', 'prototipe'],
      requirements: [
        ...A1_MANDATE.requirements,
        { label: 'Kisaran biaya pilot', field: 'budget', operator: 'range_overlap', value: null, reason: 'Biaya dibandingkan pada cakupan dan periode yang sama.' },
      ],
    },
    headers: { Origin: WEB_ORIGIN, 'Idempotency-Key': uniqueEmail('op') },
  });
  expect(created.status(), await created.text()).toBe(201);
  const mandate = (await created.json()) as { id: string; version: number };
  const activated = await partner.request.post(`/api/v1/opportunities/${mandate.id}/activate`, {
    data: { acting_party_id: partyId, expected_version: mandate.version },
    headers: { Origin: WEB_ORIGIN, 'Idempotency-Key': uniqueEmail('oa') },
  });
  expect(activated.status(), await activated.text()).toBe(200);
  await partner.close();

  // F01-GAP: Rani's need with the range still open, active.
  await signUp(page, 'inovator');
  const need = await makeSupportRequest(page, { min: null, max: null, unknown_reason: 'not_determined' });
  const me = (await (await page.request.get('/api/v1/me')).json()) as { active_party_id: string };
  const moved = await page.request.post(`/api/v1/support-requests/${need}/activate`, {
    data: { acting_party_id: me.active_party_id, expected_version: 1 },
    headers: { Origin: WEB_ORIGIN, 'Idempotency-Key': uniqueEmail('sa') },
  });
  expect(moved.status(), await moved.text()).toBe(200);

  await page.goto('/home');
  await page.getByRole('link', { name: 'Temukan Investor/Mitra' }).first().click();
  await page.getByRole('link', { name: 'Lihat kecocokan untuk kebutuhan Anda' }).click();
  await expect(page).toHaveURL(new RegExp(`/matches\\?source=SUPPORT_REQUEST:${need}$`));

  const card = page.getByRole('article', { name: title });
  await expect(card.getByText('Perlu konfirmasi')).toBeVisible();
  await card.getByRole('link', { name: 'Lengkapi kisaran biaya' }).click();
  await expect(page).toHaveURL(new RegExp(`/support-requests/${need}\\?return=`));

  await page.getByRole('textbox', { name: /Durasi \(bulan\)/ }).fill('6');
  await page.getByRole('combobox', { name: 'Bila kisaran belum diketahui' }).selectOption('');
  await page.getByRole('combobox', { name: 'Mata uang' }).selectOption('USD');
  await page.getByRole('textbox', { name: /Biaya minimum/ }).fill('20000');
  await page.getByRole('textbox', { name: /Biaya maksimum/ }).fill('30000');
  await page.getByRole('textbox', { name: /^Periode/ }).fill('6 bulan');
  await page.getByRole('textbox', { name: /Cakupan biaya/ }).fill('biaya pilot enam bulan');
  await page.getByRole('button', { name: 'Simpan kebutuhan' }).click();

  await expect(page).toHaveURL(new RegExp(`/matches\\?source=SUPPORT_REQUEST:${need}$`));
  await expect(card.getByText('Kecocokan kuat')).toBeVisible();
  await expect(card.getByText('Siap dikirim')).toBeVisible();
  await card.getByText('Tentang kisaran kecocokan').click();
  await expect(card.getByText(/bukan peluang pendanaan/)).toBeVisible();
  await expect(card.getByRole('link', { name: 'Siapkan pitching' })).toBeVisible();
});

test('discovery keeps its filters in the address, so Back returns to them', async ({ page }) => {
  await signUp(page, 'mitra');
  await page.goto('/discover?type=inventions');
  await page.getByRole('searchbox', { name: /Kata kunci/ }).fill('water filter');
  await page.getByRole('combobox', { name: 'Sektor' }).selectOption('Pertanian');
  await page.getByRole('button', { name: 'Terapkan' }).click();
  await expect(page).toHaveURL(/q=water\+filter/);
  await expect(page.getByRole('link', { name: 'Hapus semua filter' }).first()).toBeVisible();

  await page.goto('/settings');
  await page.goBack();

  await expect(page.getByRole('searchbox', { name: /Kata kunci/ })).toHaveValue('water filter');
  await expect(page.getByRole('combobox', { name: 'Sektor' })).toHaveValue('Pertanian');
});

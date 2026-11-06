import { expect, makeInvention, makePartnerProfile, signUp, test, uniqueEmail, WEB_ORIGIN } from './fixtures';

test.beforeEach(({}, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium-1280', 'Journeys run at one width.');
});

const HEADERS = { Origin: WEB_ORIGIN };

test('J02: Bima pitches one company raise to an equity mandate, and the second link opens the same pitch (S10, S11)', async ({ page, browser }) => {
  // Investor J02: an equity mandate that compares the contribution per investor and needs an incorporated company.
  const title = `Ekuitas J02 ${uniqueEmail('m').split('@')[0]}`;
  const investor = await browser.newPage({ baseURL: WEB_ORIGIN });
  await signUp(investor, 'mitra', 'Investor J02');
  const investorParty = await makePartnerProfile(investor, { sectors: ['Air bersih'], stages: ['PROTOTYPE'], support_forms: ['Ekuitas'] });
  const reason = 'Mandat ini hanya untuk ekuitas pada badan usaha yang ada.';
  const created = await investor.request.post('/api/v1/opportunities', {
    data: {
      acting_party_id: investorParty,
      title,
      outcome: 'Investasi pada perusahaan pre-seed dengan prototipe.',
      included: 'Ekuitas',
      excluded: 'Pendanaan proyek',
      support: 'Investasi ekuitas',
      timing: 'Dibuka sampai 31 Maret 2027',
      accepted_stages: ['PROTOTYPE'],
      relationship_forms: ['EQUITY'],
      sectors: ['Air bersih'],
      keywords: ['air'],
      financial: { subject: 'investorCheck', basis: 'per_investment', min: '50000', max: '150000', currency: 'USD', period: 'per investasi' },
      requirements: [
        { label: 'Bentuk pendanaan', field: 'relationship', operator: 'equals', value: 'EQUITY', reason },
        { label: 'Badan usaha yang sudah berdiri', field: 'entity', operator: 'equals', value: 'IDENTIFIED', reason },
        { label: 'Kisaran kontribusi', field: 'contribution', operator: 'range_overlap', value: null, reason },
      ],
    },
    headers: { ...HEADERS, 'Idempotency-Key': uniqueEmail('op') },
  });
  expect(created.status(), await created.text()).toBe(201);
  const mandate = (await created.json()) as { id: string; version: number };
  const activated = await investor.request.post(`/api/v1/opportunities/${mandate.id}/activate`, {
    data: { acting_party_id: investorParty, expected_version: mandate.version },
    headers: { ...HEADERS, 'Idempotency-Key': uniqueEmail('oa') },
  });
  expect(activated.status(), await activated.text()).toBe(200);

  // Bima: one raise for an existing company, linked to two published inventions.
  await signUp(page, 'inovator', 'Bima');
  const first = await makeInvention(page, true, 'LoopMaterial');
  const second = await makeInvention(page, true, 'ReFormPress');
  const me = (await (await page.request.get('/api/v1/me')).json()) as { active_party_id: string };
  const entity = await page.request.post('/api/v1/legal-entities', {
    data: { acting_party_id: me.active_party_id, name: 'Demo Circular Materials Ltd', jurisdiction: 'Indonesia' },
    headers: { ...HEADERS, 'Idempotency-Key': uniqueEmail('le') },
  });
  expect(entity.status(), await entity.text()).toBe(201);
  const raise = await page.request.post('/api/v1/funding-requests', {
    data: {
      acting_party_id: me.active_party_id,
      subject_type: 'EXISTING_ENTITY',
      legal_entity_id: ((await entity.json()) as { id: string }).id,
      financing_stage: 'pre_seed',
      financing_form: 'equity',
      currency: 'USD',
      target_amount: '500000',
      desired_min: '50000',
      desired_max: '100000',
      intended_use: 'Mengembangkan dua inovasi perusahaan',
      invention_ids: [first, second],
    },
    headers: { ...HEADERS, 'Idempotency-Key': uniqueEmail('fr') },
  });
  expect(raise.status(), await raise.text()).toBe(201);
  const raiseId = ((await raise.json()) as { id: string }).id;
  const live = await page.request.post(`/api/v1/funding-requests/${raiseId}/activate`, {
    data: { acting_party_id: me.active_party_id, expected_version: 1 },
    headers: { ...HEADERS, 'Idempotency-Key': uniqueEmail('fa') },
  });
  expect(live.status(), await live.text()).toBe(200);

  await page.goto(`/matches?source=FUNDING_REQUEST:${raiseId}`);
  const card = page.getByRole('article', { name: title });
  await expect(card.getByText('Siap dikirim')).toBeVisible();
  await card.getByRole('link', { name: 'Siapkan pitching' }).click();

  await expect(page.getByText('Pendanaan Perusahaan: Demo Circular Materials Ltd, versi 2')).toBeVisible();
  await expect(page.getByText('LoopMaterial, versi 1; ReFormPress, versi 1')).toBeVisible();
  await expect(page.getByRole('textbox', { name: /Brief pitching/ })).toHaveValue(/kontribusi yang diinginkan USD 50\.000–100\.000 per investor/);
  await page.getByRole('button', { name: 'Kirim pitching kepada Investor J02' }).click();
  await expect(page).toHaveURL(/\/pitches\/[0-9a-f-]{36}\?terkirim=1$/);
  const pitchUrl = new URL(page.url()).pathname;

  // The second linked invention leads to the same raise, so preparing it again points at the pitch already sent.
  await page.goto(`/pitches/new?source=FUNDING_REQUEST:${raiseId}&target=${mandate.id}`);
  await expect(page.getByText('Pitching untuk mandat ini sudah ada', { exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Buka pitching yang ada' }).click();
  await expect(page).toHaveURL(new RegExp(`${pitchUrl}$`));

  await investor.goto('/pitches?box=masuk');
  await expect(investor.getByRole('link', { name: new RegExp(title) })).toHaveCount(1);
  await investor.close();
});

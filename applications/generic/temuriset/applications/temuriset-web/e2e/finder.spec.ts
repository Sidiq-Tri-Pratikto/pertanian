import AxeBuilder from '@axe-core/playwright';

import { A1_MANDATE, expect, makeInvention, makePartnerProfile, makeSupportRequest, signUp, test, uniqueEmail, WEB_ORIGIN } from './fixtures';

test.beforeEach(({}, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium-1280', 'Finder journey runs at desktop width.');
});

test('investor finder: choose an investor, inspect product x mandate matrix, breakdown, recommendations, and preview product (spec 057-059)', async ({
  page,
  browser,
}) => {
  const partnerName = `Mitra Finder ${uniqueEmail('f').split('@')[0]}`;
  const mandateTitle = `Mandat Air ${uniqueEmail('m').split('@')[0]}`;
  const partner = await browser.newPage({ baseURL: WEB_ORIGIN });
  await signUp(partner, 'mitra', partnerName);
  const partyId = await makePartnerProfile(partner);
  const created = await partner.request.post('/api/v1/opportunities', {
    data: {
      acting_party_id: partyId,
      ...A1_MANDATE,
      title: mandateTitle,
      sectors: ['Air dan sanitasi'],
      keywords: ['air', 'prototipe', 'desa'],
      requirements: [],
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

  // Inventor with one product that has an active need + one published product without a need (preview).
  await signUp(page, 'inovator');
  const needId = await makeSupportRequest(page, {
    min: '20000',
    max: '30000',
    currency: 'USD',
    basis: 'total_period',
    period: '6 bulan',
    scope: 'biaya pilot enam bulan',
  });
  const me = (await (await page.request.get('/api/v1/me')).json()) as { active_party_id: string };
  await page.request.post(`/api/v1/support-requests/${needId}/activate`, {
    data: { acting_party_id: me.active_party_id, expected_version: 1 },
    headers: { Origin: WEB_ORIGIN, 'Idempotency-Key': uniqueEmail('sa') },
  });
  await makeInvention(page, true);

  // Wait for discovery projection consumer to index the partner.
  await page.goto(`/discover?type=partners&q=${encodeURIComponent(partnerName)}`);
  await expect(page.getByRole('link', { name: partnerName }).first()).toBeVisible({ timeout: 15000 });
  await page.getByRole('link', { name: partnerName }).first().click();

  await expect(page.getByRole('heading', { name: 'Kecocokan dengan produk Anda' })).toBeVisible();
  await expect(page.getByText('Pratinjau tanpa kebutuhan').first()).toBeVisible();

  // Expand the first product x mandate row to see 057 breakdown + 058 recommendations.
  const firstSummary = page.locator('#detail details.tr-disclosure > summary').first();
  await firstSummary.click();
  await expect(page.locator('#detail').getByRole('heading', { name: 'Rincian kecocokan' }).first()).toBeVisible();

  const { violations } = await new AxeBuilder({ page }).analyze();
  expect(violations.map((v) => `${v.id}: ${v.nodes.length}`)).toEqual([]);
});

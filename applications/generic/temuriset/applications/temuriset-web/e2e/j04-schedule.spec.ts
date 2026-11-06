import AxeBuilder from '@axe-core/playwright';

import { A1_MANDATE, expect, makePartnerProfile, makeSupportRequest, signUp, test, uniqueEmail, WEB_ORIGIN } from './fixtures';

test.beforeEach(({}, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium-1280', 'Journeys run at one width.');
});

const HEADERS = { Origin: WEB_ORIGIN };

/** A UTC day a few days ahead, so every slot is in the future; times below are its WIB wall clock (UTC+7). */
function day(offset: number): string {
  const date = new Date(Date.now() + offset * 24 * 3600 * 1000);
  return date.toISOString().slice(0, 10);
}

test('J04: propose, conflict, counter, conflict, confirm 10:00 UTC, then a replacement (S14, UX-13, UX-14)', async ({ page, browser }) => {
  const title = `Validasi J04 ${uniqueEmail('m').split('@')[0]}`;
  const partnerContext = await browser.newContext({ baseURL: WEB_ORIGIN });
  const partner = await partnerContext.newPage();
  await signUp(partner, 'mitra', 'Mitra J04');
  const partnerParty = await makePartnerProfile(partner);
  const created = await partner.request.post('/api/v1/opportunities', {
    data: { acting_party_id: partnerParty, ...A1_MANDATE, title, sectors: ['Air bersih'], keywords: ['air', 'prototipe'] },
    headers: { ...HEADERS, 'Idempotency-Key': uniqueEmail('op') },
  });
  expect(created.status(), await created.text()).toBe(201);
  const mandate = (await created.json()) as { id: string; version: number };
  await partner.request.post(`/api/v1/opportunities/${mandate.id}/activate`, {
    data: { acting_party_id: partnerParty, expected_version: mandate.version },
    headers: { ...HEADERS, 'Idempotency-Key': uniqueEmail('oa') },
  });

  await signUp(page, 'inovator');
  const need = await makeSupportRequest(page, { min: '20000', max: '30000', currency: 'USD', period: '6 bulan', scope: 'biaya pilot enam bulan' }, { months: 6 });
  const party = ((await (await page.request.get('/api/v1/me')).json()) as { active_party_id: string }).active_party_id;
  await page.request.post(`/api/v1/support-requests/${need}/activate`, {
    data: { acting_party_id: party, expected_version: 1 },
    headers: { ...HEADERS, 'Idempotency-Key': uniqueEmail('sa') },
  });
  const checked = (await (
    await page.request.post('/api/v1/pitches/preflight', {
      data: { acting_party_id: party, source_type: 'SUPPORT_REQUEST', source_id: need, opportunity_id: mandate.id },
      headers: HEADERS,
    })
  ).json()) as { token: string; brief: { text: string } };
  const sent = await page.request.post('/api/v1/pitches', {
    data: { acting_party_id: party, preflight_token: checked.token, brief: checked.brief.text, files: [] },
    headers: { ...HEADERS, 'Idempotency-Key': uniqueEmail('p') },
  });
  expect(sent.status(), await sent.text()).toBe(201);
  const pitchId = ((await sent.json()) as { pitch_id: string }).pitch_id;
  const approved = await partner.request.post(`/api/v1/pitches/${pitchId}/decisions`, {
    data: { acting_party_id: partnerParty, expected_version: 1, submission: 1, decision: 'APPROVE' },
    headers: { ...HEADERS, 'Idempotency-Key': uniqueEmail('d') },
  });
  expect(approved.status(), await approved.text()).toBe(200);

  // Mitra J04 already has "Agenda lain" from 09:00 to 10:00 UTC on that day.
  const d = day(3);
  const booked = await partner.request.post('/api/v1/dev/bookings', {
    data: { party_id: partnerParty, starts_at: `${d}T09:00:00Z`, ends_at: `${d}T10:00:00Z` },
    headers: HEADERS,
  });
  expect(booked.status(), await booked.text()).toBe(201);

  // Mitra J04 proposes 09:00, 11:00 and 13:00 UTC, entered as 16.00, 18.00 and 20.00 WIB.
  await partner.goto(`/pitches/${pitchId}?tab=jadwal`);
  await expect(partner.getByRole('heading', { name: 'Usulkan waktu pertemuan' }).first()).toBeVisible();
  await partner.getByLabel('Waktu 1').fill(`${d}T16:00`);
  await partner.getByLabel('Waktu 2').fill(`${d}T18:00`);
  await partner.getByLabel('Waktu 3').fill(`${d}T20:00`);
  await partner.getByRole('textbox', { name: /Agenda/ }).fill('Membahas rencana validasi enam bulan');
  await partner.getByRole('button', { name: 'Kirim usulan waktu' }).click();
  await expect(partner.getByRole('heading', { name: 'Usulan Anda, menunggu pihak lain memilih' })).toBeVisible();

  // Rani chooses 16.00 WIB: chosen is not booked, and confirming meets the other agenda.
  await page.goto(`/pitches/${pitchId}?tab=jadwal`);
  await expect(page.getByRole('heading', { name: 'Pilih waktu pertemuan' })).toBeVisible();
  await page.getByRole('radio', { name: /16\.00–17\.00 WIB/ }).check();
  await expect(page.getByText('Dipilih, belum dikonfirmasi')).toBeVisible();
  await page.getByRole('button', { name: 'Konfirmasi waktu' }).click();
  await expect(page.getByRole('alert').filter({ hasText: 'bentrok' })).toContainText('Waktu ini bentrok dengan jadwal peserta.');
  await expect(page.getByText('Membahas rencana validasi enam bulan')).toBeVisible();
  await page.getByRole('button', { name: 'Usulkan waktu lain' }).click();
  await expect(page.getByLabel('Waktu 1')).toHaveValue(`${d}T18:00`);
  await page.getByLabel('Waktu 1').fill(`${d}T16:30`);
  await page.getByLabel('Waktu 2').fill(`${d}T17:00`);
  await page.getByRole('textbox', { name: /Agenda/ }).fill('Membahas rencana validasi enam bulan');
  await page.getByRole('button', { name: 'Kirim usulan waktu' }).click();
  await expect(page.getByRole('heading', { name: 'Usulan Anda, menunggu pihak lain memilih' })).toBeVisible();

  // Mitra J04: 16.30 WIB overlaps the other agenda; 17.00 WIB (10:00 UTC) starts as it ends, so it books.
  await partner.reload();
  await partner.getByRole('radio', { name: /16\.30–17\.30 WIB/ }).check();
  await partner.getByRole('button', { name: 'Konfirmasi waktu' }).click();
  await expect(partner.getByRole('alert').filter({ hasText: 'bentrok' })).toBeVisible();
  await partner.getByRole('radio', { name: /17\.00–18\.00 WIB/ }).check();
  await partner.getByRole('button', { name: 'Konfirmasi waktu' }).click();
  await expect(partner.getByRole('heading', { name: 'Pertemuan dikonfirmasi' })).toBeVisible();
  await expect(partner.getByText('17.00–18.00 WIB (Asia/Jakarta)')).toBeVisible();
  await expect(partner.getByRole('link', { name: 'Unduh ICS' })).toHaveAttribute('href', /\/calendar\.ics$/);
  await partner.getByText('Lihat isi berkas ICS').click();
  await expect(partner.getByText(new RegExp(`DTSTART:${d.replaceAll('-', '')}T100000Z`))).toBeVisible();
  const { violations } = await new AxeBuilder({ page: partner }).analyze();
  expect(violations.map((violation) => violation.id)).toEqual([]);

  // Rani proposes a replacement the next day; the confirmed meeting stays until Mitra J04 accepts it.
  const next = day(4);
  await page.reload();
  await page.getByRole('button', { name: 'Usulkan jadwal pengganti' }).click();
  await page.getByLabel('Waktu 1').fill(`${next}T16:00`);
  await page.getByLabel('Waktu 2').fill(`${next}T18:00`);
  await page.getByRole('textbox', { name: /Agenda/ }).fill('Membahas rencana validasi enam bulan');
  await page.getByRole('button', { name: 'Kirim usulan pengganti' }).click();
  await expect(page.getByText(/pertemuan ini tetap berlaku sampai penggantinya dikonfirmasi/)).toBeVisible();

  await partner.reload();
  await expect(partner.getByRole('heading', { name: 'Usulan jadwal pengganti' })).toBeVisible();
  await expect(partner.getByRole('heading', { name: 'Pertemuan dikonfirmasi' })).toBeVisible();
  await partner.getByRole('radio', { name: /16\.00–17\.00 WIB/ }).check();
  await partner.getByRole('button', { name: 'Konfirmasi waktu' }).click();
  await expect(partner.getByRole('heading', { name: 'Usulan jadwal pengganti' })).toBeHidden();
  await expect(partner.getByText('16.00–17.00 WIB (Asia/Jakarta)')).toBeVisible();

  // Beranda: Rani's meeting is confirmed, and the discussion tab takes a message.
  await page.goto(`/pitches/${pitchId}?tab=diskusi`);
  await page.getByLabel('Pesan baru').fill('Sampai jumpa di pertemuan.');
  await page.getByRole('button', { name: 'Kirim pesan' }).click();
  await expect(page.getByText('Sampai jumpa di pertemuan.', { exact: true })).toBeVisible();
  await partnerContext.close();
});

test('Beranda leads with what waits on the partner (S02)', async ({ page }) => {
  await signUp(page, 'mitra', 'Mitra Kosong');
  await page.goto('/home');
  await expect(page.getByRole('heading', { level: 1, name: 'Beranda' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Belum ada yang perlu dikerjakan' })).toBeVisible();
});

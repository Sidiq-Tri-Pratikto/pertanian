import AxeBuilder from '@axe-core/playwright';
import type { Page } from '@playwright/test';

import { A1_MANDATE, expect, makePartnerProfile, makeSupportRequest, signUp, test, uniqueEmail, WEB_ORIGIN } from './fixtures';

test.beforeEach(({}, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium-1280', 'Journeys run at one width.');
});

const HEADERS = { Origin: WEB_ORIGIN };

/** Uploads a small PDF, or a new version of a document, and waits until the worker's scan makes it available. */
async function uploadPdf(page: Page, party: string, title: string, documentId?: string): Promise<string> {
  const content = Buffer.from(`%PDF-1.4\n${title} ${uniqueEmail('v')}\n%%EOF\n`);
  const intent = await page.request.post('/api/v1/documents/upload-intents', {
    data: { acting_party_id: party, title, kind: 'evidence', media_type: 'application/pdf', size_bytes: content.length, document_id: documentId ?? null },
    headers: HEADERS,
  });
  expect(intent.status(), await intent.text()).toBe(201);
  const { upload_url } = (await intent.json()) as { upload_url: string };
  const uploaded = await page.request.put(upload_url, { data: content, headers: { ...HEADERS, 'Content-Type': 'application/pdf' } });
  expect(uploaded.status(), await uploaded.text()).toBe(202);
  const { document_id } = (await uploaded.json()) as { document_id: string };
  await expect
    .poll(async () => {
      const document = (await (await page.request.get(`/api/v1/documents/${document_id}`)).json()) as { versions: { file_state: string }[] };
      return document.versions.every((version) => version.file_state === 'AVAILABLE');
    })
    .toBe(true);
  return document_id;
}

test('J03: revision with an honest answer, a new file version, resubmission, item review and approval (S12, S13)', async ({ page, browser }) => {
  // Mitra J03 and one active mandate; Rani's need F01 is sent to it through the API, as J01 already proves the screens.
  const title = `Validasi J03 ${uniqueEmail('m').split('@')[0]}`;
  // A page from its own context, so axe can analyze it.
  const partnerContext = await browser.newContext({ baseURL: WEB_ORIGIN });
  const partner = await partnerContext.newPage();
  await signUp(partner, 'mitra', 'Mitra J03');
  const partnerParty = await makePartnerProfile(partner);
  const created = await partner.request.post('/api/v1/opportunities', {
    data: { acting_party_id: partnerParty, ...A1_MANDATE, title, sectors: ['Air bersih'], keywords: ['air', 'prototipe'] },
    headers: { ...HEADERS, 'Idempotency-Key': uniqueEmail('op') },
  });
  expect(created.status(), await created.text()).toBe(201);
  const mandate = (await created.json()) as { id: string; version: number };
  const activated = await partner.request.post(`/api/v1/opportunities/${mandate.id}/activate`, {
    data: { acting_party_id: partnerParty, expected_version: mandate.version },
    headers: { ...HEADERS, 'Idempotency-Key': uniqueEmail('oa') },
  });
  expect(activated.status(), await activated.text()).toBe(200);

  await signUp(page, 'inovator');
  const need = await makeSupportRequest(page, { min: '20000', max: '30000', currency: 'USD', period: '6 bulan', scope: 'biaya pilot enam bulan' }, { months: 6 });
  const me = (await (await page.request.get('/api/v1/me')).json()) as { active_party_id: string };
  const party = me.active_party_id;
  const live = await page.request.post(`/api/v1/support-requests/${need}/activate`, {
    data: { acting_party_id: party, expected_version: 1 },
    headers: { ...HEADERS, 'Idempotency-Key': uniqueEmail('sa') },
  });
  expect(live.status(), await live.text()).toBe(200);
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

  // Mitra J03: the list says it is their turn; the filter survives opening the pitch and coming back.
  await partner.goto('/pitches?box=masuk');
  await partner.getByRole('combobox', { name: 'Giliran' }).selectOption('anda');
  await partner.getByRole('button', { name: 'Terapkan' }).click();
  await expect(partner).toHaveURL(/giliran=anda/);
  const row = partner.getByRole('listitem').filter({ hasText: title });
  await expect(row.getByText('Menunggu Anda')).toBeVisible();
  await row.getByRole('link', { name: /Buka pitching/ }).click();
  await expect(partner).toHaveURL(new RegExp(`/pitches/${pitchId}$`));
  await partner.goBack();
  await expect(partner.getByRole('combobox', { name: 'Giliran' })).toHaveValue('anda');
  await partner.goto(`/pitches/${pitchId}`);

  // Round 1: a required pilot-budget question and an optional planned-feature question.
  await partner.getByRole('link', { name: 'Minta revisi' }).click();
  await expect(partner).toHaveURL(new RegExp(`/pitches/${pitchId}\\?tab=revisi$`));
  await expect(partner.getByRole('tab', { name: 'Revisi' })).toHaveAttribute('aria-selected', 'true');
  await partner.getByRole('textbox', { name: /Kategori/ }).fill('Anggaran');
  await partner.getByRole('textbox', { name: /^Pertanyaan/ }).fill('Apakah biaya pilot sudah mencakup pengujian di dua lokasi?');
  await partner.getByRole('textbox', { name: /^Alasan/ }).fill('Kami perlu memastikan cakupan biaya sebelum menyiapkan uji.');
  await partner.getByRole('button', { name: 'Tambah butir' }).click();
  const second = partner.getByRole('group', { name: 'Butir 2' });
  await second.getByRole('textbox', { name: /Kategori/ }).fill('Fitur');
  await second.getByRole('textbox', { name: /^Pertanyaan/ }).fill('Kapan kapasitas 20 L/jam direncanakan tersedia?');
  await second.getByRole('textbox', { name: /^Alasan/ }).fill('Membantu kami menyusun tahap uji berikutnya.');
  await partner.getByRole('button', { name: 'Kirim permintaan revisi kepada Rani' }).click();
  await expect(partner.getByRole('heading', { name: 'Menunggu jawaban revisi' })).toBeVisible();
  await expect(partner.getByText('Jawaban terlihat setelah pengirim mengirim ulang.')).toBeVisible();

  // Rani: a test report in two versions, so version 2 can be chosen on purpose.
  const report = await uploadPdf(page, party, 'Rincian biaya per lokasi');
  await uploadPdf(page, party, 'Rincian biaya per lokasi', report);
  await page.goto('/pitches');
  await page.getByRole('listitem').filter({ hasText: title }).getByRole('link', { name: /Buka pitching/ }).click();
  await expect(page.getByRole('heading', { name: 'Jawab permintaan revisi' })).toBeVisible();
  await page.getByRole('tab', { name: 'Revisi' }).click();
  await expect(page).toHaveURL(/tab=revisi/);

  await page.getByRole('button', { name: 'Kirim ulang kepada Mitra J03' }).click();
  await expect(page.getByRole('group', { name: 'Jawaban wajib belum tersimpan' })).toBeFocused();

  const required = page.getByRole('article').filter({ hasText: 'Pertanyaan 1' });
  await required.getByRole('radio', { name: /Belum dapat dipenuhi/ }).check();
  await required.getByRole('textbox', { name: 'Penjelasan' }).fill('Biaya dua lokasi belum dapat kami penuhi; rincian satu lokasi terlampir.');
  await required.getByRole('checkbox', { name: 'Rincian biaya per lokasi, versi 2' }).check();
  await page.getByRole('button', { name: 'Simpan jawaban 1' }).click();
  await expect(page.getByText('Tersimpan', { exact: true })).toBeVisible();
  await page.getByRole('group', { name: 'Berkas untuk kiriman ini' }).getByRole('checkbox', { name: 'Rincian biaya per lokasi, versi 2' }).check();
  await page.getByRole('button', { name: 'Kirim ulang kepada Mitra J03' }).click();
  await expect(page.getByRole('heading', { name: 'Pitching Anda sedang menunggu keputusan' })).toBeVisible();
  await expect(page.getByText('Putaran 1 · untuk kiriman 1')).toBeVisible();

  // Mitra J03: the answer is visible now; accepting it approves nothing, approval is its own dialog.
  await partner.goto(`/pitches/${pitchId}?tab=revisi`);
  await expect(partner.getByText('Belum dapat dipenuhi', { exact: true })).toBeVisible();
  await partner.getByRole('button', { name: 'Terima jawaban 1' }).click();
  await expect(partner.getByText('Tinjauan: Diterima')).toBeVisible();
  await expect(partner.getByText('Terkirim', { exact: true })).toBeVisible();
  await partner.getByRole('tab', { name: 'Dokumen' }).click();
  await expect(partner.getByText('Rincian biaya per lokasi, versi 2 · kiriman 2')).toBeVisible();
  const { violations } = await new AxeBuilder({ page: partner }).analyze();
  expect(violations.map((violation) => violation.id)).toEqual([]);

  const approve = partner.getByRole('button', { name: 'Setujui untuk diskusi' });
  await approve.click();
  const dialog = partner.getByRole('dialog', { name: 'Setujui untuk diskusi' });
  await expect(dialog.getByText('Persetujuan ini membuka diskusi; belum merupakan pendanaan atau kerja sama.')).toBeVisible();
  await expect(dialog.getByText('Anda bertindak sebagai Mitra J03.')).toBeVisible();
  await partner.keyboard.press('Escape');
  await expect(dialog).toBeHidden();
  await expect(approve).toBeFocused();
  await approve.click();
  await dialog.getByRole('button', { name: 'Setujui untuk diskusi' }).click();
  await expect(partner.getByText('Disetujui untuk diskusi', { exact: true })).toBeVisible();
  await expect(partner.getByRole('heading', { name: 'Usulkan waktu pertemuan' }).first()).toBeVisible();

  // Rani: both submissions and round 1 stay in the history.
  await page.goto(`/pitches/${pitchId}?tab=riwayat`);
  await expect(page.getByText(/^Kiriman 1 · /)).toBeVisible();
  await expect(page.getByText(/^Kiriman 2 · /)).toBeVisible();
  await expect(page.getByText(/^Disetujui untuk diskusi · kiriman 2/)).toBeVisible();
  await partnerContext.close();
});

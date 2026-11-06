import AxeBuilder from '@axe-core/playwright';
import type { Page } from '@playwright/test';

import { expect, makeMandate, makePartnerProfile, makeSupportRequest, signUp, test, uniqueEmail, WEB_ORIGIN } from './fixtures';

type Entity = { id: string; version: number };
const origin = { Origin: WEB_ORIGIN };
test.use({ actionTimeout: 10_000 });

async function post<T>(page: Page, path: string, data: object, status: number): Promise<T> {
  const response = await page.request.post(path, { data, headers: { ...origin, 'Idempotency-Key': uniqueEmail('j05') } });
  expect(response.status(), await response.text()).toBe(status);
  return response.json() as Promise<T>;
}

async function audit(page: Page) {
  const { violations } = await new AxeBuilder({ page }).analyze();
  expect(violations.map(({ id }) => id)).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(page.viewportSize()!.width);
}

test('J05: both parties correct and confirm one version, then narrow its public projection', async ({ page, browser }) => {
  test.setTimeout(100_000);
  const viewport = page.viewportSize() ?? undefined;
  const partnerContext = await browser.newContext({ baseURL: WEB_ORIGIN, viewport });
  const visitorContext = await browser.newContext({ baseURL: WEB_ORIGIN, viewport });
  try {
    const partner = await partnerContext.newPage();
    const visitor = await visitorContext.newPage();
    await signUp(partner, 'mitra', 'Mitra J05');
    const partnerParty = await makePartnerProfile(partner);
    const mandate = await makeMandate(partner, true);
    await signUp(page, 'inovator', 'Rani J05');
    const party = (await (await page.request.get('/api/v1/me')).json() as { active_party_id: string }).active_party_id;
    const need = await makeSupportRequest(page, { min: '20000', max: '30000', currency: 'USD', period: '6 bulan', scope: 'biaya uji' }, { months: 6 });
    await post(page, `/api/v1/support-requests/${need}/activate`, { acting_party_id: party, expected_version: 1 }, 200);
    const preflight = await post<{ token: string; brief: { text: string } }>(page, '/api/v1/pitches/preflight', {
      acting_party_id: party, source_type: 'SUPPORT_REQUEST', source_id: need, opportunity_id: mandate,
    }, 200);
    const { pitch_id: pitchId } = await post<{ pitch_id: string }>(page, '/api/v1/pitches', {
      acting_party_id: party, preflight_token: preflight.token, brief: preflight.brief.text, files: [],
    }, 201);
    const api = `/api/v1/pitches/${pitchId}`;
    await post(partner, `${api}/decisions`, { acting_party_id: partnerParty, expected_version: 1, submission: 1, decision: 'APPROVE' }, 200);

    await page.goto(`/partnerships/new?pitch=${pitchId}`);
    await expect(page.getByText(/setelah pertemuan selesai/)).toBeVisible();

    const start = Date.now() + 12_000;
    const offer = await post<Entity & { slots: Entity[] }>(partner, `${api}/schedule-proposals`, {
      acting_party_id: partnerParty, agenda: 'Bahas uji lapangan', minutes: 30, time_zone: 'Asia/Jakarta',
      slots: [new Date(start).toISOString(), new Date(start + 3_600_000).toISOString()],
    }, 201);
    const meeting = await post<Entity>(page, `/api/v1/schedule-proposals/${offer.id}/accept`, {
      acting_party_id: party, expected_version: offer.version, slot_id: offer.slots[0].id,
    }, 200);
    await expect.poll(async () => {
      const response = await page.request.get(`${api}/schedule`);
      return ((await response.json()) as { meetings: { id: string; started: boolean }[] }).meetings.find(({ id }) => id === meeting.id)?.started;
    }, { timeout: 25_000 }).toBe(true);
    for (const [side, id] of [[page, party], [partner, partnerParty]] as const) {
      await post(side, `/api/v1/meetings/${meeting.id}/outcome`, { acting_party_id: id, result: 'COMPLETED' }, 200);
    }

    await page.goto(`/pitches/${pitchId}?tab=jadwal`);
    await page.getByRole('link', { name: 'Usulkan ringkasan' }).click();
    await expect(page.getByRole('heading', { level: 1, name: 'Usulkan ringkasan Kerja Sama' })).toBeVisible();
    await expect(page.locator('option[value=EQUITY]')).toBeDisabled();
    await page.getByRole('textbox', { name: 'Nama Kerja Sama' }).fill('Rani dan Mitra J05');
    await page.getByRole('textbox', { name: 'Cakupan' }).fill('Validasi prototipe dua belas bulan');
    await page.getByLabel(/Tanggal mulai.*wajib/).fill('2026-12-01');
    await page.getByRole('textbox', { name: 'Jumlah dana' }).fill('25000');
    await page.getByRole('textbox', { name: /Mata uang/ }).fill('USD');
    await page.getByRole('textbox', { name: 'Catatan bukti (privat)' }).fill('Catatan privat J05');
    const mine = page.getByRole('group', { name: 'Data yang Anda izinkan tampil' });
    for (const field of ['Nama Kerja Sama', 'Cakupan', 'Tanggal mulai', 'Jumlah dana']) {
      await mine.getByRole('checkbox', { name: field }).check();
    }
    await audit(page);
    await page.getByRole('button', { name: 'Kirim ringkasan versi 1' }).click();
    await expect(page).toHaveURL(/\/partnerships\/[0-9a-f-]+$/);
    await expect(page.getByText('Menunggu konfirmasi', { exact: true })).toBeVisible();
    await expect(page.getByText('Dikonfirmasi kedua pihak')).toHaveCount(0);
    await expect(page.getByRole('checkbox')).toHaveCount(0);
    const relationshipUrl = page.url();

    await partner.goto(`/pitches/${pitchId}`);
    await partner.getByRole('link', { name: 'Lihat ringkasan Kerja Sama' }).click();
    await partner.getByRole('button', { name: 'Minta perubahan' }).click();
    const correction = partner.getByRole('dialog', { name: 'Minta perubahan' });
    await correction.getByRole('textbox', { name: 'Cakupan' }).fill('Validasi prototipe enam bulan');
    await correction.getByRole('button', { name: 'Buat versi 2' }).click();
    await expect(partner.getByRole('heading', { name: /Ringkasan Kerja Sama · Versi 2/ })).toBeVisible();
    await expect(partner.getByRole('checkbox', { name: 'Jumlah dana' })).not.toBeChecked();
    for (const field of ['Nama Kerja Sama', 'Cakupan', 'Tanggal mulai']) {
      await partner.getByRole('checkbox', { name: field }).check();
    }
    await partner.getByRole('button', { name: 'Konfirmasi versi 2' }).click();
    await expect(partner.getByText('Konfirmasi versi 2 disimpan.')).toBeVisible();

    await page.reload();
    for (const field of ['Nama Kerja Sama', 'Cakupan', 'Tanggal mulai', 'Jumlah dana']) {
      await page.getByRole('checkbox', { name: field }).check();
    }
    await page.getByRole('button', { name: 'Konfirmasi versi 2' }).click();
    await expect(page.getByText('Dikonfirmasi kedua pihak')).toBeVisible();
    await expect(page.getByRole('checkbox')).toHaveCount(0);
    await audit(page);

    const profileLink = await page.getByRole('link', { name: 'Lihat profil publik' }).getAttribute('href');
    expect(profileLink).toBe(`/profiles/${party}`);
    await visitor.goto(profileLink!);
    await expect(visitor.getByText('Validasi prototipe enam bulan', { exact: true })).toBeVisible();
    await expect(visitor.getByText('2026-12-01', { exact: true })).toBeVisible();
    await expect(visitor.getByText(/25[. ]?000|Catatan privat J05/)).toHaveCount(0);
    await audit(visitor);

    await page.getByRole('button', { name: 'Sembunyikan Tanggal mulai' }).click();
    const hide = page.getByRole('dialog', { name: 'Sembunyikan data publik' });
    await expect(hide.getByText(/tidak dapat ditarik/)).toBeVisible();
    await hide.getByRole('button', { name: 'Sembunyikan sekarang' }).click();
    await expect(page.getByText('Data disembunyikan dari tampilan publik.')).toBeVisible();
    await visitor.reload();
    await expect(visitor.getByText('2026-12-01', { exact: true })).toHaveCount(0);
    await expect(visitor.getByText('Validasi prototipe enam bulan', { exact: true })).toBeVisible();

    await signUp(visitor, 'inovator', 'Pengunjung J05');
    await visitor.goto(relationshipUrl);
    await expect(visitor.getByRole('heading', { name: 'Ringkasan Kerja Sama belum tersedia' })).toBeVisible();
    await expect(visitor.getByText('Validasi prototipe enam bulan', { exact: true })).toHaveCount(0);
  } finally {
    await partnerContext.close();
    await visitorContext.close();
  }
});

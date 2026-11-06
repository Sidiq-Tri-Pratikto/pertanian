import AxeBuilder from '@axe-core/playwright';
import { readFile } from 'node:fs/promises';

import { expect, makeInvention, signUp, test, uniqueEmail, WEB_ORIGIN } from './fixtures';

test('reviews an upload before applying it, then downloads a permitted JSON export', async ({ page }) => {
  await signUp(page, 'inovator');
  const inventionId = await makeInvention(page, true, 'Ekspor saringan air');
  await page.goto('/inventions/import');
  await expect(page.getByRole('heading', { name: 'Impor dan ekspor data' })).toBeVisible();
  const file = page.getByLabel('Berkas JSON', { exact: true });
  await file.focus();
  await expect(file).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('checkbox', { name: 'Petakan catatan privat ke draf' })).toBeFocused();
  await file.setInputFiles({
    name: 'portability.json', mimeType: 'application/json',
    buffer: Buffer.from(JSON.stringify({
      schema_version: 1, external_system: 'browser', provenance: { source: 'Pengujian' },
      inventions: [{ external_id: 'browser-filter', provenance: { source: 'Pengujian' }, fields: { title: 'Draf dari berkas' } }],
    })),
  });
  await page.getByRole('button', { name: 'Validasi berkas' }).click();
  await expect(page.getByRole('heading', { name: 'Pratinjau perubahan' })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText('Buat draf', { exact: true })).toBeVisible();
  const apply = page.getByRole('button', { name: 'Terapkan impor' });
  await expect(apply).toBeDisabled();
  await page.getByRole('checkbox', { name: 'Saya sudah meninjau pratinjau' }).check();
  await apply.click();
  await expect(page.getByText('1 tersimpan · 0 dilewati')).toBeVisible({ timeout: 15_000 });
  await page.getByLabel('Versi inovasi').selectOption(`PUBLISHED:${inventionId}`);
  await page.getByRole('button', { name: 'Siapkan ekspor' }).click();
  const downloadButton = page.getByRole('button', { name: 'Unduh JSON' });
  await expect(downloadButton).toBeVisible({ timeout: 15_000 });
  const saved = page.waitForEvent('download');
  await downloadButton.click();
  const artifact = await saved;
  expect(artifact.suggestedFilename()).toBe('temuriset-export.json');
  expect(JSON.parse(await readFile((await artifact.path())!, 'utf8')).inventions[0].fields.title).toBe('Ekspor saringan air');
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(page.viewportSize()!.width);
  const { violations } = await new AxeBuilder({ page }).analyze();
  expect(violations.map(({ id, nodes }) => [id, nodes.map(({ target }) => target)])).toEqual([]);
});

test('denies a revoked document grant and keeps the selected resource', async ({ page, browser }) => {
  await signUp(page, 'inovator');
  const recipient = (await (await page.request.get('/api/v1/me')).json()) as { active_party_id: string };
  const owner = await browser.newContext({ baseURL: WEB_ORIGIN });
  try {
    const ownerPage = await owner.newPage();
    await signUp(ownerPage, 'inovator', 'Pemilik dokumen');
    const me = (await (await owner.request.get('/api/v1/me')).json()) as { active_party_id: string };
    const evidence = Buffer.from('%PDF-1.4 Uji sumber bukti');
    const intent = await owner.request.post('/api/v1/documents/upload-intents', {
      data: { acting_party_id: me.active_party_id, title: 'Bukti privat', kind: 'evidence', media_type: 'application/pdf', size_bytes: evidence.length },
      headers: { Origin: WEB_ORIGIN },
    });
    expect(intent.status()).toBe(201);
    const { upload_url } = await intent.json() as { upload_url: string };
    const uploaded = await owner.request.put(upload_url, { data: evidence, headers: { Origin: WEB_ORIGIN } });
    expect(uploaded.status()).toBe(202);
    const { document_id } = await uploaded.json() as { document_id: string };
    await expect.poll(async () => {
      const result = await owner.request.get(`/api/v1/documents/${document_id}`);
      const document = await result.json() as { versions: { file_state: string }[] };
      return document.versions[0].file_state;
    }).toBe('AVAILABLE');
    const grant = await owner.request.post(`/api/v1/documents/${document_id}/grants`, {
      data: { acting_party_id: me.active_party_id, version: 1, grantee_party_id: recipient.active_party_id, purpose: 'pitch' },
      headers: { Origin: WEB_ORIGIN, 'Idempotency-Key': uniqueEmail('grant') },
    });
    expect(grant.status()).toBe(201);
    const { id } = await grant.json() as { id: string };

    await page.goto('/inventions/import');
    const selection = page.getByLabel('ID dokumen (opsional)');
    await selection.fill(document_id);
    await page.getByRole('button', { name: 'Siapkan ekspor' }).click();
    const download = page.getByRole('button', { name: 'Unduh JSON' });
    await expect(download).toBeVisible({ timeout: 15_000 });
    const revoked = await owner.request.post(`/api/v1/grants/${id}/revoke`, {
      data: { acting_party_id: me.active_party_id },
      headers: { Origin: WEB_ORIGIN, 'Idempotency-Key': uniqueEmail('rev') },
    });
    expect(revoked.status()).toBe(200);
    await download.click();
    await expect(page.getByRole('heading', { name: 'Ekspor belum dapat dilanjutkan' })).toBeVisible();
    await expect(page.getByText(/Akses ke dokumen ini sudah dicabut/)).toBeVisible();
    await expect(selection).toHaveValue(document_id);
    await page.getByRole('button', { name: 'Periksa status ekspor' }).click();
    await expect(page.getByText('Ekspor · Kedaluwarsa')).toBeVisible();
  } finally {
    await owner.close();
  }
});

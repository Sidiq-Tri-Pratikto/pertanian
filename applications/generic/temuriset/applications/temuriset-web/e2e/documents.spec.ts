import AxeBuilder from '@axe-core/playwright';

import { expect, makeInvention, signUp, test, WEB_ORIGIN } from './fixtures';

test.beforeEach(({}, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium-1280', 'Journeys run at one width.');
});

/** A one-page PDF, with text or (like a scan) without, built byte by byte so its offsets are right. */
function pdf(text: string | null): Buffer {
  const stream = text ? `BT /F1 12 Tf 72 720 Td (${text}) Tj ET` : '';
  const objects = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>',
    `<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`,
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
  ];
  let out = '%PDF-1.4\n';
  const offsets: number[] = [];
  objects.forEach((body, index) => {
    offsets.push(out.length);
    out += `${index + 1} 0 obj\n${body}\nendobj\n`;
  });
  const xref = out.length;
  out += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n${offsets.map((offset) => `${String(offset).padStart(10, '0')} 00000 n \n`).join('')}`;
  out += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
  return Buffer.from(out, 'latin1');
}

async function openEvidenceStep(page: import('@playwright/test').Page) {
  await signUp(page, 'inovator');
  const id = await makeInvention(page, false);
  await page.goto(`/inventions/${id}/edit?step=2`);
  return id;
}

async function upload(page: import('@playwright/test').Page, name: string, mimeType: string, buffer: Buffer) {
  await page.getByLabel('Unggah dokumen bukti').setInputFiles({ name, mimeType, buffer });
}

test('a PDF is scanned, read and offered, with review kept separate (UX-10)', async ({ page }) => {
  await openEvidenceStep(page);

  await upload(page, 'Laporan uji.pdf', 'application/pdf', pdf('Kapasitas saring 10 L/jam'));

  const item = page.locator('.tr-doc', { hasText: 'Laporan uji' });
  await expect(item.getByText('Aman dan tersedia')).toBeVisible({ timeout: 15_000 });
  await expect(item.getByText('Teks berhasil dibaca')).toBeVisible({ timeout: 15_000 });
  await expect(item.getByText('Disediakan, belum diperiksa')).toBeVisible();
  await expect(item.getByText('Privat. Belum dibagikan kepada siapa pun.')).toBeVisible();
});

test('a scan without text is available but needs manual reading', async ({ page }) => {
  await openEvidenceStep(page);

  await upload(page, 'Pindaian.pdf', 'application/pdf', pdf(null));

  const item = page.locator('.tr-doc', { hasText: 'Pindaian' });
  await expect(item.getByText('Aman dan tersedia')).toBeVisible({ timeout: 15_000 });
  await expect(item.getByText('Perlu diisi manual')).toBeVisible({ timeout: 15_000 });
});

test('a file that is not what it claims is rejected and the draft is unchanged', async ({ page }) => {
  await openEvidenceStep(page);
  const title = await page.getByRole('textbox', { name: 'Apa yang diukur' }).first().inputValue();

  await upload(page, 'Bukan PDF.pdf', 'application/pdf', Buffer.from('MZ\x90\x00 this is an executable'));

  await expect(page.locator('.tr-doc', { hasText: 'Bukan PDF' }).getByText('Ditolak saat pemeriksaan keamanan')).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('textbox', { name: 'Apa yang diukur' }).first()).toHaveValue(title);
});

test('a file over the limit is refused with the limit, and nothing uploads', async ({ page }) => {
  await openEvidenceStep(page);
  const requests: string[] = [];
  page.on('request', (request) => request.url().includes('/documents/upload-intents') && requests.push(request.url()));

  await upload(page, 'Besar.pdf', 'application/pdf', Buffer.alloc(21 * 1024 * 1024, 0x25));

  await expect(page.getByText(/Berkas melebihi batas 20 MB untuk PDF dan DOCX/)).toBeVisible();
  expect(requests).toEqual([]);
});

test('the owner sees a grant, revokes it in a dialog, and the recipient is refused afterwards (AC65)', async ({ page, browser }) => {
  const id = await openEvidenceStep(page);
  await upload(page, 'Laporan uji.pdf', 'application/pdf', pdf('Laporan'));
  await expect(page.getByText('Aman dan tersedia', { exact: true })).toBeVisible({ timeout: 15_000 });
  const partnerPage = await (await browser.newContext()).newPage();
  await signUp(partnerPage, 'mitra', 'Bima');
  const partner = (await (await partnerPage.request.get('/api/v1/me')).json()) as { active_party_id: string };
  const me = (await (await page.request.get('/api/v1/me')).json()) as { active_party_id: string };
  const [document] = (await (await page.request.get('/api/v1/documents')).json()) as { id: string }[];
  const granted = await page.request.post(`/api/v1/documents/${document.id}/grants`, {
    data: { acting_party_id: me.active_party_id, version: 1, grantee_party_id: partner.active_party_id, purpose: 'pitch' },
    headers: { Origin: WEB_ORIGIN, 'Idempotency-Key': `grant-${id}` },
  });
  expect(granted.status()).toBe(201);
  const content = `/api/v1/documents/${document.id}/versions/1/content`;
  expect((await partnerPage.request.get(content)).status()).toBe(200);

  await page.reload();
  await expect(page.getByText('Dibagikan hanya kepada Bima, hanya versi 1.')).toBeVisible();
  const opener = page.getByRole('button', { name: /Cabut akses\s*Bima/ });
  await opener.click();
  const dialog = page.getByRole('dialog', { name: 'Cabut akses Bima?' });
  await expect(dialog.getByRole('heading', { name: 'Cabut akses Bima?' })).toBeFocused();
  const { violations } = await new AxeBuilder({ page }).include('dialog').analyze();
  expect(violations.map((violation) => violation.id)).toEqual([]);
  await page.keyboard.press('Escape');
  await expect(dialog).toBeHidden();
  await expect(opener).toBeFocused();

  await opener.click();
  await dialog.getByRole('button', { name: 'Cabut akses' }).click();

  await expect(page.getByText(/Akses Bima dicabut. Unduhan baru diblokir/)).toBeVisible();
  await expect(page.getByLabel('Unggah dokumen bukti')).toBeFocused();
  const refused = await partnerPage.request.get(content, { headers: { Range: 'bytes=0-7' } });
  expect(refused.status()).toBe(403);
  expect(((await refused.json()) as { error: { code: string } }).error.code).toBe('GRANT_REVOKED');
  await partnerPage.context().close();
});

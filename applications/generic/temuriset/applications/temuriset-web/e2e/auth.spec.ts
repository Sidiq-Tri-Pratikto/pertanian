import { expect, latestCode, signUp, test, uniqueEmail, WEB_ORIGIN } from './fixtures';

// Journeys run once, at desktop width; every route is also checked at every width by the other specs.
test.beforeEach(({}, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium-1280', 'Journeys run at one width.');
});

async function startSignUp(page: import('@playwright/test').Page, persona: 'inovator' | 'mitra', email: string) {
  await page.goto('/start');
  await page.getByRole('radio', { name: persona === 'inovator' ? /Saya punya inovasi/ : /Saya berinvestasi/ }).check();
  await page.getByRole('textbox', { name: /Nama tampilan/ }).fill(persona === 'inovator' ? 'Rani' : 'Bima');
  await page.getByRole('textbox', { name: /Email/ }).fill(email);
  await page.getByRole('button', { name: 'Kirim kode' }).click();
  await expect(page).toHaveURL(/\/start\/kode$/);
}

for (const [persona, home, heading] of [
  ['inovator', '/home', 'Beranda'],
  ['mitra', '/discover', 'Jelajahi'],
] as const) {
  test(`${persona} signs up with a code and lands on ${heading} without any organization field (UX-01)`, async ({ page }) => {
    const email = uniqueEmail(persona);

    await startSignUp(page, persona, email);
    await expect(page.getByText(`Kami mengirim kode enam angka ke ${email}`)).toBeVisible();
    await page.getByRole('textbox', { name: /Kode verifikasi/ }).fill(await latestCode(page.request, email));
    await page.getByRole('button', { name: 'Masuk' }).click();

    await expect(page).toHaveURL(new RegExp(`${home}$`));
    await expect(page.getByRole('heading', { level: 1, name: heading })).toBeVisible();
    await expect(page.getByRole('combobox', { name: 'Bertindak sebagai' })).toHaveValue(/.+/);
  });
}

test('a wrong code focuses the summary, states attempts left and keeps the code (UX-09)', async ({ page }) => {
  const email = uniqueEmail('salah');
  await startSignUp(page, 'inovator', email);
  const right = await latestCode(page.request, email);
  const wrong = String((Number(right) + 1) % 1_000_000).padStart(6, '0');

  await page.getByRole('textbox', { name: /Kode verifikasi/ }).fill(wrong);
  await page.getByRole('button', { name: 'Masuk' }).click();

  const summary = page.getByRole('group', { name: 'Masih ada yang perlu diperbaiki' });
  await expect(summary).toBeFocused();
  await expect(summary.getByRole('link', { name: 'Kode tidak cocok. Sisa percobaan: 4.' })).toBeVisible();
  await expect(page.getByRole('textbox', { name: /Kode verifikasi/ })).toHaveValue(wrong);
});

test('a signed-out visit returns to the page after sign-in', async ({ page }) => {
  const email = await signUp(page, 'inovator');
  await page.context().clearCookies();

  await page.goto('/settings');
  await expect(page).toHaveURL(/\/start\?kembali=%2Fsettings$/);
  await page.getByRole('link', { name: 'Masuk' }).click();
  await page.getByRole('textbox', { name: /Email/ }).fill(email);
  await page.getByRole('button', { name: 'Kirim kode' }).click();
  await expect(page).toHaveURL(/\/start\/kode$/);
  await page.getByRole('textbox', { name: /Kode verifikasi/ }).fill(await latestCode(page.request, email));
  await page.getByRole('button', { name: 'Masuk' }).click();

  await expect(page).toHaveURL(/\/settings$/);
});

test('switching to an organization reloads in that context and announces it (UX-02)', async ({ page }) => {
  await signUp(page, 'mitra', 'Bima');
  const created = await page.request.post('/api/v1/organizations', {
    data: { name: 'Demo Circular Materials Ltd', kind: 'company' },
    headers: { Origin: WEB_ORIGIN, 'Idempotency-Key': uniqueEmail('org') },
  });
  expect(created.status()).toBe(201);
  const organization = (await created.json()) as { party_id: string };

  await page.goto('/settings');
  const switcher = page.getByRole('combobox', { name: 'Bertindak sebagai' });
  await switcher.focus();
  await switcher.selectOption(organization.party_id);

  await expect(page.getByText('Sekarang bertindak sebagai Demo Circular Materials Ltd')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Anggota Demo Circular Materials Ltd' })).toBeVisible();
  await expect(switcher).toBeFocused();
});

test('a manager invites with capabilities and the invitee accepts after reading what it grants', async ({ page, browser }) => {
  await signUp(page, 'mitra', 'Bima');
  const organization = (await (
    await page.request.post('/api/v1/organizations', {
      data: { name: 'Demo Circular Materials Ltd', kind: 'company' },
      headers: { Origin: WEB_ORIGIN, 'Idempotency-Key': uniqueEmail('org') },
    })
  ).json()) as { party_id: string };
  await page.request.put('/api/v1/me/context', { data: { party_id: organization.party_id }, headers: { Origin: WEB_ORIGIN } });
  const invitee = browser.newContext();
  const inviteePage = await (await invitee).newPage();
  const inviteeEmail = await signUp(inviteePage, 'inovator');

  await page.goto('/settings');
  await page.getByText('Undang anggota').click();
  await page.getByRole('textbox', { name: /Email anggota/ }).fill(inviteeEmail);
  await page.getByRole('checkbox', { name: 'Mengubah portofolio' }).check();
  await expect(page.getByText(/Mengundang sebagai:/)).toContainText('Demo Circular Materials Ltd');
  await page.getByRole('button', { name: 'Kirim undangan' }).click();
  await expect(page.getByText('Undangan dikirim. Berlaku 7 hari.')).toBeVisible();
  await expect(page.getByText(inviteeEmail, { exact: true })).toBeVisible();

  const mail = (await (await inviteePage.request.get('/api/v1/dev/mailbox', { params: { email: inviteeEmail } })).json()) as { body: string }[];
  const link = new URL(mail[0].body.match(/https?:\/\/\S+/)![0]);
  await inviteePage.goto(link.pathname);
  await expect(inviteePage.getByText('Demo Circular Materials Ltd')).toBeVisible();
  await expect(inviteePage.getByText('Mengubah portofolio')).toBeVisible();
  await inviteePage.getByRole('button', { name: 'Terima undangan' }).click();

  await expect(inviteePage).toHaveURL(/\/settings\?bergabung=1$/);
  await expect(inviteePage.getByText('Anda sudah bergabung dengan organisasi')).toBeVisible();
  await (await invitee).close();
});

test('sign-out ends the session in this browser', async ({ page }) => {
  await signUp(page, 'inovator');
  await page.goto('/settings');

  await page.getByRole('button', { name: 'Keluar' }).click();

  await expect(page).toHaveURL(/\/start\?masuk=1$/);
  await page.goto('/home');
  await expect(page).toHaveURL(/\/start\?kembali=%2Fhome$/);
});

import AxeBuilder from '@axe-core/playwright';
import type { APIRequestContext } from '@playwright/test';

import { expect, makeInvention, signUp, test, uniqueEmail, WEB_ORIGIN } from './fixtures';

test.beforeEach(({}, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium-1280', 'Journeys run at one width.');
});

type Mail = { subject: string; body: string };

async function mailbox(request: APIRequestContext, email: string): Promise<Mail[]> {
  return (await (await request.get(`/api/v1/dev/mailbox?email=${encodeURIComponent(email)}`)).json()) as Mail[];
}

function link(body: string, path: string): string {
  const found = body.match(new RegExp(`https?://[^\\s]*${path}[^\\s]*`));
  expect(found, body).not.toBeNull();
  return new URL(found![0]).pathname + new URL(found![0]).search;
}

test('a visitor follows an invention in English, gets one update email, and unfollows (053)', async ({ page, browser }) => {
  const email = uniqueEmail('follower');
  const title = `Saringan ${uniqueEmail('f').split('@')[0].replace(/[^a-z0-9]/g, '')}`;

  // The inventor publishes the invention and turns its public page on.
  await signUp(page, 'inovator');
  const invention = await makeInvention(page, true, title);
  await page.goto(`/inventions/${invention}`);
  await page.getByRole('checkbox', { name: 'Tampilkan halaman publik inovasi ini' }).check();
  await page.getByRole('button', { name: 'Simpan halaman publik' }).click();
  await expect(page.getByText('Halaman publik tersimpan dan terlihat oleh siapa pun.')).toBeVisible();

  // A visitor follows from the English page; nothing is sent before confirming.
  const visitorContext = await browser.newContext({ baseURL: WEB_ORIGIN });
  const visitor = await visitorContext.newPage();
  await visitor.goto(`/en/inventions/${invention}`);
  await visitor.getByRole('textbox', { name: /Email address/ }).fill(email);
  await visitor.getByRole('button', { name: 'Send confirmation email' }).click();
  await expect(visitor.getByText('Check your email')).toBeVisible();
  const [confirmation] = await mailbox(visitor.request, email);
  expect(confirmation.subject).toBe(`Confirm your subscription: ${title}`);
  await visitor.goto(link(confirmation.body, '/en/follow/confirm'));
  await expect(visitor.getByText(`Invention: ${title}`)).toBeVisible();
  const { violations } = await new AxeBuilder({ page: visitor }).analyze();
  expect(violations.map((violation) => violation.id)).toEqual([]);
  await visitor.getByRole('button', { name: 'Confirm subscription' }).click();
  await expect(visitor.getByRole('heading', { name: 'You’re following this invention' })).toBeVisible();

  // The inventor publishes an update; the follower gets it once, in English.
  await page.reload();
  await page.getByRole('textbox', { name: /Judul kabar/ }).fill('Jadwal pilot dikonfirmasi');
  await page.getByRole('textbox', { name: /Isi kabar/ }).fill('Koperasi menyepakati uji dua unit pada Januari.');
  await page.getByRole('button', { name: 'Simpan sebagai draf' }).click();
  await page.getByRole('button', { name: 'Terbitkan' }).click();
  await expect(page.getByText('“Jadwal pilot dikonfirmasi” terbit di halaman publik.')).toBeVisible();
  await expect.poll(async () => (await mailbox(visitor.request, email))[0]?.subject, { timeout: 15_000 }).toBe(`An update from ${title}`);
  const [update] = await mailbox(visitor.request, email);
  expect(update.body).toContain('Koperasi menyepakati uji dua unit pada Januari.');

  // Unfollowing takes one press from the link in the email.
  await visitor.goto(link(update.body, '/en/follow/manage'));
  await visitor.getByRole('button', { name: 'Unfollow invention' }).click();
  await expect(visitor.getByRole('heading', { name: 'You’re unsubscribed' })).toBeVisible();
  await visitorContext.close();
});

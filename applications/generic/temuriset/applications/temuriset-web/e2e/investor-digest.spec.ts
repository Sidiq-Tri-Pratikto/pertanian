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

test('an investor subscribes with only an email, confirms, gets a direct alert, and needs signup for details (046)', async ({ page, browser }) => {
  // The keyword is unique per run, so other tests' inventions never match this subscriber.
  const word = uniqueEmail('kw').split('@')[0].replace(/[^a-z0-9]/g, '');
  const email = uniqueEmail('investor');
  const visitorContext = await browser.newContext({ baseURL: WEB_ORIGIN });
  const visitor = await visitorContext.newPage();

  await visitor.goto('/start');
  await visitor.getByRole('link', { name: 'Berlangganan kabar inovasi' }).click();
  await expect(visitor).toHaveURL(/\/langganan$/);
  await visitor.getByRole('textbox', { name: /Email/ }).fill(email);
  await visitor.getByRole('textbox', { name: 'Kata kunci' }).fill(word);
  await visitor.getByRole('button', { name: 'Berlangganan' }).click();
  await expect(visitor.getByRole('heading', { name: 'Periksa email Anda' })).toBeVisible();

  const [confirmation] = await mailbox(visitor.request, email);
  expect(confirmation.subject).toBe('Konfirmasi langganan kabar inovasi TemuRiset');
  await visitor.goto(link(confirmation.body, '/langganan/konfirmasi'));
  await visitor.getByRole('button', { name: 'Konfirmasi langganan' }).click();
  await expect(visitor.getByRole('heading', { name: 'Langganan aktif' })).toBeVisible();

  // An inventor publishes a matching invention and includes it from the invention page.
  await signUp(page, 'inovator');
  const title = `Saringan air ${word}`;
  const invention = await makeInvention(page, true, title);
  await page.goto(`/inventions/${invention}`);
  const toggle = page.getByRole('checkbox', { name: /Sertakan dalam kabar untuk investor/ });
  await expect(toggle).not.toBeChecked();
  // The switch saves in the background; wait for the save before reloading.
  const saved = page.waitForResponse((response) => response.url().endsWith('/investor-digest') && response.request().method() === 'PUT');
  await toggle.check();
  expect((await saved).ok()).toBe(true);
  await page.reload();
  await expect(page.getByRole('checkbox', { name: /Sertakan dalam kabar untuk investor/ })).toBeChecked();

  // The worker sends the direct alert; it names the reason and links to the teaser.
  await expect.poll(async () => (await mailbox(visitor.request, email))[0]?.subject, { timeout: 15_000 }).toBe(`Inovasi sesuai minat Anda: ${title}`);
  const [alert] = await mailbox(visitor.request, email);
  expect(alert.body).toContain(`kata kunci “${word}”`);
  expect(alert.body).toContain('Inovator: Inovator di TemuRiset');

  await visitor.goto(link(alert.body, '/temuan/'));
  await expect(visitor.getByRole('heading', { level: 1, name: title })).toBeVisible();
  const { violations } = await new AxeBuilder({ page: visitor }).analyze();
  expect(violations.map((violation) => violation.id)).toEqual([]);
  await visitor.getByRole('link', { name: 'Daftar untuk melihat detail' }).click();
  await expect(visitor).toHaveURL(new RegExp(`/start\\?kembali=${encodeURIComponent(`/inventions/${invention}`)}`));

  // Leaving takes one press from the link in any email.
  await visitor.goto(link(alert.body, '/langganan/atur'));
  await visitor.getByRole('button', { name: 'Berhenti berlangganan' }).click();
  await expect(visitor.getByRole('heading', { name: 'Anda sudah berhenti berlangganan' })).toBeVisible();
  await visitorContext.close();
});

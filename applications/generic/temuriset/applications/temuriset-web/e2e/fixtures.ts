import { test as base, expect, type APIRequestContext, type Page } from '@playwright/test';

import type { Persona } from '@/features/persona';

import type { Route } from './routes';

let counter = 0;

/** The web origin under test; the service refuses cookie-bearing writes from any other. */
export const WEB_ORIGIN = `http://localhost:${process.env.E2E_PORT ?? 3029}`;

/** A unique address per sign-up, so tests never share an account or a rate-limit window. */
export function uniqueEmail(prefix: string): string {
  counter += 1;
  return `${prefix}-${process.pid}-${Date.now()}-${counter}@example.com`;
}

/** The newest code mailed to an address, read from the development mailbox through the web origin. */
export async function latestCode(request: APIRequestContext, email: string): Promise<string> {
  const messages = (await (await request.get('/api/v1/dev/mailbox', { params: { email } })).json()) as { body: string }[];
  const code = messages[0]?.body.match(/\b\d{6}\b/)?.[0];
  expect(code, `code mailed to ${email}`).toBeTruthy();
  return code!;
}

/** Signs a browser context up through the API, the same requests the S01 screens send; its cookie jar keeps the session. */
export async function signUp(page: Page, persona: Persona, name = 'Rani'): Promise<string> {
  const email = uniqueEmail(persona);
  const headers = { Origin: WEB_ORIGIN };
  const request = page.request;
  const sent = await request.post('/api/v1/auth/code', {
    data: { email, purpose: 'sign_up', display_name: name, time_zone: 'Asia/Jakarta', persona },
    headers,
  });
  expect(sent.status()).toBe(202);
  const verified = await request.post('/api/v1/auth/verify', { data: { email, code: await latestCode(request, email) }, headers });
  expect(verified.status(), await verified.text()).toBe(200);
  return email;
}

export const COMPLETE_DRAFT = {
  title: 'Saringan air keramik desa',
  summary: 'Saringan air keramik untuk rumah tangga di desa tanpa listrik.',
  problem: 'Air sumur keruh dan tidak aman diminum.',
  solution: 'Saringan keramik berpori dengan perak koloid.',
  intended_users: 'Rumah tangga di desa',
  sector: 'Air bersih',
  stage: 'PROTOTYPE',
  keywords: ['air'],
  facts: [
    { label: 'Kapasitas saring', value: '10', unit: 'L/jam', timing: 'CURRENT', provenance: 'SELF_DECLARED' },
    { label: 'Kapasitas saring', value: '20', unit: 'L/jam', timing: 'PLANNED', provenance: 'SELF_DECLARED' },
  ],
  claims: [{ kind: 'authority', subject_name: 'Rani', status: 'not_established' }],
};

/** Creates an invention through the API as the signed-in account; optionally publishes it. Returns its id. */
export async function makeInvention(page: Page, publish: boolean, title = COMPLETE_DRAFT.title): Promise<string> {
  const headers = { Origin: WEB_ORIGIN };
  const me = (await (await page.request.get('/api/v1/me')).json()) as { active_party_id: string };
  const created = (await (
    await page.request.post('/api/v1/inventions', { data: { acting_party_id: me.active_party_id }, headers: { ...headers, 'Idempotency-Key': uniqueEmail('c') } })
  ).json()) as { id: string; version: number };
  const saved = await page.request.put(`/api/v1/inventions/${created.id}/draft`, {
    data: { acting_party_id: me.active_party_id, expected_version: created.version, ...COMPLETE_DRAFT, title },
    headers: { ...headers, 'Idempotency-Key': uniqueEmail('s') },
  });
  expect(saved.status(), await saved.text()).toBe(200);
  if (publish) {
    const version = ((await saved.json()) as { version: number }).version;
    const published = await page.request.post(`/api/v1/inventions/${created.id}/publish`, {
      data: { acting_party_id: me.active_party_id, expected_version: version },
      headers: { ...headers, 'Idempotency-Key': uniqueEmail('p') },
    });
    expect(published.status(), await published.text()).toBe(200);
  }
  return created.id;
}

/** Starts a support request for a new published invention through the API, optionally with a budget. Returns its id. */
export async function makeSupportRequest(page: Page, budget?: Record<string, unknown>): Promise<string> {
  const invention = await makeInvention(page, true);
  const me = (await (await page.request.get('/api/v1/me')).json()) as { active_party_id: string };
  const created = await page.request.post('/api/v1/support-requests', {
    data: { acting_party_id: me.active_party_id, invention_id: invention, outcome: 'Validasi prototipe enam bulan', support_forms: ['project_funding'], budget },
    headers: { Origin: WEB_ORIGIN, 'Idempotency-Key': uniqueEmail('sr') },
  });
  expect(created.status(), await created.text()).toBe(201);
  return ((await created.json()) as { id: string }).id;
}

/** Starts a raise for a company not founded yet, linked to a new published invention. Returns its id. */
export async function makeFundingRequest(page: Page): Promise<string> {
  const invention = await makeInvention(page, true, 'LoopMaterial');
  const me = (await (await page.request.get('/api/v1/me')).json()) as { active_party_id: string };
  const created = await page.request.post('/api/v1/funding-requests', {
    data: { acting_party_id: me.active_party_id, subject_type: 'PROPOSED_ENTITY', proposed_name: 'PT Loop', currency: 'USD', target_amount: '500000', invention_ids: [invention] },
    headers: { Origin: WEB_ORIGIN, 'Idempotency-Key': uniqueEmail('fr') },
  });
  expect(created.status(), await created.text()).toBe(201);
  return ((await created.json()) as { id: string }).id;
}

type Fixtures = {
  /** Opens a route as its persona and fails on console errors, failed requests or an unexpected status. */
  visit: (route: Route) => Promise<Page>;
};

export const test = base.extend<Fixtures>({
  // Named `provide`, not `use`, so the React hooks lint rule does not mistake it for React's `use`.
  visit: async ({ page, context }, provide) => {
    const problems: string[] = [];
    let expected = 200;
    page.on('console', (message) => {
      // Chromium reports the document's own 404 as a console error; that status is asserted separately.
      if (message.type() === 'error' && !(expected === 404 && message.text().includes('404'))) {
        problems.push(`console: ${message.text()}`);
      }
    });
    page.on('pageerror', (error) => problems.push(`page error: ${error.message}`));
    page.on('requestfailed', (request) => {
      // Prefetches cancelled by navigation are not failures.
      if (request.failure()?.errorText !== 'net::ERR_ABORTED') problems.push(`failed: ${request.url()}`);
    });
    page.on('response', (response) => {
      if (response.status() >= 400 && response.request().resourceType() !== 'document') {
        problems.push(`HTTP ${response.status()}: ${response.url()}`);
      }
    });

    await provide(async (route) => {
      expected = route.status ?? 200;
      await context.clearCookies();
      if (route.persona) await signUp(page, route.persona);
      let path = route.path;
      if (path.includes(':draft')) path = path.replace(':draft', await makeInvention(page, false));
      if (path.includes(':published')) path = path.replace(':published', await makeInvention(page, true));
      if (path.includes(':support')) path = path.replace(':support', await makeSupportRequest(page));
      if (path.includes(':funding')) path = path.replace(':funding', await makeFundingRequest(page));
      const response = await page.goto(path);
      expect(response?.status(), `status of ${route.path}`).toBe(expected);
      await page.waitForLoadState('networkidle');
      return page;
    });

    expect(problems, 'console errors and failed requests').toEqual([]);
  },
});

export { expect };

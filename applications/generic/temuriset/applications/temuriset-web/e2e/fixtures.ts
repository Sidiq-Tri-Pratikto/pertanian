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
      const response = await page.goto(route.path);
      expect(response?.status(), `status of ${route.path}`).toBe(expected);
      await page.waitForLoadState('networkidle');
      return page;
    });

    expect(problems, 'console errors and failed requests').toEqual([]);
  },
});

export { expect };

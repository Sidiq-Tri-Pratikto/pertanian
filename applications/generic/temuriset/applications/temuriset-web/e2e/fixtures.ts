import { test as base, expect, type Page } from '@playwright/test';

import { PERSONA_COOKIE } from '@/features/persona';

import type { Route } from './routes';

type Fixtures = {
  /** Opens a route as its persona and fails on console errors, failed requests or an unexpected status. */
  visit: (route: Route) => Promise<Page>;
};

export const test = base.extend<Fixtures>({
  // Named `provide`, not `use`, so the React hooks lint rule does not mistake it for React's `use`.
  visit: async ({ page, context, baseURL }, provide) => {
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
      if (route.persona) {
        await context.addCookies([{ name: PERSONA_COOKIE, value: route.persona, url: baseURL! }]);
      }
      const response = await page.goto(route.path);
      expect(response?.status(), `status of ${route.path}`).toBe(expected);
      await page.waitForLoadState('networkidle');
      return page;
    });

    expect(problems, 'console errors and failed requests').toEqual([]);
  },
});

export { expect };

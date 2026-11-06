import { existsSync } from 'node:fs';
import { defineConfig, devices } from '@playwright/test';

import { loadStagingFixtures, STAGING_JOURNEYS, STAGING_SUITES, stagingOrigin, VIEWPORTS } from './e2e/staging';

// Real-browser checks (spec 003). They run against `next build` plus `next start`, never `next dev`, on a port of
// their own so a running dev server is never mistaken for the build under test.
const port = Number(process.env.E2E_PORT ?? 3029);
const staging = stagingOrigin();
const baseURL = staging ?? `http://localhost:${port}`;
const stagingFiles = STAGING_SUITES.map((name) => `${name}.spec.ts`);
if (staging) {
  if (process.argv.slice(2).join(' ') !== 'test') {
    throw new Error('Run staging with npx playwright test and no filters or overrides.');
  }
  const missing = [
    ...stagingFiles.filter((file) => !existsSync(new URL(`./e2e/${file}`, import.meta.url))),
    ...STAGING_JOURNEYS.filter(({ file, title }) => !title || !existsSync(new URL(`./e2e/${file}`, import.meta.url)))
      .map(({ name }) => name),
  ];
  if (missing.length) throw new Error(`Staging suites are missing: ${missing.join(', ')}.`);
  loadStagingFixtures(staging);
}

export default defineConfig({
  testDir: './e2e',
  fullyParallel: !staging,
  testMatch: staging ? [...stagingFiles, ...STAGING_JOURNEYS.map(({ file }) => file)].map((file) => `**/e2e/${file}`) : undefined,
  maxFailures: staging ? 1 : 0,
  forbidOnly: !!(staging || process.env.CI),
  retries: 0,
  workers: staging ? 1 : process.env.CI ? 2 : undefined,
  reporter: staging ? [['list'], ['./e2e/staging-reporter.ts']] : [['list'], ['html', { open: 'never', outputFolder: 'playwright-report' }]],
  metadata: { build: staging ? 'deployed HTTPS application' : 'next build + next start', browser: 'chromium' },
  use: { baseURL, trace: staging ? 'off' : 'retain-on-failure' },
  projects: VIEWPORTS.map((width) => ({
    name: `chromium-${width}`,
    use: { ...devices['Desktop Chrome'], viewport: { width, height: 800 } },
  })),
  webServer: staging ? undefined : {
    command: `npx next start --port ${port}`,
    url: `${baseURL}/start`,
    reuseExistingServer: false,
    timeout: 60_000,
  },
});

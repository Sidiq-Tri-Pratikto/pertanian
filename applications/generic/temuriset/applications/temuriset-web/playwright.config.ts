import { defineConfig, devices } from '@playwright/test';

// Real-browser checks (spec 003). They run against `next build` plus `next start`, never `next dev`, on a port of
// their own so a running dev server is never mistaken for the build under test.
const port = Number(process.env.E2E_PORT ?? 3029);
const baseURL = `http://localhost:${port}`;

/** The widths every route must hold without horizontal scroll (PRD section 13). */
export const VIEWPORTS = [320, 360, 768, 1280] as const;

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: [['list'], ['html', { open: 'never', outputFolder: 'playwright-report' }]],
  metadata: { build: 'next build + next start', browser: 'chromium', apiUrl: process.env.API_URL ?? '' },
  use: { baseURL, trace: 'retain-on-failure' },
  projects: VIEWPORTS.map((width) => ({
    name: `chromium-${width}`,
    use: { ...devices['Desktop Chrome'], viewport: { width, height: 800 } },
  })),
  webServer: {
    command: `npx next start --port ${port}`,
    url: `${baseURL}/start`,
    reuseExistingServer: false,
    timeout: 60_000,
  },
});

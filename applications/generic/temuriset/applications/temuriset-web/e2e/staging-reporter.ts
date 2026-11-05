import { basename } from 'node:path';
import type { FullResult, Reporter, Suite } from '@playwright/test/reporter';
import { ROUTES } from './routes';
import { STAGING_SUITES, VIEWPORTS } from './staging';

const keyboardRoutes = ROUTES.filter((route) => route.status === undefined);
const keyboardChecks = keyboardRoutes.length + keyboardRoutes.filter((route) => route.persona !== null).length;

export default class StagingReporter implements Reporter {
  private suite?: Suite;

  onBegin(_config: unknown, suite: Suite): void {
    this.suite = suite;
  }

  async onEnd(result: FullResult): Promise<{ status: FullResult['status'] } | undefined> {
    if (result.status !== 'passed') return;
    const tests = this.suite?.allTests() ?? [];
    const incomplete = STAGING_SUITES.filter((name) => {
      return VIEWPORTS.some((width) => {
        const group = tests.filter((test) => basename(test.location.file) === `${name}.spec.ts` &&
          test.parent.project()?.name === `chromium-${width}`);
        const passed = group.filter((test) => test.results.length === 1 && test.results[0].status === 'passed').length;
        // Compare both declared and passing counts so filtered runs and unexpected skips fail closed.
        if (name === 'axe') return group.length !== ROUTES.length || passed !== ROUTES.length;
        if (name === 'overflow') return group.length !== 2 * ROUTES.length || passed !== (width === 320 ? 2 : 1) * ROUTES.length;
        if (name === 'keyboard') return group.length !== 2 * keyboardRoutes.length || passed !== (width === 360 ? keyboardChecks : 0);
        return passed === 0 || passed !== group.length;
      });
    });
    if (incomplete.length === 0) return;
    process.stderr.write(`Staging evidence incomplete for ${incomplete.join(', ')}.\n`);
    return { status: 'failed' };
  }
}

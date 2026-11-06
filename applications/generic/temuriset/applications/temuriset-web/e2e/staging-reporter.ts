import { basename } from 'node:path';
import type { FullResult, Reporter, Suite, TestCase } from '@playwright/test/reporter';
import { ROUTES } from './routes';
import { STAGING_JOURNEYS, STAGING_SUITES, VIEWPORTS } from './staging';

const keyboardRoutes = ROUTES.filter((route) => route.status === undefined);
const keyboardChecks = keyboardRoutes.length + keyboardRoutes.filter((route) => route.persona !== null).length;

function passed(test: TestCase): boolean {
  return test.results.length === 1 && test.results[0].status === 'passed';
}

export default class StagingReporter implements Reporter {
  private suite?: Suite;

  onBegin(_config: unknown, suite: Suite): void {
    this.suite = suite;
  }

  async onEnd(result: FullResult): Promise<{ status: FullResult['status'] } | undefined> {
    if (result.status !== 'passed') return;
    const tests = this.suite?.allTests() ?? [];
    const incomplete: string[] = STAGING_SUITES.filter((name) => {
      return VIEWPORTS.some((width) => {
        const group = tests.filter((test) => basename(test.location.file) === `${name}.spec.ts` &&
          test.parent.project()?.name === `chromium-${width}`);
        const passing = group.filter(passed).length;
        // Compare both declared and passing counts so filtered runs and unexpected skips fail closed.
        if (name === 'axe') return group.length !== ROUTES.length || passing !== ROUTES.length;
        if (name === 'overflow') return group.length !== 2 * ROUTES.length || passing !== (width === 320 ? 2 : 1) * ROUTES.length;
        return group.length !== 2 * keyboardRoutes.length || passing !== (width === 360 ? keyboardChecks : 0);
      });
    });
    for (const { name, file, project, title } of STAGING_JOURNEYS) {
      const group = tests.filter((test) => basename(test.location.file) === file && test.parent.project()?.name === project);
      const journey = group.filter((test) => test.title === title);
      if (journey.length !== 1 || group.some((test) => !passed(test))) incomplete.push(name);
    }
    if (incomplete.length === 0) return;
    process.stderr.write(`Staging evidence incomplete for ${incomplete.join(', ')}.\n`);
    return { status: 'failed' };
  }
}

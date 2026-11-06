import type { FullResult, Suite, TestCase, TestResult } from '@playwright/test/reporter';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { ROUTES } from '../../e2e/routes';
import { STAGING_JOURNEYS, VIEWPORTS } from '../../e2e/staging';
import StagingReporter from '../../e2e/staging-reporter';

function discovered(file: string, project: string, title: string, status: TestResult['status']): TestCase {
  return {
    location: { file, line: 1, column: 1 },
    parent: { project: () => ({ name: project }) },
    title,
    results: [{ status }],
  } as TestCase;
}

function baseline() {
  return VIEWPORTS.flatMap((width) => ROUTES.flatMap((route) => {
    const project = `chromium-${width}`;
    return [
      discovered('axe.spec.ts', project, 'axe', 'passed'),
      discovered('overflow.spec.ts', project, 'overflow', 'passed'),
      discovered('overflow.spec.ts', project, 'text scaling', width === 320 ? 'passed' : 'skipped'),
      ...(route.status === undefined ? [
        discovered('keyboard.spec.ts', project, 'focus visibility', width === 360 ? 'passed' : 'skipped'),
        discovered('keyboard.spec.ts', project, 'skip link', width === 360 && route.persona ? 'passed' : 'skipped'),
      ] : []),
    ];
  }));
}

function journeys() {
  return STAGING_JOURNEYS.flatMap(({ file, project, title }) => title ? [discovered(file, project, title, 'passed')] : []);
}

async function gate(tests: TestCase[]) {
  const stderr = vi.spyOn(process.stderr, 'write').mockImplementation(() => true);
  const reporter = new StagingReporter();
  reporter.onBegin(undefined, { allTests: () => tests } as Suite);
  expect(await reporter.onEnd({ status: 'passed' } as FullResult)).toEqual({ status: 'failed' });
  return stderr.mock.calls[0][0];
}

afterEach(() => vi.restoreAllMocks());

describe('staging journey evidence', () => {
  it('recognizes the exact M7 journeys and rejects the missing J04 and J05 journeys', async () => {
    expect(await gate([...baseline(), ...journeys()])).toBe('Staging evidence incomplete for J04, J05.\n');
  });

  it('rejects a passing test in the J01 file when the required journey was filtered out', async () => {
    const [j01, ...remaining] = journeys();
    const other = discovered(j01.location.file, 'chromium-1280', 'discovery keeps its filters', 'passed');
    expect(await gate([...baseline(), other, ...remaining])).toBe('Staging evidence incomplete for J01, J04, J05.\n');
  });

  it('rejects an unexpected skip of the named journey at its required viewport', async () => {
    const [j01, j02, ...remaining] = journeys();
    const skipped = discovered(j02.location.file, 'chromium-1280', j02.title, 'skipped');
    expect(await gate([...baseline(), j01, skipped, ...remaining])).toBe('Staging evidence incomplete for J02, J04, J05.\n');
  });
});

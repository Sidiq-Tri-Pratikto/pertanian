import { act, render } from '@testing-library/react';
import axe from 'axe-core';
import type { ReactElement } from 'react';

import { destinationFor } from '@/features/destinations';
import { findFeature } from '@/features/registry';
import { ComingSoonView } from '@/views/ComingSoonView';
import { DestinationView } from '@/views/DestinationView';
import { SettingsView } from '@/views/SettingsView';
import { StartView } from '@/views/StartView';

const noop = async () => {};
const CAPABILITIES = ['core', 'company_funding', 'organization_review'];

// jsdom has no layout or computed colours, so contrast and reflow are checked in Chromium by `e2e/axe.spec.ts`.
// Without CSS jsdom also shows both navigations; the design system hides one of them at every width.
async function violations(element: ReactElement): Promise<string[]> {
  const { container } = render(element);
  let result: axe.AxeResults | undefined;
  // Next links update their prefetch state while axe walks the tree.
  await act(async () => {
    result = await axe.run(container, {
      rules: { 'color-contrast': { enabled: false }, region: { enabled: false }, 'landmark-unique': { enabled: false } },
    });
  });
  return result!.violations.map((violation) => `${violation.id}: ${violation.nodes.map((node) => node.target).join(', ')}`);
}

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('accessibility of the base screens', () => {
  it.each([
    ['start', <StartView key="s" action={noop} persona={null} invalid />],
    ['home', <DestinationView key="h" persona="inovator" destination={destinationFor('home', 'inovator')} capabilities={CAPABILITIES} />],
    ['partner pitches', <DestinationView key="p" persona="mitra" destination={destinationFor('pitches', 'mitra')} capabilities={CAPABILITIES} />],
    ['coming soon', <ComingSoonView key="c" persona="inovator" feature={findFeature('kecocokan')} showSpecs />],
    ['unknown feature', <ComingSoonView key="u" persona="mitra" feature={undefined} />],
    ['settings', <SettingsView key="t" action={noop} persona="mitra" saved invalid={false} capabilities={CAPABILITIES} />],
  ])('%s has no detectable violations', async (_, element) => {
    expect(await violations(element)).toEqual([]);
  });
});

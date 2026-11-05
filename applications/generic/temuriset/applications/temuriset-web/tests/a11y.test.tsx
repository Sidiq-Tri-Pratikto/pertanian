import { act, render } from '@testing-library/react';
import axe from 'axe-core';
import type { ReactElement } from 'react';

import { destinationFor } from '@/features/destinations';
import { findFeature } from '@/features/registry';
import { ComingSoonView } from '@/views/ComingSoonView';
import { DestinationView } from '@/views/DestinationView';
import { SettingsView } from '@/views/SettingsView';
import { StartView } from '@/views/StartView';
import { CodeView } from '@/views/CodeView';
import { InvitationView } from '@/views/InvitationView';

import { makeMe } from './fixtures';

vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn(), replace: vi.fn(), refresh: vi.fn() }) }));
vi.mock('@/features/actions', () => ({ forgetPersona: async () => {} }));

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
  sessionStorage.setItem('tr_masuk', JSON.stringify({ email: 'rani@example.com', purpose: 'sign_in', returnTo: null }));
  vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('accessibility of the base screens', () => {
  it.each([
    ['sign-up', <StartView key="s" persona={null} mode="sign_up" returnTo={null} />],
    ['sign-in', <StartView key="m" persona={null} mode="sign_in" returnTo={null} />],
    ['code', <CodeView key="k" />],
    ['home', <DestinationView key="h" me={makeMe()} destination={destinationFor('home', 'inovator')} capabilities={CAPABILITIES} />],
    ['partner pitches', <DestinationView key="p" me={makeMe({ persona: 'mitra' })} destination={destinationFor('pitches', 'mitra')} capabilities={CAPABILITIES} />],
    ['coming soon', <ComingSoonView key="c" me={makeMe()} feature={findFeature('kecocokan')} showSpecs />],
    ['unknown feature', <ComingSoonView key="u" me={makeMe({ persona: 'mitra' })} feature={undefined} />],
    ['settings', <SettingsView key="t" me={makeMe()} capabilities={CAPABILITIES} members={null} invitations={null} joined />],
    [
      'organization settings',
      <SettingsView
        key="o"
        me={makeMe({ organization: true, actingAsOrganization: true })}
        capabilities={CAPABILITIES}
        members={[{ account_id: 'a', display_name: 'Bima', capabilities: ['manage_members'], version: 1 }]}
        invitations={[{ id: 'i1', email: 'eve@example.com', capabilities: ['schedule'], expires_at: '2026-11-12T02:00:00Z', status: 'pending' }]}
      />,
    ],
    [
      'invitation',
      <InvitationView
        key="i"
        me={makeMe()}
        token="t"
        invitation={{ organization_name: 'Demo', capabilities: ['edit_portfolio'], expires_at: '2026-11-12T02:00:00Z', status: 'pending' }}
      />,
    ],
    ['missing invitation', <InvitationView key="n" me={makeMe()} token="t" invitation={null} />],
  ])('%s has no detectable violations', async (_, element) => {
    expect(await violations(element)).toEqual([]);
  });
});

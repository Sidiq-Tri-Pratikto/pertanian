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

import { DocumentsPanel } from '@/features/documents/DocumentsPanel';
import { EditorView } from '@/views/portfolio/EditorView';
import { InventionsView, InventionView } from '@/views/portfolio/InventionViews';
import type { Invention } from '@/features/portfolio/model';

import { makeMe } from './fixtures';

const SAMPLE: Invention = {
  id: 'i',
  managing_party_id: 'p',
  status: 'DRAFT',
  version: 2,
  history: [1],
  published: null,
  operation_id: null,
  draft: {
    number: 1, state: 'draft', title: 'Saringan air', summary: '', problem: 'Air keruh', solution: 'Saringan', intended_users: 'Desa', sector: 'Air',
    stage: 'PILOT', keywords: [], private_notes: '', published_at: null,
    facts: [{ label: 'Kapasitas', value: '10', unit: 'L/jam', timing: 'CURRENT', provenance: 'SELF_DECLARED', key: null, document_version_id: null }],
    claims: [{ kind: 'creator', subject_name: 'Rani', party_id: null, scope: '', status: 'not_established', source: '', asserted_at: null }],
  },
};

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
    ['empty inventions', <InventionsView key="ie" me={makeMe()} inventions={[]} />],
    ['inventions', <InventionsView key="il" me={makeMe()} inventions={[{ id: 'i', status: 'PUBLISHED', title: 'Saringan', version: 2, has_draft: true, published_number: 1 }]} />],
    ...[1, 2, 3, 4].map((step) => [`editor step ${step}`, <EditorView key={`e${step}`} me={makeMe()} invention={SAMPLE} initialStep={step} />] as [string, ReactElement]),
    ['owner detail', <InventionView key="d" me={makeMe()} invention={SAMPLE} />],
    [
      'documents',
      <DocumentsPanel
        key="docs"
        me={makeMe()}
        initial={[
          {
            id: 'd1', title: 'Laporan uji', kind: 'evidence',
            grants: [{ id: 'g1', version: 1, grantee_party_id: 'p2', grantee_name: 'Mitra A', purpose: 'pitch', revoked_at: null, downloads: 0 }],
            versions: [{ number: 1, media_type: 'application/pdf', size_bytes: 10, sha256: 'x', file_state: 'AVAILABLE', extraction_state: 'NEEDS_MANUAL_INPUT', review_state: 'PROVIDED_UNREVIEWED', created_at: '' }],
          },
        ]}
      />,
    ],
    ['missing invention', <InventionView key="m" me={makeMe()} />],
  ])('%s has no detectable violations', async (_, element) => {
    expect(await violations(element)).toEqual([]);
  });
});

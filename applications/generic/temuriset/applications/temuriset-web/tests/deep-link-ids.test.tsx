import { render } from '@testing-library/react';
import { vi } from 'vitest';

import type { SupportRequest } from '@/features/needs/model';
import { SupportForm } from '@/features/needs/SupportForm';
import type { Invention } from '@/features/portfolio/model';
import { NeedsView } from '@/views/needs/NeedsViews';
import { EditorView } from '@/views/portfolio/EditorView';

import { makeMe } from './fixtures';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), refresh: vi.fn() }),
  usePathname: () => '/inventions/inv-1/edit',
}));

const ME = makeMe();

const INVENTION: Invention = {
  id: 'inv-1',
  managing_party_id: 'party-1',
  status: 'DRAFT',
  version: 1,
  draft: {
    number: 1,
    state: 'draft',
    title: 'ClearSpring',
    summary: 'Filter air bersih.',
    problem: 'Akses air bersih terbatas.',
    solution: 'Filter portabel.',
    intended_users: 'Desa.',
    sector: 'Air bersih',
    stage: 'PROTOTYPE',
    keywords: ['air'],
    facts: [],
    claims: [],
    private_notes: '',
    published_at: null,
  },
  published: null,
  history: [1],
};

const SUPPORT: SupportRequest = {
  id: 'sr-1',
  invention_id: 'inv-1',
  invention_title: 'ClearSpring',
  invention_version: 1,
  outcome: 'Uji lapangan',
  support_forms: ['funding'],
  relationship_form: 'PROJECT',
  scope: 'Dua desa',
  months: 6,
  region: 'Jawa Tengah',
  accepts_partial: true,
  accepts_noncash: false,
  noncash_description: '',
  status: 'DRAFT',
  version: 1,
  budget: null,
};

describe('stable deep-link element ids (spec 055 FR-007)', () => {
  it('provides #kata-kunci, #sektor, and #tahap on editor step 1', () => {
    const { container } = render(<EditorView me={ME} invention={INVENTION} initialStep={1} />);
    expect(container.querySelector('#kata-kunci')).not.toBeNull();
    expect(container.querySelector('#sektor')).not.toBeNull();
    expect(container.querySelector('#tahap')).not.toBeNull();
  });

  it('provides #tkt, #fakta, and #dokumen on editor step 2', () => {
    const { container } = render(<EditorView me={ME} invention={INVENTION} initialStep={2} documents={<div>Docs</div>} />);
    expect(container.querySelector('#tkt')).not.toBeNull();
    expect(container.querySelector('#fakta')).not.toBeNull();
    expect(container.querySelector('#dokumen')).not.toBeNull();
  });

  it('provides #kisaran and #bentuk on SupportForm and #baru on NeedsView', () => {
    const form = render(<SupportForm request={SUPPORT} actingPartyId="party-1" />);
    expect(form.container.querySelector('#kisaran')).not.toBeNull();
    expect(form.container.querySelector('#bentuk')).not.toBeNull();

    const list = render(<NeedsView me={ME} support={[SUPPORT]} funding={[]} published={[{ id: 'inv-1', title: 'ClearSpring' }]} fundingOn={false} />);
    expect(list.container.querySelector('#baru')).not.toBeNull();
  });
});

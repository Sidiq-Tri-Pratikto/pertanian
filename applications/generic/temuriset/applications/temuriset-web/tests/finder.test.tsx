import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';
import type { ReactElement } from 'react';

import { finderHref, sortFitItems, topDimensions, type FitItem, type MyProduct } from '@/features/discovery/fit';
import { resultCount } from '@/features/discovery/model';
import { FitTable } from '@/views/discovery/finder/FitTable';
import type { Discovery, DiscoveryItem } from '@/features/discovery/model';
import { LocaleProvider } from '@/features/i18n/LocaleProvider';
import { setAppLocale } from '@/features/i18n/t';
import { FinderView } from '@/views/discovery/finder/FinderView';

import { makeMe } from './fixtures';

const router = { push: vi.fn(), replace: vi.fn(), refresh: vi.fn() };
vi.mock('next/navigation', () => ({ useRouter: () => router }));

const PRODUCTS: MyProduct[] = [
  { id: 'inv-a', title: 'ClearSpring' },
  { id: 'inv-b', title: 'SolarBox Desa' },
];

const INVESTOR_B: DiscoveryItem & { best_fit?: unknown } = {
  subject_type: 'PARTNER',
  subject_id: 'partner-b',
  title: 'Investor B',
  card: {
    subtype: 'Investor energi desa',
    availability_label: 'Pitching dibuka',
    source_label: 'Dikonfirmasi pemilik profil',
    thesis: 'Mendanai energi surya skala kecil.',
    opportunities: [{ id: 'opp-b', title: 'Pendanaan energi surya desa' }],
  },
  curated: false,
  saved: false,
  reasons: [],
  best_fit: {
    label: 'Kecocokan kuat',
    eligibility: 'ELIGIBLE',
    fit: { lower: '88.11', upper: '94.04', coverage: '0.95' },
    invention_id: 'inv-b',
    invention_title: 'SolarBox Desa',
    opportunity_id: 'opp-b',
    matching_products: 1,
  },
};

const EMPTY_INVESTOR: DiscoveryItem = {
  subject_type: 'PARTNER',
  subject_id: 'partner-empty',
  title: 'Investor Kosong',
  card: {
    subtype: 'Investor baru',
    availability_label: 'Ketersediaan belum dikonfirmasi',
    source_label: 'Dikonfirmasi pemilik profil',
    opportunities: [],
  },
  curated: false,
  saved: false,
  reasons: [],
};

const FIT_ITEMS: FitItem[] = [
  {
    invention: { id: 'inv-a', title: 'ClearSpring', stage: 'PROTOTYPE', tkt_level: 4 },
    source: null,
    opportunity: { id: 'opp-b', title: 'Pendanaan energi surya desa', partner_party_id: 'partner-b', partner: 'Investor B' },
    preview: true,
    result: {
      opportunity_id: 'opp-b',
      opportunity_version_id: 'ov-b',
      opportunity_version: 1,
      partner_party_id: 'partner-b',
      partner: 'Investor B',
      title: 'Pendanaan energi surya desa',
      availability: { available: true, reason: null },
      eligibility: 'ELIGIBLE',
      readiness: 'READY_TO_SUBMIT',
      relevant: true,
      label: 'Kecocokan lemah',
      fit: { lower: '25.00', upper: '65.00', coverage: '0.60' },
      breakdown: [
        { id: 'sector', score: 0, status: 'MISMATCH', weight: '0.15', values: { source: 'Air dan sanitasi', target: ['Energi'] } },
        { id: 'topic', score: 25, status: 'MISMATCH', weight: '0.45', values: { matched: ['desa'], missing: ['surya'] } },
        { id: 'readiness', score: 100, status: 'MATCH', weight: '0.15', values: { stage: 'PROTOTYPE', accepted_stages: ['PROTOTYPE'], tkt: 4, min_tkt: 3 } },
        { id: 'money', score: null, status: 'UNKNOWN', weight: '0.15', values: {} },
        { id: 'form', score: null, status: 'UNKNOWN', weight: '0.30', values: {} },
        { id: 'requirements', score: null, status: 'NOT_APPLICABLE', weight: null, values: { passed: 0, failed: [], unknown: [], total: 0 } },
        { id: 'evidence', score: null, status: 'NOT_APPLICABLE', weight: null, values: { provided: 0, reviewed: 0, applicable: 0 } },
        { id: 'availability', score: 100, status: 'MATCH', weight: '0.15', values: { available: true, reason: null } },
      ],
      recommendations: [
        { kind: 'no_need', blocking: false, dimension: null, target: { invention_id: 'inv-a', field: 'new_need' }, values: {}, estimate: null },
      ],
      reasons: [],
      gap: null,
      later: [],
      rows: [],
      evidence: { provided: 0, reviewed: 0, applicable: 0, note: 'Belum ada checklist' },
    },
  },
  {
    invention: { id: 'inv-b', title: 'SolarBox Desa', stage: 'PROTOTYPE', tkt_level: 5 },
    source: { type: 'SUPPORT_REQUEST', id: 'need-b', version: 1, title: 'SolarBox Desa' },
    opportunity: { id: 'opp-b', title: 'Pendanaan energi surya desa', partner_party_id: 'partner-b', partner: 'Investor B' },
    preview: false,
    result: {
      opportunity_id: 'opp-b',
      opportunity_version_id: 'ov-b',
      opportunity_version: 1,
      partner_party_id: 'partner-b',
      partner: 'Investor B',
      title: 'Pendanaan energi surya desa',
      availability: { available: true, reason: null },
      eligibility: 'ELIGIBLE',
      readiness: 'READY_TO_SUBMIT',
      relevant: true,
      label: 'Kecocokan kuat',
      fit: { lower: '94.00', upper: '100.00', coverage: '0.95' },
      breakdown: [
        { id: 'sector', score: 100, status: 'MATCH', weight: '0.15', values: { source: 'Energi', target: ['Energi'] } },
        { id: 'topic', score: 100, status: 'MATCH', weight: '0.45', values: { matched: ['surya'], missing: [] } },
        { id: 'readiness', score: 100, status: 'MATCH', weight: '0.15', values: { stage: 'PROTOTYPE', accepted_stages: ['PROTOTYPE'], tkt: 5, min_tkt: 3 } },
        { id: 'money', score: 100, status: 'MATCH', weight: '0.15', values: {} },
        { id: 'form', score: 100, status: 'MATCH', weight: '0.30', values: { source: 'PROJECT', target: ['PROJECT'] } },
        { id: 'requirements', score: null, status: 'NOT_APPLICABLE', weight: null, values: { passed: 0, failed: [], unknown: [], total: 0 } },
        { id: 'evidence', score: null, status: 'NOT_APPLICABLE', weight: null, values: { provided: 0, reviewed: 0, applicable: 0 } },
        { id: 'availability', score: 100, status: 'MATCH', weight: '0.15', values: { available: true, reason: null } },
      ],
      recommendations: [],
      reasons: [],
      gap: null,
      later: [],
      rows: [],
      evidence: { provided: 0, reviewed: 0, applicable: 0, note: 'Belum ada checklist' },
    },
  },
];

function makePage(items: DiscoveryItem[]): Discovery {
  return {
    type: 'partners',
    sections: [
      { id: 'relevant', title: 'Sesuai produk Anda', items },
      { id: 'new', title: 'Belum cocok', items: [] },
      { id: 'curated', title: 'Pilihan kurator', items: [] },
    ],
    filters: {},
    next_cursor: null,
    total_estimate: items.length,
    relaxation: null,
  };
}

async function axeViolations(element: ReactElement): Promise<string[]> {
  const { container } = render(element);
  let result: axe.AxeResults | undefined;
  await act(async () => {
    result = await axe.run(container, { rules: { 'color-contrast': { enabled: false }, region: { enabled: false }, 'landmark-unique': { enabled: false } } });
  });
  return result!.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target).join(', ')}`);
}

afterEach(() => {
  setAppLocale('id');
  router.push.mockClear();
});

describe('investor finder revamp (spec 059)', () => {
  it('sorts fit items best first and extracts top dimensions', () => {
    const sorted = sortFitItems(FIT_ITEMS);
    expect(sorted.map((item) => item.invention.title)).toEqual(['SolarBox Desa', 'ClearSpring']);
    expect(topDimensions(FIT_ITEMS[0].result.breakdown!, 2)).toHaveLength(2);
    expect(finderHref({ sector: 'Energi' }, 'inv-b', 'partner-b')).toBe(
      '/discover?type=partners&sector=Energi&selected=partner-b&produk=inv-b',
    );
  });

  it('shows product picker, best-fit investor rows, expandable product × mandate rows, preview badge, and English mode', async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <FinderView
        me={makeMe()}
        filters={{}}
        page={makePage([INVESTOR_B as DiscoveryItem])}
        fundingOn
        matchesHref="/matches?source=SUPPORT_REQUEST:need-b"
        products={PRODUCTS}
        initialFit={FIT_ITEMS}
      />,
    );

    expect(screen.getByRole('combobox', { name: 'Cocokkan untuk' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Kecocokan dengan produk Anda' })).toBeInTheDocument();
    expect(screen.getByText('Pratinjau tanpa kebutuhan')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Siapkan pitching' })).toHaveAttribute(
      'href',
      '/pitches/new?source=SUPPORT_REQUEST:need-b&target=opp-b',
    );
    expect(screen.getByRole('link', { name: 'Buat kebutuhan untuk produk ini' })).toBeInTheDocument();

    await user.selectOptions(screen.getByRole('combobox', { name: 'Cocokkan untuk' }), 'inv-b');
    expect(router.push).toHaveBeenCalledWith('/discover?type=partners&produk=inv-b');

    rerender(
      <LocaleProvider locale="en">
        <FinderView
          me={makeMe()}
          filters={{}}
          page={makePage([INVESTOR_B as DiscoveryItem])}
          fundingOn
          matchesHref={null}
          products={PRODUCTS}
          initialFit={FIT_ITEMS}
        />
      </LocaleProvider>,
    );
    expect(screen.getByRole('combobox', { name: 'Match for' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Fit with your products' })).toBeInTheDocument();
    expect(screen.getByText('Preview without a need')).toBeInTheDocument();
  });

  it('shows an honest empty-mandate message when an investor has no active mandates', () => {
    render(
      <FinderView
        me={makeMe()}
        filters={{}}
        page={makePage([EMPTY_INVESTOR])}
        fundingOn
        matchesHref={null}
        products={PRODUCTS}
        initialFit={[]}
      />,
    );
    expect(
      screen.getByText('Investor ini belum membuka mandat. Simpan atau ikuti untuk kabar berikutnya.'),
    ).toBeInTheDocument();
  });

  it('shows "Tahap dan TKT 25 → 100" after a return, then forgets it once seen (AC81)', () => {
    window.sessionStorage.setItem(
      'tr_fit_prev',
      JSON.stringify({ 'inv-a:opp-b': { readiness: 25, topic: 25 } }),
    );
    const { unmount } = render(<FitTable items={FIT_ITEMS} returnTo="/discover?type=partners" />);
    expect(screen.getAllByText('Tahap dan TKT 25 → 100').length).toBeGreaterThan(0);
    expect(screen.queryByText(/Topik dan detail produk 25 →/)).toBeNull();
    unmount();

    render(<FitTable items={FIT_ITEMS} returnTo="/discover?type=partners" />);
    expect(screen.queryByText(/→/)).toBeNull();
  });

  it('counts one result in the singular in English', () => {
    setAppLocale('en');
    try {
      expect(resultCount(1)).toBe('1 result');
      expect(resultCount(3)).toBe('3 results');
    } finally {
      setAppLocale('id');
    }
    expect(resultCount(1)).toBe('1 hasil');
  });

  it('is axe clean', async () => {
    expect(
      await axeViolations(
        <FinderView
          me={makeMe()}
          filters={{}}
          page={makePage([INVESTOR_B as DiscoveryItem])}
          fundingOn
          matchesHref={null}
          products={PRODUCTS}
          initialFit={FIT_ITEMS}
        />,
      ),
    ).toEqual([]);
  });
});

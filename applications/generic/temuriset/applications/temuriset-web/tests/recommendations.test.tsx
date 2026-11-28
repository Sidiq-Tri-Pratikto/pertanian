import { act, render, screen } from '@testing-library/react';
import axe from 'axe-core';
import type { ReactElement } from 'react';

import { ImprovementList } from '@/components/tr/ImprovementList';
import {
  deltasFor,
  estimateText,
  recommendationAction,
  recommendationCopy,
  topImpactSteps,
  type Recommendation,
} from '@/features/discovery/recommendations';
import { LocaleProvider } from '@/features/i18n/LocaleProvider';
import { setAppLocale } from '@/features/i18n/t';
import { EditorView } from '@/views/portfolio/EditorView';

import { makeMe, PERSONAL } from './fixtures';

vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn(), replace: vi.fn(), refresh: vi.fn() }) }));

const SAMPLE_RECS: Recommendation[] = [
  {
    kind: 'requirement',
    blocking: true,
    dimension: 'requirements',
    target: { need_id: 'need-1', source_type: 'SUPPORT_REQUEST', field: 'budget' },
    values: { label: 'Kisaran biaya pilot', reason: 'Kisaran biaya pilot untuk kebutuhan ini belum diisi.', action: 'complete-budget' },
    estimate: { label: 'Kecocokan kuat', fit: { lower: '88.11', upper: '94.04', coverage: '0.95' }, gain: '14.00' },
  },
  {
    kind: 'topic',
    blocking: false,
    dimension: 'topic',
    target: { invention_id: 'inv-1', field: 'keywords' },
    values: { missing: ['pertanian', 'irigasi'], matched: ['desa'] },
    estimate: { label: 'Kecocokan potensial', fit: { lower: '54.00', upper: '80.00', coverage: '0.80' }, gain: '20.00' },
  },
  {
    kind: 'tkt_below',
    blocking: false,
    dimension: 'readiness',
    target: { invention_id: 'inv-1', field: 'tkt' },
    values: { tkt: 4, min_tkt: 6 },
    estimate: { label: 'Kecocokan potensial', fit: { lower: '52.00', upper: '70.00', coverage: '0.85' }, gain: '10.00' },
  },
  {
    kind: 'stage',
    blocking: false,
    dimension: 'readiness',
    target: { invention_id: 'inv-1', field: 'stage' },
    values: { stage: 'PROTOTYPE', accepted_stages: ['PILOT', 'WORKING'] },
    estimate: null,
  },
  {
    kind: 'sector',
    blocking: false,
    dimension: 'sector',
    target: { invention_id: 'inv-1', field: 'sector' },
    values: { source: 'Air dan sanitasi', target: ['Pertanian'] },
    estimate: null,
  },
  {
    kind: 'availability',
    blocking: false,
    dimension: 'availability',
    target: { partner_party_id: 'p-1' },
    values: { reason: 'TARGET_NOT_ACTIVE' },
    estimate: null,
  },
];

async function axeViolations(element: ReactElement): Promise<string[]> {
  const { container } = render(element);
  let result: axe.AxeResults | undefined;
  await act(async () => {
    result = await axe.run(container, { rules: { 'color-contrast': { enabled: false }, region: { enabled: false } } });
  });
  return result!.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target).join(', ')}`);
}

afterEach(() => setAppLocale('id'));

describe('recommendations (spec 058)', () => {
  it('formats conditional copy and deep-link contract addresses for every kind', () => {
    const returnTo = '/matches?source=SUPPORT_REQUEST:need-1';
    expect(recommendationAction(SAMPLE_RECS[0], returnTo)?.href).toBe(
      `/support-requests/need-1?return=${encodeURIComponent(returnTo)}#kisaran`,
    );
    expect(recommendationAction(SAMPLE_RECS[1], returnTo)?.href).toBe(
      `/inventions/inv-1/edit?step=1&return=${encodeURIComponent(returnTo)}#kata-kunci`,
    );
    expect(recommendationAction(SAMPLE_RECS[2], returnTo)?.href).toBe(
      `/inventions/inv-1/edit?step=2&return=${encodeURIComponent(returnTo)}#tkt`,
    );
    expect(recommendationAction(SAMPLE_RECS[3], returnTo)?.href).toBe('/discover?type=partners&produk=inv-1');
    expect(recommendationAction(SAMPLE_RECS[4], returnTo)?.href).toBe('/discover?type=partners&produk=inv-1');
    expect(recommendationAction(SAMPLE_RECS[5], returnTo)).toBeNull();
    expect(recommendationCopy(SAMPLE_RECS[1]).body).toContain('Bila sesuai');
    expect(estimateText(SAMPLE_RECS[1].estimate!)).toContain('54–80');
  });

  it('caps at five items with Lihat semua (n) and translates to English', () => {
    const { rerender } = render(<ImprovementList recommendations={SAMPLE_RECS} returnTo="/matches?source=SUPPORT_REQUEST:need-1" />);
    expect(screen.getByRole('heading', { name: 'Cara meningkatkan kecocokan' })).toBeInTheDocument();
    expect(screen.getByText('Lihat semua (6)')).toBeInTheDocument();
    expect(screen.getByText('Menghalangi')).toBeInTheDocument();

    rerender(
      <LocaleProvider locale="en">
        <ImprovementList recommendations={SAMPLE_RECS} />
      </LocaleProvider>,
    );
    expect(screen.getByRole('heading', { name: 'How to improve the match' })).toBeInTheDocument();
    expect(screen.getByText('See all (6)')).toBeInTheDocument();
  });

  it('computes top-3 impact steps and dimension deltas cleanly', () => {
    const top = topImpactSteps([
      { partner: 'Investor A', recommendations: SAMPLE_RECS },
      { partner: 'Investor B', recommendations: [SAMPLE_RECS[1]] },
    ]);
    expect(top[0].partners).toEqual(['Investor A', 'Investor B']);
    expect(top.length).toBeLessThanOrEqual(3);

    const deltas = deltasFor({ o1: { topic: 25, sector: 0 } }, 'o1', [
      { id: 'topic', score: 100, status: 'MATCH', weight: '0.45', values: {} },
      { id: 'sector', score: 0, status: 'MISMATCH', weight: '0.15', values: {} },
    ]);
    expect(deltas).toEqual({ topic: { before: 25, after: 100 } });
  });

  it('shows the return link and publish reminder in EditorView when opened with returnTo', () => {
    const invention = {
      id: 'inv-1',
      managing_party_id: PERSONAL,
      status: 'PUBLISHED' as const,
      version: 2,
      draft: null,
      published: {
        id: 'v1',
        number: 1,
        state: 'published' as const,
        title: 'ClearSpring',
        summary: 'Saringan air.',
        problem: 'Air keruh.',
        solution: 'Saringan bertingkat.',
        intended_users: 'Desa',
        sector: 'Air dan sanitasi',
        stage: 'PROTOTYPE' as const,
        keywords: ['air'],
        facts: [],
        claims: [],
        private_notes: '',
        published_at: '2026-11-01T00:00:00Z',
      },
      history: [1],
    };
    render(<EditorView me={makeMe()} invention={invention} initialStep={1} returnTo="/matches?source=SUPPORT_REQUEST:need-1" />);
    expect(screen.getByRole('link', { name: 'Kembali ke kecocokan' })).toHaveAttribute(
      'href',
      '/matches?source=SUPPORT_REQUEST:need-1',
    );
    expect(screen.getByRole('button', { name: 'Terbitkan, lalu kembali ke kecocokan' })).toBeInTheDocument();
  });

  it('is axe clean', async () => {
    expect(await axeViolations(<ImprovementList recommendations={SAMPLE_RECS} />)).toEqual([]);
  });
});

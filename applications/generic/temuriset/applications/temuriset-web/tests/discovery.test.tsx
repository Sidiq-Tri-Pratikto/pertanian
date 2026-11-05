import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import type { ReactElement } from 'react';

import type { Discovery, DiscoveryItem, MatchResult, MatchRun } from '@/features/discovery/model';
import { readFilters, readSource, readType } from '@/features/discovery/model';
import { DiscoverView } from '@/views/discovery/DiscoverView';
import { MatchesView } from '@/views/discovery/MatchesView';

import { makeMe } from './fixtures';

const router = { push: vi.fn(), replace: vi.fn(), refresh: vi.fn() };
vi.mock('next/navigation', () => ({ useRouter: () => router }));

type Reply = { status: number; body?: unknown };
let replies: Reply[] = [];
const fetchMock = vi.fn(async () => {
  const reply = replies.shift() ?? { status: 500, body: {} };
  return new Response(reply.body === undefined ? null : JSON.stringify(reply.body), { status: reply.status });
});

beforeEach(() => {
  replies = [];
  fetchMock.mockClear();
  router.refresh.mockClear();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => vi.unstubAllGlobals());

async function violations(element: ReactElement): Promise<string[]> {
  const { container } = render(element);
  let result: axe.AxeResults | undefined;
  await act(async () => {
    result = await axe.run(container, { rules: { 'color-contrast': { enabled: false }, region: { enabled: false }, 'landmark-unique': { enabled: false } } });
  });
  return result!.violations.map((violation) => `${violation.id}: ${violation.nodes.map((node) => node.target).join(', ')}`);
}

/** A golden result from the service contract, with its placeholder ids made unique. */
function golden(name: string, id: string): MatchResult {
  let counter = 0;
  const text = readFileSync(resolve(process.cwd(), `../../contracts/golden/${name}.json`), 'utf8');
  return JSON.parse(text.replace(/<id>/g, () => `${id}-0000-4000-8000-${String(counter++).padStart(12, '0')}`)) as MatchResult;
}

const SOURCE = { type: 'SUPPORT_REQUEST' as const, id: '11111111-1111-4111-8111-111111111111' };

function runOf(results: MatchResult[], excluded: MatchResult[] = []): MatchRun {
  return {
    run_id: 'r1',
    created_at: '2026-11-05T00:00:00Z',
    engine: 'lexical-rules@1',
    policy_versions: { 'matching-weights': 1, 'fit-thresholds': 1 },
    source: { type: 'SUPPORT_REQUEST', id: SOURCE.id, version: 2, title: 'ClearSpring' },
    results,
    excluded,
    operation_id: null,
  };
}

const CLEARSPRING: DiscoveryItem = {
  subject_type: 'INVENTION',
  subject_id: 'inv-f01',
  title: 'ClearSpring',
  card: { summary: 'Filter air sederhana.', sector: 'Air dan sanitasi', stage: 'PROTOTYPE', managing_party_name: 'Rani' },
  curated: false,
  saved: false,
  reasons: ['Sesuai sektor pada profil Anda: Air dan sanitasi'],
};

const RAISE: DiscoveryItem = {
  subject_type: 'FUNDING_REQUEST',
  subject_id: 'fraise01',
  title: 'Demo Circular Materials Ltd',
  card: {
    financing_stage: 'pre_seed',
    currency: 'USD',
    target_amount: '500000.0000',
    desired_min: '50000.0000',
    desired_max: '100000.0000',
    inventions: [
      { invention_id: 'inv-f04', title: 'LoopMaterial' },
      { invention_id: 'inv-f05', title: 'ReFormPress' },
    ],
  },
  curated: false,
  saved: true,
  reasons: [],
};

function page(overrides: Partial<Discovery> = {}, items: Record<string, DiscoveryItem[]> = {}): Discovery {
  return {
    type: 'inventions',
    sections: [
      { id: 'relevant', title: 'Sesuai profil Anda', items: items.relevant ?? [] },
      { id: 'new', title: 'Baru diterbitkan', items: items.new ?? [] },
      { id: 'curated', title: 'Pilihan kurator', items: items.curated ?? [] },
    ],
    filters: {},
    next_cursor: null,
    total_estimate: 0,
    relaxation: null,
    ...overrides,
  };
}

describe('discovery (S03)', () => {
  it('shows result types as separate links and groups results in labelled sections', () => {
    render(<DiscoverView me={makeMe({ persona: 'mitra' })} type="inventions" filters={{}} page={page({ total_estimate: 1 }, { relevant: [CLEARSPRING] })} fundingOn matchesHref={null} />);

    const types = within(screen.getByRole('navigation', { name: 'Jenis hasil' }));
    expect(types.getByRole('link', { name: 'Inovasi' })).toHaveAttribute('aria-current', 'page');
    expect(types.getByRole('link', { name: 'Pendanaan Perusahaan' })).toHaveAttribute('href', '/discover?type=funding');
    expect(screen.getByRole('heading', { level: 2, name: 'Sesuai profil Anda' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { level: 2, name: 'Pilihan kurator' })).toBeNull();
    expect(screen.getByText('Sesuai sektor pada profil Anda: Air dan sanitasi')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Lihat inovasi' })).toHaveAttribute('href', '/inventions/inv-f01');
  });

  it('hides company funding when the deployment does not run it', () => {
    render(<DiscoverView me={makeMe({ persona: 'mitra' })} type="inventions" filters={{}} page={page()} fundingOn={false} matchesHref={null} />);

    expect(screen.queryByRole('link', { name: 'Pendanaan Perusahaan' })).toBeNull();
  });

  it('shows one card per raise with both inventions and the per-investor range', () => {
    render(<DiscoverView me={makeMe({ persona: 'mitra' })} type="funding" filters={{}} page={page({ type: 'funding', total_estimate: 1 }, { new: [RAISE] })} fundingOn matchesHref={null} />);

    expect(screen.getAllByRole('article')).toHaveLength(1);
    expect(screen.getByRole('link', { name: 'LoopMaterial' })).toHaveAttribute('href', '/inventions/inv-f04');
    expect(screen.getByRole('link', { name: 'ReFormPress' })).toBeInTheDocument();
    expect(screen.getByText(/50\.000–100\.000/)).toBeInTheDocument();
  });

  it('explains empty filters, offers "Hapus semua filter" and the deliberate relaxation, and keeps the values', () => {
    const empty = page({ filters: { sector: 'Pertanian', stage: 'IDEA' }, relaxation: { remove: 'sector', label: 'Hapus filter sektor', total_estimate: 1 } });
    render(<DiscoverView me={makeMe({ persona: 'mitra' })} type="inventions" filters={{ sector: 'Pertanian', stage: 'IDEA' }} page={empty} fundingOn matchesHref={null} />);

    expect(screen.getByRole('heading', { name: 'Tidak ada hasil untuk filter ini' })).toBeInTheDocument();
    expect(screen.getByText(/Sektor "Pertanian", Tahap "IDEA". Syarat tidak dilonggarkan tanpa pilihan Anda./)).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: 'Hapus semua filter' })[0]).toHaveAttribute('href', '/discover?type=inventions');
    expect(screen.getByRole('link', { name: 'Hapus filter sektor (1 hasil)' })).toHaveAttribute('href', '/discover?type=inventions&stage=IDEA');
    expect(screen.getByRole('combobox', { name: 'Sektor' })).toHaveDisplayValue('Pertanian');
  });

  it('saves and hides for the acting party, then refreshes', async () => {
    const user = userEvent.setup();
    replies = [{ status: 200, body: {} }, { status: 200, body: {} }];
    render(<DiscoverView me={makeMe({ persona: 'mitra' })} type="inventions" filters={{}} page={page({ total_estimate: 1 }, { new: [CLEARSPRING] })} fundingOn matchesHref={null} />);

    await user.click(screen.getByRole('button', { name: 'Simpan: ClearSpring' }));
    await user.click(screen.getByRole('button', { name: 'Kurang relevan: ClearSpring' }));

    await waitFor(() => expect(router.refresh).toHaveBeenCalledTimes(2));
    const [path, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect([path, init.method]).toEqual(['/api/v1/saved-items/INVENTION/inv-f01', 'PUT']);
    expect((fetchMock.mock.calls[1] as unknown as [string])[0]).toBe('/api/v1/discovery-feedback/INVENTION/inv-f01');
  });

  it('says a failed save did not happen', async () => {
    const user = userEvent.setup();
    replies = [{ status: 500, body: {} }];
    render(<DiscoverView me={makeMe({ persona: 'mitra' })} type="inventions" filters={{}} page={page({ total_estimate: 1 }, { new: [CLEARSPRING] })} fundingOn matchesHref={null} />);

    await user.click(screen.getByRole('button', { name: 'Simpan: ClearSpring' }));

    expect(await screen.findByText('Belum tersimpan. Coba lagi.')).toHaveAttribute('role', 'status');
    expect(router.refresh).not.toHaveBeenCalled();
  });

  it('offers an inventor the way to matching', () => {
    render(<DiscoverView me={makeMe()} type="partners" filters={{}} page={page({ type: 'partners' })} fundingOn matchesHref="/matches?source=SUPPORT_REQUEST:x" />);

    expect(screen.getByRole('link', { name: 'Lihat kecocokan untuk kebutuhan Anda' })).toHaveAttribute('href', '/matches?source=SUPPORT_REQUEST:x');
  });

  it('reads the address safely', () => {
    expect(readType('funding', 'inovator')).toBe('funding');
    expect(readType('evil', 'mitra')).toBe('inventions');
    expect(readType(undefined, 'inovator')).toBe('partners');
    expect(readFilters({ q: 'air', sector: ['Energi', 'x'], other: 'y' })).toEqual({ q: 'air', sector: 'Energi' });
    expect(readSource(`SUPPORT_REQUEST:${SOURCE.id}`)).toEqual(SOURCE);
    expect(readSource('DROP:1')).toBeNull();
  });

  it('has no axe violations', async () => {
    expect(await violations(<DiscoverView me={makeMe({ persona: 'mitra' })} type="inventions" filters={{}} page={page({ total_estimate: 2 }, { relevant: [CLEARSPRING], new: [RAISE] })} fundingOn matchesHref={null} />)).toEqual([]);
  });
});

describe('matches (S10)', () => {
  it('runs matching, then shows the gap and "Lengkapi kisaran biaya" with a return path', async () => {
    replies = [{ status: 201, body: runOf([], [golden('match-f01gap-a1', 'aaaaaaaa')]) }];
    render(<MatchesView me={makeMe()} source={SOURCE} externals={[]} />);

    expect(screen.getByRole('status')).toHaveTextContent('Menghitung kecocokan');
    const card = await screen.findByRole('article');
    expect(within(card).getByText('Perlu konfirmasi')).toBeInTheDocument();
    expect(within(card).getByText('Perlu dilengkapi: Kisaran biaya pilot untuk kebutuhan ini belum diisi.')).toBeInTheDocument();
    expect(within(card).getByRole('link', { name: 'Lengkapi kisaran biaya' })).toHaveAttribute(
      'href',
      `/support-requests/${SOURCE.id}?return=${encodeURIComponent(`/matches?source=SUPPORT_REQUEST:${SOURCE.id}`)}`,
    );
    const [path, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(path).toBe('/api/v1/matches');
    expect((init.headers as Record<string, string>)['Idempotency-Key']).toBeTruthy();
  });

  it('shows a strong match with three reasons, separate eligibility, readiness and fit, and "Siapkan pitching"', async () => {
    replies = [{ status: 201, body: runOf([golden('match-f01-a1', 'bbbbbbbb')]) }];
    render(<MatchesView me={makeMe()} source={SOURCE} externals={[]} />);

    const card = await screen.findByRole('article');
    expect(within(card).getByText('Kecocokan kuat').closest('.tr-status')).not.toHaveClass('tr-status--success');
    expect(within(card).getByText('Memenuhi syarat masuk')).toBeInTheDocument();
    expect(within(card).getByText('Siap dikirim')).toBeInTheDocument();
    expect(within(card).getByText('88,11–94,04 · informasi 95%')).toBeInTheDocument();
    expect(within(card).getAllByRole('listitem').filter((item) => item.closest('.tr-reasons'))).toHaveLength(3);
    expect(within(card).getByRole('link', { name: 'Siapkan pitching' })).toBeInTheDocument();
    expect(within(card).getByText(/bukan peluang pendanaan/)).toBeInTheDocument();
    expect(within(card).getByText('Untuk tahap berikutnya. Tidak menghalangi pengajuan.')).toBeInTheDocument();
  });

  it('puts an incompatible target under "Mandat tidak direkomendasikan" with its reason', async () => {
    replies = [{ status: 201, body: runOf([], [golden('match-f03-d1', 'cccccccc')]) }];
    render(<MatchesView me={makeMe()} source={SOURCE} externals={[]} />);

    expect(await screen.findByText('Mandat tidak direkomendasikan (1)')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Belum ada mandat yang sesuai' })).toBeInTheDocument();
    expect(screen.getByText(/Menghalangi: Fitur baru direncanakan/)).toBeInTheDocument();
  });

  it('keeps the source and offers a retry when matching fails', async () => {
    const user = userEvent.setup();
    replies = [
      { status: 503, body: { error: { code: 'SERVICE_UNAVAILABLE', message: 'Layanan sedang sibuk. Coba lagi sebentar lagi.', request_id: 'ref_1', recovery: { retryable: true } } } },
      { status: 201, body: runOf([golden('match-f01-a1', 'dddddddd')]) },
    ];
    render(<MatchesView me={makeMe()} source={SOURCE} externals={[]} />);

    expect(await screen.findByRole('alert')).toHaveTextContent('Layanan sedang sibuk.');
    await user.click(screen.getByRole('button', { name: 'Coba lagi' }));

    expect(await screen.findByText('Kecocokan kuat')).toBeInTheDocument();
    const bodies = fetchMock.mock.calls.map((call) => JSON.parse(String((call as unknown as [string, RequestInit])[1].body)));
    expect(bodies.every((body) => body.source_id === SOURCE.id)).toBe(true);
  });

  it('shows an external form as another site and never as a sent pitch (AC24)', async () => {
    replies = [{ status: 201, body: runOf([]) }];
    render(<MatchesView me={makeMe()} source={SOURCE} externals={[{ id: 'e', name: 'Dana Riset E', url: 'https://example.org/formulir-demo' }]} />);

    expect(await screen.findByRole('heading', { name: 'Dana Riset E' })).toBeInTheDocument();
    expect(screen.getByText(/membuka situs lain dan bukan pitching yang terkirim/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Buka formulir mitra/ })).toHaveAttribute('href', 'https://example.org/formulir-demo');
  });

  it('has no axe violations', async () => {
    replies = [{ status: 201, body: runOf([golden('match-f01-a1', 'eeeeeeee')], [golden('match-f03-d1', 'ffffffff')]) }];
    const results = await violations(<MatchesView me={makeMe()} source={SOURCE} externals={[]} />);
    expect(results).toEqual([]);
  });
});

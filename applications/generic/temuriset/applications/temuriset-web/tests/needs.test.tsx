import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';
import type { ReactElement } from 'react';

import type { FundingRequest, SupportRequest } from '@/features/needs/model';
import { needsRange } from '@/features/needs/model';
import { DestinationView } from '@/views/DestinationView';
import { destinationFor } from '@/features/destinations';
import { FUNDING_OFF, FundingEditView, FundingView, NeedsView, SupportView } from '@/views/needs/NeedsViews';

import { makeMe } from './fixtures';

const router = { push: vi.fn(), replace: vi.fn(), refresh: vi.fn() };
vi.mock('next/navigation', () => ({ useRouter: () => router }));

// Testing Library normalizes the no-break space between currency and digits to a plain space.
const F01: SupportRequest = {
  id: 'sr1',
  version: 1,
  invention_id: 'inv1',
  invention_version: 1,
  invention_title: 'Saringan air keramik desa',
  outcome: 'Validasi prototipe enam bulan',
  support_forms: ['project_funding', 'testing_support'],
  relationship_form: 'PROJECT',
  scope: 'Validasi prototipe',
  months: 6,
  region: 'Indonesia',
  accepts_partial: true,
  accepts_noncash: false,
  noncash_description: '',
  status: 'DRAFT',
  operation_id: null,
  budget: {
    min: '20000.0000',
    max: '30000.0000',
    currency: 'USD',
    basis: 'total_period',
    period: '6 bulan',
    scope: 'biaya pilot enam bulan',
    estimated_on: null,
    assumptions: '',
    unknown_reason: null,
    financial: true,
    lines: [],
    lines_total: null,
    lines_explanation: '',
  },
};

const OPEN: SupportRequest = { ...F01, id: 'sr2', budget: { ...F01.budget!, min: null, max: null, currency: null, unknown_reason: 'not_determined' } };

const FRAISE01: FundingRequest = {
  id: 'fr1',
  version: 1,
  subject_type: 'EXISTING_ENTITY',
  subject_label: 'Demo Circular Materials Ltd',
  legal_entity: { id: 'le1', name: 'Demo Circular Materials Ltd', jurisdiction: 'Indonesia', registration_reference: '', review_status: 'declared' },
  proposed_name: '',
  financing_stage: 'pre_seed',
  financing_form: 'equity',
  currency: 'USD',
  target_amount: '500000.0000',
  desired_min: '50000.0000',
  desired_max: '100000.0000',
  accepts_partial: true,
  accepts_syndicated: true,
  intended_use: 'Mengembangkan dua inovasi perusahaan',
  timing: '',
  inventions: [
    { invention_id: 'f04', version: 1, title: 'LoopMaterial' },
    { invention_id: 'f05', version: 1, title: 'ReFormPress' },
  ],
  status: 'ACTIVE',
  operation_id: null,
};

type Reply = { status: number; body?: unknown };
let replies: Reply[] = [];
const fetchMock = vi.fn(async () => {
  const reply = replies.shift() ?? { status: 500, body: {} };
  return new Response(reply.body === undefined ? null : JSON.stringify(reply.body), { status: reply.status });
});

function sent(index: number) {
  const [path, init] = fetchMock.mock.calls[index] as unknown as [string, RequestInit];
  return { path, method: init?.method, body: init?.body ? JSON.parse(String(init.body)) : undefined };
}

beforeEach(() => {
  replies = [];
  fetchMock.mockClear();
  Object.values(router).forEach((mock) => mock.mockClear());
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('support requests (S06)', () => {
  it('labels F01 money with subject, currency, period and scope (UX-05)', () => {
    render(<SupportView me={makeMe()} request={F01} />);

    const summary = screen.getByRole('region', { name: 'Ringkasan' });
    expect(within(summary).getByText('Dukungan Proyek')).toBeInTheDocument();
    expect(within(summary).getByText('USD 20.000–30.000')).toBeInTheDocument();
    expect(within(summary).getByText('selama 6 bulan', { exact: false })).toBeInTheDocument();
    expect(within(summary).getByText('Cakupan: biaya pilot enam bulan')).toBeInTheDocument();
    expect(within(summary).getByText('Bentuk dukungan: Pendanaan proyek, Dukungan pengujian')).toBeInTheDocument();
  });

  it('reads an open range as "Belum ditentukan" and puts it in Beranda\'s queue', () => {
    expect(needsRange(OPEN)).toBe(true);
    expect(needsRange(F01)).toBe(false);
    expect(needsRange({ ...OPEN, status: 'CLOSED' })).toBe(false);

    render(<SupportView me={makeMe()} request={OPEN} />);
    expect(within(screen.getByRole('region', { name: 'Ringkasan' })).getByText('Belum ditentukan')).toBeInTheDocument();

    render(
      <DestinationView
        me={makeMe()}
        destination={destinationFor('home', 'inovator')}
        capabilities={['core']}
        queue={[{ href: '/support-requests/sr2', label: 'Lengkapi kisaran biaya pilot untuk kebutuhan ini', context: 'Validasi' }]}
      />,
    );
    expect(screen.getByRole('link', { name: 'Lengkapi kisaran biaya pilot untuk kebutuhan ini' })).toHaveAttribute('href', '/support-requests/sr2');
  });

  it('keeps both values and focuses the error summary when the maximum is below the minimum', async () => {
    replies = [
      {
        status: 422,
        body: {
          error: {
            code: 'VALIDATION_FAILED',
            message: 'Ada isian yang belum valid.',
            request_id: 'ref_1',
            recovery: { retryable: false },
            details: [{ loc: ['body', 'budget', 'max'], msg: 'Biaya maksimum tidak boleh lebih kecil dari biaya minimum.', type: 'budget' }],
          },
        },
      },
    ];
    render(<SupportView me={makeMe()} request={F01} />);
    const min = screen.getByRole('textbox', { name: /Biaya minimum/ });
    const max = screen.getByRole('textbox', { name: /Biaya maksimum/ });
    await userEvent.clear(min);
    await userEvent.type(min, '30000');
    await userEvent.clear(max);
    await userEvent.type(max, '20000');
    await userEvent.click(screen.getByRole('button', { name: 'Simpan kebutuhan' }));

    const summary = await screen.findByRole('group', { name: 'Masih ada yang perlu diperbaiki' });
    await waitFor(() => expect(summary).toHaveFocus());
    expect(within(summary).getByRole('link', { name: 'Biaya maksimum tidak boleh lebih kecil dari biaya minimum.' })).toHaveAttribute('href', '#sr-max');
    expect(min).toHaveValue('30000');
    expect(max).toHaveValue('20000');
    expect(sent(0).body.budget).toMatchObject({ min: '30000', max: '20000', currency: 'USD' });
    expect(sent(0).body.expected_version).toBe(1);
  });

  it('returns to the match it was opened from after saving', async () => {
    replies = [{ status: 200, body: { ...F01, version: 2 } }];
    render(<SupportView me={makeMe()} request={F01} returnTo="/discover?tahap=PROTOTYPE" />);

    await userEvent.click(screen.getByRole('button', { name: 'Simpan kebutuhan' }));

    await waitFor(() => expect(router.push).toHaveBeenCalledWith('/discover?tahap=PROTOTYPE'));
    expect(screen.getByRole('link', { name: 'Kembali' })).toHaveAttribute('href', '/discover?tahap=PROTOTYPE');
  });

  it('activates a draft and reports a missing field from the service', async () => {
    replies = [
      {
        status: 422,
        body: {
          error: {
            code: 'VALIDATION_FAILED',
            message: 'Ada isian yang belum valid.',
            request_id: 'ref_2',
            recovery: { retryable: false },
            details: [{ loc: ['body', 'support_forms'], msg: 'Pilih setidaknya satu bentuk dukungan.', type: 'activation' }],
          },
        },
      },
    ];
    render(<SupportView me={makeMe()} request={{ ...F01, support_forms: [] }} />);

    await userEvent.click(screen.getByRole('button', { name: 'Aktifkan kebutuhan' }));

    expect(await screen.findByRole('link', { name: 'Pilih setidaknya satu bentuk dukungan.' })).toHaveAttribute('href', '#sr-forms');
    expect(sent(0)).toMatchObject({ path: '/api/v1/support-requests/sr1/activate', method: 'POST' });
  });

  it('lists needs and raises, and starts a need for the chosen invention', async () => {
    replies = [{ status: 201, body: { ...F01, id: 'sr9' } }];
    render(<NeedsView me={makeMe()} support={[F01]} funding={[FRAISE01]} published={[{ id: 'inv1', title: 'Saringan air keramik desa' }]} fundingOn invention="inv1" />);

    expect(screen.getByRole('heading', { name: 'Validasi prototipe enam bulan' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Demo Circular Materials Ltd' })).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Tambah kebutuhan dukungan' }));

    await waitFor(() => expect(router.push).toHaveBeenCalledWith('/support-requests/sr9'));
    expect(sent(0).body).toEqual({ acting_party_id: makeMe().active_party_id, invention_id: 'inv1' });
  });
});

describe('company funding (S07)', () => {
  it('shows one raise card with target and contribution apart and both inventions (UX-06)', () => {
    render(<FundingView me={makeMe()} request={FRAISE01} fundingOn />);

    const card = screen.getByRole('article');
    expect(within(card).getByText('Target Pendanaan')).toBeInTheDocument();
    expect(within(card).getByText('USD 500.000')).toBeInTheDocument();
    expect(within(card).getByText('Kisaran kontribusi per investor')).toBeInTheDocument();
    expect(within(card).getByText('USD 50.000–100.000')).toBeInTheDocument();
    expect(within(card).getByText('2 inovasi terkait')).toBeInTheDocument();
    expect(within(card).getByRole('link', { name: 'LoopMaterial, versi 1' })).toHaveAttribute('href', '/inventions/f04');
    expect(within(card).getByText('Tahap pendanaan')).toBeInTheDocument();
    expect(within(card).queryByText(/valuasi|%/i)).toBeNull();
    expect(screen.getByRole('link', { name: 'Ubah pendanaan' })).toHaveAttribute('href', '/funding-requests/fr1/edit');
  });

  it('labels a company not founded yet', () => {
    render(<FundingView me={makeMe()} request={{ ...FRAISE01, subject_type: 'PROPOSED_ENTITY', legal_entity: null, proposed_name: 'PT Loop' }} fundingOn />);

    expect(screen.getByText('Perusahaan belum didirikan')).toBeInTheDocument();
  });

  it('explains when company funding is off and offers nothing editable', () => {
    render(<FundingEditView me={makeMe()} request={FRAISE01} entities={[]} published={[]} fundingOn={false} />);

    expect(screen.getByText(FUNDING_OFF)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Simpan pendanaan' })).toBeNull();
    expect(screen.queryByRole('textbox')).toBeNull();
  });

  it('declares a new company, then saves the raise against the version it read', async () => {
    replies = [
      { status: 201, body: { id: 'le2', name: 'PT Loop Material', jurisdiction: '', registration_reference: '', review_status: 'declared' } },
      { status: 200, body: { ...FRAISE01, version: 2 } },
    ];
    const draft: FundingRequest = { ...FRAISE01, subject_type: 'PROPOSED_ENTITY', legal_entity: null, inventions: [], target_amount: null, desired_min: null, desired_max: null, currency: null };
    render(<FundingEditView me={makeMe()} request={draft} entities={[]} published={[{ id: 'f04', title: 'LoopMaterial' }]} fundingOn />);

    await userEvent.selectOptions(screen.getByRole('combobox', { name: /Status perusahaan/ }), 'EXISTING_ENTITY');
    await userEvent.type(screen.getByRole('textbox', { name: /Nama badan hukum/ }), 'PT Loop Material');
    await userEvent.selectOptions(screen.getByRole('combobox', { name: /Mata uang/ }), 'USD');
    await userEvent.type(screen.getByRole('textbox', { name: /Target Pendanaan/ }), '500000');
    await userEvent.click(screen.getByRole('checkbox', { name: 'LoopMaterial' }));
    await userEvent.click(screen.getByRole('button', { name: 'Simpan pendanaan' }));

    await waitFor(() => expect(router.push).toHaveBeenCalledWith('/funding-requests/fr1'));
    expect(sent(0)).toMatchObject({ path: '/api/v1/legal-entities', method: 'POST', body: { name: 'PT Loop Material' } });
    expect(sent(1).body).toMatchObject({ subject_type: 'EXISTING_ENTITY', legal_entity_id: 'le2', target_amount: '500000', currency: 'USD', invention_ids: ['f04'], expected_version: 1 });
    expect(sent(1).body).not.toHaveProperty('valuation');
  });

  it('shows the service refusal with its reference when company funding was switched off meanwhile', async () => {
    replies = [{ status: 403, body: { error: { code: 'CAPABILITY_UNAVAILABLE', message: 'Fitur ini tidak tersedia pada layanan ini.', request_id: 'ref_9', recovery: { retryable: false } } } }];
    render(<FundingEditView me={makeMe()} request={{ ...FRAISE01, legal_entity: FRAISE01.legal_entity }} entities={[FRAISE01.legal_entity!]} published={[]} fundingOn />);

    await userEvent.click(screen.getByRole('button', { name: 'Simpan pendanaan' }));

    expect(await screen.findByText(/Fitur ini tidak tersedia pada layanan ini\. Kode rujukan: ref_9/)).toBeInTheDocument();
  });
});

async function violations(element: ReactElement): Promise<string[]> {
  const { container } = render(element);
  let result: axe.AxeResults | undefined;
  await act(async () => {
    result = await axe.run(container, { rules: { 'color-contrast': { enabled: false }, region: { enabled: false }, 'landmark-unique': { enabled: false } } });
  });
  return result!.violations.map((violation) => `${violation.id}: ${violation.nodes.map((node) => node.target).join(', ')}`);
}

describe('accessibility of the needs screens', () => {
  it.each([
    ['needs list', <NeedsView key="l" me={makeMe()} support={[F01, OPEN]} funding={[FRAISE01]} published={[{ id: 'inv1', title: 'Saringan' }]} fundingOn />],
    ['empty needs, funding off', <NeedsView key="e" me={makeMe()} support={[]} funding={[]} published={[]} fundingOn={false} />],
    ['support detail', <SupportView key="s" me={makeMe()} request={F01} />],
    ['funding detail', <FundingView key="f" me={makeMe()} request={FRAISE01} fundingOn />],
    ['funding editor', <FundingEditView key="fe" me={makeMe()} request={FRAISE01} entities={[FRAISE01.legal_entity!]} published={[{ id: 'f04', title: 'LoopMaterial' }]} fundingOn />],
  ])('%s has no detectable violations', async (_, element) => {
    expect(await violations(element)).toEqual([]);
  });
});

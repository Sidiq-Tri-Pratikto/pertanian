import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';
import type { ReactElement } from 'react';

import { InvestorDigestToggle } from '@/features/subscriptions/InvestorDigestToggle';
import { keywordsOf } from '@/features/subscriptions/api';
import { ConfirmView } from '@/views/subscriptions/ConfirmView';
import { ManageView } from '@/views/subscriptions/ManageView';
import { SubscribeView } from '@/views/subscriptions/SubscribeView';
import { TeaserView } from '@/views/subscriptions/TeaserView';

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

function sent(index: number) {
  const [path, init] = fetchMock.mock.calls[index] as unknown as [string, RequestInit];
  return { path, method: init.method, body: init.body ? JSON.parse(String(init.body)) : undefined };
}

const failure = (code: string, message: string) => ({ error: { code, message, request_id: 'ref_3', recovery: { retryable: false } } });

const ACTIVE = { email: 'in***@example.com', topics: { sectors: ['Energi'], stages: [], keywords: ['surya'] }, status: 'ACTIVE' as const, confirmed_at: '2026-11-15T10:00:00Z' };

const TEASER = {
  id: '11111111-1111-4111-8111-111111111111',
  title: 'ClearSpring',
  summary: 'Filter air tenaga surya untuk desa.',
  sector: 'Air dan sanitasi',
  stage: 'PROTOTYPE' as const,
  keywords: ['filter', 'air'],
  inventor_name: 'Inovator di TemuRiset',
  published_at: '2026-11-10T10:00:00Z',
};

async function violations(element: ReactElement): Promise<string[]> {
  const { container } = render(element);
  let result: axe.AxeResults | undefined;
  await act(async () => {
    result = await axe.run(container, { rules: { 'color-contrast': { enabled: false }, region: { enabled: false } } });
  });
  return result!.violations.map((violation) => violation.id);
}

describe('quick subscription (spec 046)', () => {
  it('asks for an email and at least one topic before sending anything', async () => {
    render(<SubscribeView />);
    await userEvent.click(screen.getByRole('button', { name: 'Berlangganan' }));

    const summary = screen.getByRole('group', { name: 'Masih ada yang perlu diperbaiki' });
    await waitFor(() => expect(summary).toHaveFocus());
    expect(screen.getByRole('link', { name: 'Tulis alamat email Anda.' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Pilih setidaknya satu sektor, tahap, atau kata kunci.' })).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('sends the email with topics and says to check the inbox', async () => {
    replies = [{ status: 202, body: { status: 'check_email' } }];
    render(<SubscribeView />);

    await userEvent.type(screen.getByLabelText(/Email/), 'investor@example.com');
    await userEvent.click(screen.getByLabelText('Air dan sanitasi'));
    await userEvent.click(screen.getByLabelText('Prototipe'));
    await userEvent.type(screen.getByLabelText('Kata kunci'), 'filter air, surya');
    await userEvent.click(screen.getByRole('button', { name: 'Berlangganan' }));

    expect(await screen.findByRole('heading', { name: 'Periksa email Anda' })).toBeInTheDocument();
    expect(sent(0)).toMatchObject({ path: '/api/v1/subscriptions', body: { email: 'investor@example.com', topics: { sectors: ['Air dan sanitasi'], stages: ['PROTOTYPE'], keywords: ['filter air', 'surya'] } } });
  });

  it('keeps the form and shows the reason when the service refuses', async () => {
    replies = [{ status: 429, body: failure('RATE_LIMITED', 'Terlalu banyak permintaan. Tunggu sebentar lalu coba lagi.') }];
    render(<SubscribeView />);

    await userEvent.type(screen.getByLabelText(/Email/), 'investor@example.com');
    await userEvent.click(screen.getByLabelText('Energi'));
    await userEvent.click(screen.getByRole('button', { name: 'Berlangganan' }));

    expect(await screen.findByText('Terlalu banyak permintaan. Tunggu sebentar lalu coba lagi.')).toBeInTheDocument();
    expect(screen.getByLabelText(/Email/)).toHaveValue('investor@example.com');
  });

  it('splits keywords and drops repeats', () => {
    expect(keywordsOf(' air , surya, air,,  a, b, c, d')).toEqual(['air', 'surya', 'a', 'b', 'c']);
  });

  it('has no axe violations', async () => {
    expect(await violations(<SubscribeView />)).toEqual([]);
  });
});

describe('confirm and manage links', () => {
  it('confirms only on the button, then links to the manage page', async () => {
    replies = [{ status: 200, body: { ...ACTIVE, manage_token: 'manage-token-123456789012' } }];
    render(<ConfirmView token="confirm-token-1234567890" />);
    expect(fetchMock).not.toHaveBeenCalled();

    await userEvent.click(screen.getByRole('button', { name: 'Konfirmasi langganan' }));

    expect(await screen.findByRole('heading', { name: 'Langganan aktif' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Ubah minat atau berhenti berlangganan' })).toHaveAttribute('href', '/langganan/atur?token=manage-token-123456789012');
    expect(sent(0)).toMatchObject({ path: '/api/v1/subscriptions/confirm', body: { token: 'confirm-token-1234567890' } });
  });

  it('explains a used or expired confirmation link', async () => {
    replies = [{ status: 404, body: failure('NOT_FOUND', 'Data yang diminta tidak ditemukan.') }];
    render(<ConfirmView token="old-token-12345678901234" />);
    await userEvent.click(screen.getByRole('button', { name: 'Konfirmasi langganan' }));
    expect(await screen.findByText(/sudah dipakai atau kedaluwarsa/)).toBeInTheDocument();
  });

  it('shows the topics, saves a change and unsubscribes', async () => {
    replies = [
      { status: 200, body: ACTIVE },
      { status: 200, body: { ...ACTIVE, topics: { sectors: ['Energi', 'Material'], stages: [], keywords: ['surya'] } } },
      { status: 200, body: { ...ACTIVE, status: 'UNSUBSCRIBED' } },
    ];
    render(<ManageView token="manage-token-123456789012" />);

    expect(await screen.findByLabelText('Energi')).toBeChecked();
    expect(screen.getByLabelText('Kata kunci')).toHaveValue('surya');
    await userEvent.click(screen.getByLabelText('Material'));
    await userEvent.click(screen.getByRole('button', { name: 'Simpan minat' }));
    await waitFor(() => expect(screen.getAllByText('Tersimpan').length).toBeGreaterThan(0));
    await userEvent.click(screen.getByRole('button', { name: 'Berhenti berlangganan' }));

    expect(await screen.findByRole('heading', { name: 'Anda sudah berhenti berlangganan' })).toBeInTheDocument();
    expect(sent(1)).toMatchObject({ method: 'PUT', body: { token: 'manage-token-123456789012', topics: { sectors: ['Energi', 'Material'] } } });
    expect(sent(2)).toMatchObject({ path: '/api/v1/subscriptions/unsubscribe' });
  });

  it('says when a manage link no longer works', async () => {
    replies = [{ status: 404, body: failure('NOT_FOUND', 'Tidak ditemukan.') }];
    render(<ManageView token="gone-token-1234567890123" />);
    expect(await screen.findByRole('heading', { name: 'Tautan tidak berlaku' })).toBeInTheDocument();
  });
});

describe('teaser and the inventor switch', () => {
  it('shows only the brief summary and sends detail requests to signup with the way back', () => {
    render(<TeaserView teaser={TEASER} />);

    expect(screen.getByRole('heading', { level: 1, name: 'ClearSpring' })).toBeInTheDocument();
    expect(screen.getByText('Inovator: Inovator di TemuRiset')).toBeInTheDocument();
    expect(screen.getByText('Air dan sanitasi · Prototipe')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Daftar untuk melihat detail' })).toHaveAttribute('href', `/start?kembali=${encodeURIComponent(`/inventions/${TEASER.id}`)}`);
    expect(screen.getByRole('link', { name: 'Sudah punya akun? Masuk' })).toHaveAttribute('href', `/start?masuk=1&kembali=${encodeURIComponent(`/inventions/${TEASER.id}`)}`);
  });

  it('says when a teaser is no longer available', () => {
    render(<TeaserView teaser={null} />);
    expect(screen.getByRole('heading', { name: 'Ringkasan ini tidak tersedia' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Atur kabar inovasi Anda' })).toHaveAttribute('href', '/langganan');
  });

  it('switches inclusion on, and puts it back when the version is stale', async () => {
    replies = [{ status: 200, body: {} }, { status: 409, body: failure('STALE_VERSION', 'Data ini sudah diubah.') }];
    render(<InvestorDigestToggle inventionId="inv-1" actingPartyId="party-1" version={3} enabled={false} />);
    const box = screen.getByLabelText(/^Sertakan dalam kabar untuk investor/);

    await userEvent.click(box);
    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(sent(0)).toMatchObject({ path: '/api/v1/inventions/inv-1/investor-digest', method: 'PUT', body: { acting_party_id: 'party-1', expected_version: 3, enabled: true } });

    await userEvent.click(box);
    expect(await screen.findByText(/baru saja berubah/)).toBeInTheDocument();
    expect(box).toBeChecked();
  });

  it('has no axe violations', async () => {
    expect(await violations(<TeaserView teaser={TEASER} />)).toEqual([]);
  });
});

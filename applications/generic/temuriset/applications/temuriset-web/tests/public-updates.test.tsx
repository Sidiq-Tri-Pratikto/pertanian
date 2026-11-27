import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';

import { PublicUpdatesPanel, type PublicUpdate } from '@/features/portfolio/PublicUpdatesPanel';
import { TeaserView } from '@/views/subscriptions/TeaserView';

const router = { push: vi.fn(), replace: vi.fn(), refresh: vi.fn() };
vi.mock('next/navigation', () => ({ useRouter: () => router }));

const fetchMock = vi.fn<typeof fetch>(async () => new Response(JSON.stringify({}), { status: 200 }));

beforeEach(() => {
  fetchMock.mockClear();
  router.refresh.mockClear();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => vi.unstubAllGlobals());

const INVENTION = '11111111-1111-4111-8111-111111111111';

const UPDATE: PublicUpdate = {
  id: '22222222-2222-4222-8222-222222222222',
  invention_id: INVENTION,
  title: 'Uji lapangan kedua',
  body: 'Tiga keluarga memakai saringan selama dua minggu.',
  content_locale: 'id',
  status: 'DRAFT',
  published_at: null,
  withdrawn_at: null,
  version: 1,
  created_at: '2026-11-20T10:00:00Z',
  updated_at: '2026-11-20T10:00:00Z',
};

function lastCall() {
  const [url, init] = fetchMock.mock.calls.at(-1) as [string, RequestInit];
  return { url, init, body: JSON.parse(String(init.body)) as Record<string, unknown> };
}

describe('public updates (spec 052)', () => {
  it('saves a new update as a draft with an idempotency key, after naming what is missing', async () => {
    const user = userEvent.setup();
    const { container } = render(<PublicUpdatesPanel inventionId={INVENTION} actingPartyId="party-1" updates={[]} pageOn />);

    await user.click(screen.getByRole('button', { name: 'Simpan sebagai draf' }));
    expect(screen.getByText('Tulis judul kabar.')).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();

    await user.type(screen.getByRole('textbox', { name: /Judul kabar/ }), 'Uji lapangan kedua');
    await user.type(screen.getByRole('textbox', { name: /Isi kabar/ }), 'Tiga keluarga memakai saringan.');
    await user.click(screen.getByRole('button', { name: 'Simpan sebagai draf' }));

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    const { url, init, body } = lastCall();
    expect(url).toContain(`/api/v1/inventions/${INVENTION}/updates`);
    expect(new Headers(init.headers).get('Idempotency-Key')).toBeTruthy();
    expect(body).toEqual({ acting_party_id: 'party-1', title: 'Uji lapangan kedua', body: 'Tiga keluarga memakai saringan.', content_locale: 'id' });
    expect(await screen.findByText('Draf kabar tersimpan. Terbitkan bila sudah siap.')).toBeInTheDocument();
    const result = await axe.run(container, { rules: { 'color-contrast': { enabled: false }, region: { enabled: false } } });
    expect(result.violations.map((violation) => violation.id)).toEqual([]);
  });

  it('shows the service message when publishing is refused, and says why up front', async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ error: { code: 'INVALID_TRANSITION', message: 'Aktifkan halaman publik dulu.', request_id: 'r-1', recovery: { retryable: false } } }), { status: 409 }),
    );
    const user = userEvent.setup();
    render(<PublicUpdatesPanel inventionId={INVENTION} actingPartyId="party-1" updates={[UPDATE]} pageOn={false} />);

    expect(screen.getByText(/Nyalakan halaman publik di atas/)).toBeInTheDocument();
    const row = screen.getByRole('listitem');
    expect(within(row).getByText('Draf, belum terlihat')).toBeInTheDocument();
    await user.click(within(row).getByRole('button', { name: 'Terbitkan' }));

    expect(await screen.findByText('Aktifkan halaman publik dulu.')).toBeInTheDocument();
    expect(lastCall().body).toEqual({ acting_party_id: 'party-1', expected_version: 1 });
    expect(router.refresh).not.toHaveBeenCalled();
  });

  it('withdraws a published update and corrects one against its version', async () => {
    const published = { ...UPDATE, status: 'PUBLISHED' as const, published_at: '2026-11-21T03:00:00Z', version: 2 };
    const user = userEvent.setup();
    render(<PublicUpdatesPanel inventionId={INVENTION} actingPartyId="party-1" updates={[published]} pageOn />);

    expect(screen.getByText('Terbit 21 Nov 2026')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Tarik dari halaman' }));
    await waitFor(() => expect(lastCall().url).toContain(`/updates/${UPDATE.id}/withdraw`));

    await user.click(screen.getByText('Perbaiki teks'));
    const title = screen.getAllByRole('textbox', { name: /Judul kabar/ }).at(-1)!;
    await user.clear(title);
    await user.type(title, 'Uji lapangan kedua selesai');
    await user.click(screen.getByRole('button', { name: 'Simpan perbaikan' }));

    await waitFor(() => expect(lastCall().init.method).toBe('PUT'));
    expect(lastCall().body).toMatchObject({ expected_version: 2, title: 'Uji lapangan kedua selesai' });
    expect(await screen.findByText(/tidak dikirim ulang/)).toBeInTheDocument();
  });

  it('lists the latest updates on the public page, labelled when written in the other language', () => {
    const teaser = {
      id: INVENTION,
      title: 'ClearSpring',
      summary: 'Saringan air sederhana.',
      sector: 'Air dan sanitasi',
      stage: 'PILOT' as const,
      keywords: [],
      inventor_name: 'Rani',
      published_at: '2026-11-20T10:00:00Z',
      follow_enabled: true,
      content_locale: 'id' as const,
      latest_updates: [{ id: UPDATE.id, title: UPDATE.title, body: UPDATE.body, content_locale: 'id' as const, published_at: '2026-11-21T03:00:00Z' }],
    };
    render(<TeaserView teaser={teaser} locale="en" />);

    const section = screen.getByRole('region', { name: 'Latest updates' });
    expect(within(section).getByRole('heading', { name: 'Uji lapangan kedua' })).toHaveAttribute('lang', 'id');
    expect(within(section).getByText('21 November 2026')).toHaveAttribute('datetime', '2026-11-21T03:00:00Z');
    expect(within(section).getByText(/Written in Indonesian/)).toBeInTheDocument();
  });
});

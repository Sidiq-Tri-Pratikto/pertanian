import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';
import type { ReactElement } from 'react';

import { MandatesView } from '@/views/intake/MandatesView';
import { PartnerView } from '@/views/intake/PartnerView';

import { makeMe, PERSONAL } from './fixtures';
import { A1, DRAFT, INVESTOR_B, MITRA_A, OTHER_PARTY, RECIPIENT_E } from './intake-fixtures';

const router = { push: vi.fn(), replace: vi.fn(), refresh: vi.fn() };
vi.mock('next/navigation', () => ({ useRouter: () => router }));

type Reply = { status: number; body?: unknown };
let replies: Reply[] = [];
const fetchMock = vi.fn(async () => {
  const reply = replies.shift() ?? { status: 500, body: {} };
  return new Response(reply.body === undefined ? null : JSON.stringify(reply.body), { status: reply.status });
});

function sent(index: number) {
  const [path, init] = fetchMock.mock.calls[index] as unknown as [string, RequestInit];
  const key = (init?.headers as Record<string, string> | undefined)?.['Idempotency-Key'];
  return { path, method: init?.method, key, body: init?.body ? JSON.parse(String(init.body)) : undefined };
}

function failure(code: string, message: string, details: unknown[] = []) {
  return { error: { code, message, request_id: 'ref_1', recovery: { retryable: false }, details } };
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

async function violations(element: ReactElement): Promise<string[]> {
  const { container } = render(element);
  let result: axe.AxeResults | undefined;
  await act(async () => {
    result = await axe.run(container, { rules: { 'color-contrast': { enabled: false }, region: { enabled: false }, 'landmark-unique': { enabled: false } } });
  });
  return result!.violations.map((violation) => `${violation.id}: ${violation.nodes.map((node) => node.target).join(', ')}`);
}

describe('partner profile (S08)', () => {
  it('shows the owner each mandate with status, version, outcome, support and money, and the controls', () => {
    render(<PartnerView me={makeMe({ persona: 'mitra' })} partyId={PERSONAL} profile={MITRA_A} mandates={[A1]} />);

    expect(screen.getByRole('heading', { level: 1, name: 'Mitra A' })).toBeInTheDocument();
    expect(screen.getByText('Membantu prototipe menjadi siap uji lapangan.', { selector: 'p' })).toBeInTheDocument();
    expect(screen.getByText('Sektor: Air dan sanitasi, Pertanian')).toBeInTheDocument();
    expect(screen.getByText('Tahap yang diterima: Prototipe, Pilot')).toBeInTheDocument();
    expect(screen.getByText('Wilayah: Indonesia')).toBeInTheDocument();
    expect(screen.getByText('Bentuk dukungan: Pendanaan proyek, Fasilitas uji')).toBeInTheDocument();
    expect(screen.getByText('Pitching dibuka', { selector: 'span' })).toBeInTheDocument();
    expect(screen.getByText('Dikonfirmasi pemilik profil')).toBeInTheDocument();

    const card = screen.getByRole('article', { name: A1.title });
    expect(within(card).getByText('Aktif')).toBeInTheDocument();
    expect(within(card).getByText('Versi 1')).toBeInTheDocument();
    expect(within(card).getByText(A1.outcome)).toBeInTheDocument();
    expect(within(card).getByText(`Dukungan: ${A1.support}. ${A1.timing}.`)).toBeInTheDocument();
    expect(within(card).getByText('Kisaran dukungan mitra')).toBeInTheDocument();
    expect(within(card).getByText('USD 15.000–40.000')).toBeInTheDocument();
    expect(within(card).getByRole('link', { name: /Ubah mandat.*Validasi prototipe enam bulan/ })).toHaveAttribute('href', '/opportunities/a1/edit');
    expect(within(card).getByRole('button', { name: 'Tutup penerimaan' })).toBeInTheDocument();
    expect(within(card).getByText('Tidak berlaku')).toBeInTheDocument();
    expect(within(card).getByText(A1.requirements[0].reason)).toBeInTheDocument();
  });

  it('labels a source-reported profile and says what the external link is (AC22, AC24)', () => {
    render(<PartnerView me={makeMe()} partyId={OTHER_PARTY} profile={RECIPIENT_E} mandates={[]} />);

    expect(screen.getByText('Dilaporkan sumber')).toBeInTheDocument();
    expect(screen.getByText('Ketersediaan belum dikonfirmasi')).toBeInTheDocument();
    expect(screen.getByText('Tahap yang diterima: Belum diketahui')).toBeInTheDocument();
    expect(screen.getByText('Wilayah: Belum diketahui')).toBeInTheDocument();
    expect(screen.getByText(/Tautan ini membuka situs lain dan bukan pitching yang terkirim/)).toBeInTheDocument();
    const link = screen.getByRole('link', { name: /Buka formulir mitra.*membuka situs lain/ });
    expect(link).toHaveAttribute('href', 'https://example.org/formulir-demo');
    expect(screen.queryByRole('button', { name: 'Simpan profil' })).not.toBeInTheDocument();
  });

  it('records one handoff per click with its own key, without leaving the page', async () => {
    replies = [{ status: 201, body: { id: 'h1', partner_party_id: OTHER_PARTY, external_url: 'https://example.org/formulir-demo', submitted: false, operation_id: 'o' } }];
    render(<PartnerView me={makeMe()} partyId={OTHER_PARTY} profile={RECIPIENT_E} mandates={[]} />);
    const link = screen.getByRole('link', { name: /Buka formulir mitra.*membuka situs lain/ });
    link.addEventListener('click', (event) => event.preventDefault());

    await userEvent.click(link);

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    expect(sent(0)).toMatchObject({ path: `/api/v1/partners/${OTHER_PARTY}/handoffs`, method: 'POST', body: { acting_party_id: PERSONAL }, key: expect.any(String) });
    expect(router.push).not.toHaveBeenCalled();
    expect(screen.queryByText(/belum tercatat/)).not.toBeInTheDocument();
  });

  it('says so when a handoff could not be recorded', async () => {
    replies = [{ status: 500, body: failure('INTERNAL_ERROR', 'Gagal.') }];
    render(<PartnerView me={makeMe()} partyId={OTHER_PARTY} profile={RECIPIENT_E} mandates={[]} />);
    const link = screen.getByRole('link', { name: /Buka formulir mitra.*membuka situs lain/ });
    link.addEventListener('click', (event) => event.preventDefault());

    await userEvent.click(link);

    expect(await screen.findByText(/Pembukaan ini belum tercatat di TemuRiset/)).toBeInTheDocument();
  });

  it('does not record a handoff when the owner opens their own form', async () => {
    render(<PartnerView me={makeMe()} partyId={PERSONAL} profile={{ ...RECIPIENT_E, party_id: PERSONAL }} mandates={[]} />);
    const link = screen.getByRole('link', { name: /Buka formulir mitra.*membuka situs lain/ });
    link.addEventListener('click', (event) => event.preventDefault());

    await userEvent.click(link);

    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('says when a partner takes no new approaches, and why a target is unavailable', () => {
    const unavailable = { ...A1, target_availability: { available: false, reason: 'NO_NEW_APPROACHES' as const } };
    render(<PartnerView me={makeMe()} partyId={OTHER_PARTY} profile={{ ...MITRA_A, party_id: OTHER_PARTY, contact_route: 'NONE' }} mandates={[unavailable]} />);

    expect(screen.getAllByText('Mitra ini sedang tidak menerima pendekatan baru.')).toHaveLength(2);
  });

  it('shows the general intake label and the per-investment basis without a duration', () => {
    const general = { ...A1, general_intake_label: 'berdasarkan profil umum mitra' };
    render(<PartnerView me={makeMe()} partyId={PERSONAL} profile={INVESTOR_B} mandates={[general]} />);

    expect(screen.getByText('berdasarkan profil umum mitra')).toBeInTheDocument();
    expect(screen.getByText('Kisaran investasi investor, per investasi')).toBeInTheDocument();
    expect(screen.getByText('USD 50.000–150.000')).toBeInTheDocument();
    expect(screen.queryByText(/selama per investasi/)).not.toBeInTheDocument();
  });

  it('offers a partner with no profile a way to create one, and the first save has no version', async () => {
    replies = [{ status: 200, body: MITRA_A }];
    render(<PartnerView me={makeMe({ persona: 'mitra' })} partyId={PERSONAL} profile={null} mandates={[]} />);

    expect(screen.getByRole('heading', { name: 'Profil mitra belum ada' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Buat profil' })).toHaveAttribute('href', '#profil-mitra');
    await userEvent.type(screen.getByRole('textbox', { name: /Jenis mitra/ }), 'Mitra validasi');
    await userEvent.type(screen.getByRole('textbox', { name: /Sektor/ }), 'Air, Pertanian');
    await userEvent.click(screen.getByRole('checkbox', { name: 'Prototipe' }));
    await userEvent.click(screen.getByRole('button', { name: 'Simpan profil' }));

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(sent(0)).toMatchObject({
      path: `/api/v1/partners/${PERSONAL}`,
      method: 'PUT',
      key: expect.any(String),
      body: { acting_party_id: PERSONAL, expected_version: null, subtype: 'Mitra validasi', sectors: ['Air', 'Pertanian'], stages: ['PROTOTYPE'], intake_status: 'OPEN', contact_route: 'IN_APP', check_range: null, external_url: null },
    });
  });

  it('saves a later version, keeps the range exact, and sends the external address only for an external route', async () => {
    replies = [{ status: 200, body: { ...INVESTOR_B, version: 2 } }];
    render(<PartnerView me={makeMe()} partyId={PERSONAL} profile={INVESTOR_B} mandates={[]} />);

    await userEvent.click(screen.getByText('Ubah profil'));
    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Jalur kontak' }), 'EXTERNAL');
    await userEvent.type(screen.getByRole('textbox', { name: /Alamat formulir/ }), 'https://example.org/f');
    await userEvent.click(screen.getByRole('button', { name: 'Simpan profil' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(sent(0).body).toMatchObject({
      expected_version: 1,
      contact_route: 'EXTERNAL',
      external_url: 'https://example.org/f',
      check_range: { subject: 'investorCheck', basis: 'per_investment', min: '50000', max: '150000', currency: 'USD', period: 'per investasi', months: null, unknown_reason: null },
    });
  });

  it('keeps the values and links each field after a refused save, and flags a conflict', async () => {
    replies = [
      { status: 422, body: failure('VALIDATION_FAILED', 'Ada isian yang belum valid.', [{ loc: ['body', 'check_range', 'months'], msg: 'Isi jumlah bulan yang dicakup.', type: 'financial' }]) },
      { status: 409, body: failure('STALE_VERSION', 'Data ini sudah diubah.') },
    ];
    render(<PartnerView me={makeMe()} partyId={PERSONAL} profile={MITRA_A} mandates={[]} />);

    await userEvent.click(screen.getByText('Ubah profil'));
    await userEvent.type(screen.getByRole('textbox', { name: /Jenis mitra/ }), ' baru');
    await userEvent.click(screen.getByRole('button', { name: 'Simpan profil' }));

    expect(await screen.findByRole('link', { name: 'Isi jumlah bulan yang dicakup.' })).toHaveAttribute('href', '#p-months');
    expect(screen.getByRole('textbox', { name: /Jenis mitra/ })).toHaveValue('Mitra validasi prototipe baru');
    await userEvent.click(screen.getByRole('button', { name: 'Simpan profil' }));
    expect(await screen.findByText(/Data ini sudah diubah/)).toBeInTheDocument();
    expect(sent(1).key).not.toBe(sent(0).key);
  });

  it('gives a member without the edit capability no controls', () => {
    const me = { ...makeMe({ persona: 'mitra' }), capabilities: ['schedule'] };
    render(<PartnerView me={me} partyId={PERSONAL} profile={MITRA_A} mandates={[A1]} />);

    expect(screen.queryByText('Ubah profil')).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Ubah mandat/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Tutup penerimaan' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Buat mandat' })).not.toBeInTheDocument();
  });

  it('has no axe violations for the owner, an inventor, and an empty profile', async () => {
    expect(await violations(<PartnerView me={makeMe({ persona: 'mitra' })} partyId={PERSONAL} profile={MITRA_A} mandates={[A1, DRAFT]} />)).toEqual([]);
    document.body.innerHTML = '';
    expect(await violations(<PartnerView me={makeMe()} partyId={OTHER_PARTY} profile={RECIPIENT_E} mandates={[]} />)).toEqual([]);
    document.body.innerHTML = '';
    expect(await violations(<PartnerView me={makeMe({ persona: 'mitra' })} partyId={PERSONAL} profile={null} mandates={[]} />)).toEqual([]);
  });
});

describe('mandates list (FR-002)', () => {
  it('lists the acting party mandates with status and version, and links the profile', () => {
    render(<MandatesView me={makeMe({ persona: 'mitra' })} mandates={[A1, DRAFT]} capabilities={[]} />);

    expect(screen.getByRole('heading', { level: 1, name: 'Kebutuhan/Mandat' })).toBeInTheDocument();
    const cards = screen.getAllByRole('article');
    expect(within(cards[0]).getByText('Aktif')).toBeInTheDocument();
    expect(within(cards[1]).getByText('Draf')).toBeInTheDocument();
    expect(within(cards[0]).getByText('Versi 1')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Profil mitra saya' })).toHaveAttribute('href', `/partners/${PERSONAL}`);
  });

  it('shows an empty state, and starting a mandate opens its editor once', async () => {
    replies = [{ status: 201, body: DRAFT }];
    render(<MandatesView me={makeMe({ persona: 'mitra' })} mandates={[]} capabilities={[]} />);

    expect(screen.getByRole('heading', { name: 'Belum ada mandat' })).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Buat mandat' }));

    await waitFor(() => expect(router.push).toHaveBeenCalledWith('/opportunities/d1/edit'));
    expect(sent(0)).toMatchObject({ path: '/api/v1/opportunities', method: 'POST', body: { acting_party_id: PERSONAL }, key: expect.any(String) });
  });

  it('reports a mandate that could not be started', async () => {
    replies = [{ status: 403, body: failure('FORBIDDEN', 'Anda tidak memiliki akses.') }];
    render(<MandatesView me={makeMe({ persona: 'mitra' })} mandates={[]} capabilities={[]} />);

    await userEvent.click(screen.getByRole('button', { name: 'Buat mandat' }));

    expect(await screen.findByText('Anda tidak memiliki akses.')).toBeInTheDocument();
    expect(router.push).not.toHaveBeenCalled();
  });

  it('announces an activated version', () => {
    render(<MandatesView me={makeMe({ persona: 'mitra' })} mandates={[A1]} capabilities={[]} activated="2" />);

    expect(screen.getByText('Mandat aktif sebagai versi 2. Pitching yang sudah terkirim memakai versinya sendiri.')).toBeInTheDocument();
  });

  it('pauses and resumes with the version it saw and a key', async () => {
    replies = [{ status: 200, body: { ...A1, status: 'PAUSED', version: 3 } }];
    const { unmount } = render(<MandatesView me={makeMe({ persona: 'mitra' })} mandates={[A1]} capabilities={[]} />);

    await userEvent.click(screen.getByRole('button', { name: 'Jeda penerimaan' }));

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(sent(0)).toMatchObject({ path: '/api/v1/opportunities/a1/pause', method: 'POST', body: { acting_party_id: PERSONAL, expected_version: 2 }, key: expect.any(String) });
    unmount();

    replies = [{ status: 200, body: A1 }];
    render(<MandatesView me={makeMe({ persona: 'mitra' })} mandates={[{ ...A1, status: 'PAUSED', version: 3 }]} capabilities={[]} />);
    await userEvent.click(screen.getByRole('button', { name: 'Aktifkan lagi' }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(sent(1)).toMatchObject({ path: '/api/v1/opportunities/a1/activate', body: { expected_version: 3 } });
  });

  it('closes only after the dialog confirms, and Escape-style cancel sends nothing', async () => {
    replies = [{ status: 200, body: { ...A1, status: 'CLOSED', version: 3 } }];
    render(<MandatesView me={makeMe({ persona: 'mitra' })} mandates={[A1]} capabilities={[]} />);

    await userEvent.click(screen.getByRole('button', { name: 'Tutup penerimaan' }));
    expect(fetchMock).not.toHaveBeenCalled();
    const dialog = await screen.findByRole('dialog', { name: `Tutup penerimaan ${A1.title}?` });
    expect(within(dialog).getByText(/tidak dapat dibuka kembali/)).toBeInTheDocument();
    await userEvent.click(within(dialog).getByRole('button', { name: 'Tutup penerimaan' }));

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(sent(0)).toMatchObject({ path: '/api/v1/opportunities/a1/close', body: { expected_version: 2 } });
  });

  it('keeps the key only while a status change may not have arrived, and shows the failure', async () => {
    fetchMock.mockRejectedValueOnce(new TypeError('offline'));
    replies = [{ status: 409, body: failure('INVALID_TRANSITION', 'Status ini tidak dapat diubah dengan cara itu.') }, { status: 200, body: A1 }];
    render(<MandatesView me={makeMe({ persona: 'mitra' })} mandates={[A1]} capabilities={[]} />);
    const pause = () => userEvent.click(screen.getByRole('button', { name: 'Jeda penerimaan' }));

    await pause();
    expect(await screen.findByText(/Layanan belum dapat dihubungi/)).toBeInTheDocument();
    await pause();
    expect(await screen.findByText(/Status ini tidak dapat diubah/)).toBeInTheDocument();
    await pause();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));

    expect(sent(1).key).toBe(sent(0).key);
    expect(sent(2).key).not.toBe(sent(1).key);
  });

  it('offers no change on a closed mandate', () => {
    render(<MandatesView me={makeMe({ persona: 'mitra' })} mandates={[{ ...A1, status: 'CLOSED' }]} capabilities={[]} />);

    expect(screen.queryByRole('link', { name: /Ubah mandat/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Tutup penerimaan' })).not.toBeInTheDocument();
    expect(screen.getByText('Ditutup')).toBeInTheDocument();
  });

  it('has no axe violations', async () => {
    expect(await violations(<MandatesView me={makeMe({ persona: 'mitra' })} mandates={[A1, DRAFT]} capabilities={[]} activated="2" />)).toEqual([]);
    document.body.innerHTML = '';
    expect(await violations(<MandatesView me={makeMe({ persona: 'mitra' })} mandates={[]} capabilities={[]} />)).toEqual([]);
  });
});

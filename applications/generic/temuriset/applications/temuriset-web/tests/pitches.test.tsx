import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';

import { ApiError } from '@/api/errors';
import type { Preflight } from '@/features/pitches/model';
import { missingFiles } from '@/features/pitches/model';
import { keepsKey, stateOf } from '@/features/pitches/submit-state';
import { PreflightView } from '@/views/pitches/PreflightView';

import { makeMe, PERSONAL } from './fixtures';

const router = { push: vi.fn(), replace: vi.fn(), refresh: vi.fn() };
vi.mock('next/navigation', () => ({ useRouter: () => router }));

type Reply = { status: number; body?: unknown } | 'network';
let replies: (Reply | Promise<Reply>)[] = [];
const fetchMock = vi.fn(async () => {
  const reply = await (replies.shift() ?? { status: 500, body: {} });
  if (reply === 'network') throw new TypeError('Failed to fetch');
  return new Response(reply.body === undefined ? null : JSON.stringify(reply.body), { status: reply.status });
});

beforeEach(() => {
  replies = [];
  fetchMock.mockClear();
  router.push.mockClear();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => vi.unstubAllGlobals());

function sent(index: number) {
  const [path, init] = fetchMock.mock.calls[index] as unknown as [string, RequestInit];
  return { path, key: (init.headers as Record<string, string>)['Idempotency-Key'], body: init.body ? JSON.parse(String(init.body)) : undefined };
}

function failure(code: string, message: string, extra: Record<string, unknown> = {}) {
  return { error: { code, message, request_id: 'ref_9', recovery: { retryable: false }, ...extra } };
}

const SOURCE = { type: 'SUPPORT_REQUEST' as const, id: '11111111-1111-4111-8111-111111111111' };
const TARGET = '22222222-2222-4222-8222-222222222222';
const FILE = 'ffffffff-ffff-4fff-8fff-ffffffffffff';

function row(label: string, field: string, result: 'PASS' | 'UNKNOWN', mode = 'DECLARATION', appliesAt = 'SUBMISSION') {
  return { requirement_id: `${field}-${label}`.padEnd(36, '0').slice(0, 36), label, field, mandatory: true, applies_at: appliesAt, verification_mode: mode, result, reason: `${label} alasan.`, action: null };
}

function preflight(overrides: Partial<Preflight> = {}): Preflight {
  return {
    preflight_id: 'p1',
    token: 'token-1',
    expires_at: '2026-11-06T10:30:00Z',
    readiness: 'READY_TO_SUBMIT',
    eligibility: 'ELIGIBLE',
    label: 'Kecocokan kuat',
    fit: { lower: '88.11', upper: '94.04', coverage: '0.95' },
    sender: { party_id: PERSONAL, name: 'Rani' },
    recipient: { party_id: 'a', name: 'Mitra A' },
    opportunity: { id: TARGET, version_id: 'v1', version: 1, title: 'Validasi prototipe enam bulan' },
    source: { type: 'SUPPORT_REQUEST', id: SOURCE.id, version: 2, title: 'ClearSpring' },
    inventions: [{ invention_id: 'i1', version_id: 'iv1', version: 1, title: 'ClearSpring' }],
    purpose: 'PROJECT',
    availability: { available: true, reason: null },
    rows: [row('Tahap inovasi', 'stage', 'PASS'), row('Berkas uji fungsi', 'document:function', 'PASS', 'DOCUMENT_PRESENT')],
    gap: null,
    later: [],
    shareable_files: [
      { document_id: 'd1', version_id: FILE, version: 1, title: 'Laporan uji fungsi ClearSpring', file_state: 'AVAILABLE', review_state: 'PROVIDED_UNREVIEWED', fact_keys: ['function'] },
    ],
    brief: { id: 'b1', preflight_id: 'p1', text: 'Masalah: Air keruh.\nSaat ini: Kapasitas saring 10 L/jam.', sentences: [], summarizer: 'off', summarizer_status: 'off' },
    duplicate_pitch_id: null,
    ...overrides,
  };
}

describe('submit state machine', () => {
  it('maps each failure to what the screen shows, and keeps the key only after a lost answer', () => {
    expect(stateOf(ApiError.unreachable())).toEqual({ kind: 'lost' });
    const stale = new ApiError('PREFLIGHT_STALE', 'Ada yang berubah.', { retryable: false }, 'r', { fields: { reason: 'Mandat berubah setelah pemeriksaan.' } });
    expect(stateOf(stale)).toEqual({ kind: 'stale', reason: 'Mandat berubah setelah pemeriksaan.' });
    expect(stateOf(new ApiError('DUPLICATE_PITCH', 'Sudah ada.', { retryable: false }, 'r', { fields: { pitch_id: 'x' } }))).toEqual({ kind: 'duplicate', pitchId: 'x' });
    expect(stateOf(new ApiError('NOT_READY', 'Belum.', { retryable: false }, 'r', { fields: { requirement: 'Berkas' } }))).toEqual({ kind: 'not_ready', message: 'Belum.', requirement: 'Berkas' });
    expect(stateOf(new ApiError('TARGET_CLOSED', 'Ditutup.', { retryable: false }, 'r', { fields: { reason: 'Sudah ditutup.' } }))).toEqual({ kind: 'failed', message: 'Ditutup. Sudah ditutup.', requestId: 'r' });
    expect(keepsKey({ kind: 'lost' })).toBe(true);
    expect(keepsKey({ kind: 'stale', reason: '' })).toBe(false);
  });

  it('knows which required files the chosen ones leave out', () => {
    expect(missingFiles(preflight(), [])).toEqual([{ label: 'Berkas uji fungsi', key: 'function' }]);
    expect(missingFiles(preflight(), [FILE])).toEqual([]);
  });
});

describe('preflight (S11)', () => {
  it('shows recipient, sender, versions, unchecked files and the brief, then sends once with one key', async () => {
    const user = userEvent.setup();
    replies = [{ status: 200, body: preflight() }, { status: 201, body: { pitch_id: 'pitch-1', status: 'SUBMITTED' } }];
    render(<PreflightView me={makeMe()} source={SOURCE} targetId={TARGET} />);

    expect(await screen.findByText('Siap dikirim')).toBeInTheDocument();
    expect(screen.getByText('Mitra A · Validasi prototipe enam bulan, versi 1')).toBeInTheDocument();
    expect(screen.getByText('Dukungan Proyek: ClearSpring, versi 2')).toBeInTheDocument();
    const file = screen.getByRole('checkbox', { name: /Laporan uji fungsi ClearSpring, versi 1/ });
    expect(file).not.toBeChecked();
    expect(screen.getByRole('textbox', { name: /Brief pitching/ })).toHaveValue('Masalah: Air keruh.\nSaat ini: Kapasitas saring 10 L/jam.');

    await user.click(file);
    await user.type(screen.getByRole('textbox', { name: /Brief pitching/ }), ' Tambahan.');
    await user.click(screen.getByRole('button', { name: 'Kirim pitching kepada Mitra A' }));

    await waitFor(() => expect(router.push).toHaveBeenCalledWith('/pitches/pitch-1?terkirim=1'));
    const submitted = sent(1);
    expect(submitted.path).toBe('/api/v1/pitches');
    expect(submitted.body).toEqual({
      acting_party_id: PERSONAL,
      preflight_token: 'token-1',
      brief: 'Masalah: Air keruh.\nSaat ini: Kapasitas saring 10 L/jam. Tambahan.',
      files: [{ document_id: 'd1', version: 1 }],
    });
    expect(submitted.key).toBeTruthy();
  });

  it('keeps automatic summary hidden when the deployment does not offer it', async () => {
    replies = [{ status: 200, body: preflight() }];
    render(<PreflightView me={makeMe()} source={SOURCE} targetId={TARGET} />);

    expect(await screen.findByRole('textbox', { name: /Brief pitching/ })).toBeEnabled();
    expect(screen.queryByRole('button', { name: 'Buat ringkasan otomatis' })).not.toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('requests an extractive suggestion and replaces an edited draft only after explicit confirmation', async () => {
    const user = userEvent.setup();
    const checked = preflight();
    const summary = { ...checked.brief, text: 'Masalah: Air keruh.', summarizer_status: 'used' };
    replies = [{ status: 200, body: checked }, { status: 200, body: summary }];
    render(<PreflightView me={makeMe()} source={SOURCE} targetId={TARGET} summaryAvailable />);
    const draft = await screen.findByRole('textbox', { name: /Brief pitching/ });
    await user.type(draft, ' Catatan saya.');

    await user.click(screen.getByRole('button', { name: 'Buat ringkasan otomatis' }));

    expect(await screen.findByText(summary.text)).toBeInTheDocument();
    expect(sent(1)).toEqual({ path: '/api/v1/briefs/b1/summary', body: undefined, key: undefined });
    expect(draft).toHaveValue(checked.brief.text + ' Catatan saya.');
    await user.click(screen.getByRole('button', { name: 'Ganti brief dengan ringkasan' }));
    expect(draft).toHaveValue(summary.text);
  });

  it.each(['off', 'unavailable', 'refused', 'network'])('keeps the edited brief when summary is %s', async (status) => {
    const user = userEvent.setup();
    const checked = preflight();
    const message = status === 'refused' ? 'Ringkasan otomatis ditolak' : 'Ringkasan otomatis tidak tersedia';
    const error = status === 'unavailable' || status === 'refused'
      ? failure(`SUMMARY_${status.toUpperCase()}`, `${message}. Lanjutkan dengan menyunting brief.`).error
      : null;
    replies = [
      { status: 200, body: checked },
      status === 'network' ? 'network' : { status: 200, body: { ...checked.brief, text: 'Templat lain.', summarizer_status: status, summarizer_error: error } },
    ];
    render(<PreflightView me={makeMe()} source={SOURCE} targetId={TARGET} summaryAvailable />);
    const draft = await screen.findByRole('textbox', { name: /Brief pitching/ });
    await user.type(draft, ' Catatan saya.');
    await user.click(screen.getByRole('button', { name: 'Buat ringkasan otomatis' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(message);
    expect(draft).toHaveValue(checked.brief.text + ' Catatan saya.');
    expect(draft).toBeEnabled();
    expect(screen.queryByRole('button', { name: 'Ganti brief dengan ringkasan' })).not.toBeInTheDocument();
    if (error) expect(screen.getByText('ID referensi: ref_9')).toBeInTheDocument();
  });

  it('discards an in-flight suggestion after the draft is edited, even if the text returns to its prior value', async () => {
    const user = userEvent.setup();
    const checked = preflight();
    const pending = Promise.withResolvers<Reply>();
    replies = [{ status: 200, body: checked }, pending.promise];
    render(<PreflightView me={makeMe()} source={SOURCE} targetId={TARGET} summaryAvailable />);
    const draft = await screen.findByRole('textbox', { name: /Brief pitching/ });
    await user.click(screen.getByRole('button', { name: 'Buat ringkasan otomatis' }));
    expect(screen.getByRole('button', { name: 'Menyusun ringkasan…' })).toHaveAttribute('aria-busy', 'true');

    await user.type(draft, 'x{Backspace}');
    await act(async () => pending.resolve({ status: 200, body: { ...checked.brief, text: 'Saran lama.', summarizer_status: 'used' } }));

    expect(draft).toHaveValue(checked.brief.text);
    expect(screen.queryByText('Saran lama.')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Ganti brief dengan ringkasan' })).not.toBeInTheDocument();
  });

  it('discards a pending suggestion after preflight refresh', async () => {
    const user = userEvent.setup();
    const checked = preflight();
    const pending = Promise.withResolvers<Reply>();
    replies = [
      { status: 200, body: checked },
      pending.promise,
      { status: 409, body: failure('PREFLIGHT_STALE', 'Ada yang berubah sejak pemeriksaan.') },
      { status: 200, body: preflight({ token: 'token-2', opportunity: { ...checked.opportunity, version: 2 } }) },
    ];
    render(<PreflightView me={makeMe()} source={SOURCE} targetId={TARGET} summaryAvailable />);
    await user.click(await screen.findByRole('checkbox', { name: /Laporan uji fungsi/ }));
    await user.click(screen.getByRole('button', { name: 'Buat ringkasan otomatis' }));
    await user.click(screen.getByRole('button', { name: 'Kirim pitching kepada Mitra A' }));
    const conflict = await screen.findByRole('group', { name: 'Versi berubah' });
    await user.click(within(conflict).getByRole('button', { name: 'Periksa ulang' }));

    await screen.findByText('Mitra A · Validasi prototipe enam bulan, versi 2');
    await act(async () => pending.resolve({ status: 200, body: { ...checked.brief, text: 'Saran kedaluwarsa.', summarizer_status: 'used' } }));
    expect(screen.queryByText('Saran kedaluwarsa.')).not.toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /Brief pitching/ })).toHaveValue(checked.brief.text);
  });

  it('links the file list from the error summary and sends nothing when a required file is not chosen', async () => {
    const user = userEvent.setup();
    replies = [{ status: 200, body: preflight() }];
    render(<PreflightView me={makeMe()} source={SOURCE} targetId={TARGET} />);

    await user.click(await screen.findByRole('button', { name: 'Kirim pitching kepada Mitra A' }));

    const summary = screen.getByRole('group', { name: 'Masih ada yang perlu diperbaiki' });
    expect(within(summary).getByRole('link', { name: 'Pilih berkas untuk syarat “Berkas uji fungsi”.' })).toHaveAttribute('href', '#berkas-pilihan');
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('keeps the edited brief through a stale preflight and checks again', async () => {
    const user = userEvent.setup();
    replies = [
      { status: 200, body: preflight() },
      { status: 409, body: failure('PREFLIGHT_STALE', 'Ada yang berubah sejak pemeriksaan.', { reason: 'Mandat berubah setelah pemeriksaan.' }) },
      { status: 200, body: preflight({ token: 'token-2', opportunity: { id: TARGET, version_id: 'v2', version: 2, title: 'Validasi prototipe enam bulan' } }) },
    ];
    render(<PreflightView me={makeMe()} source={SOURCE} targetId={TARGET} />);
    await user.click(await screen.findByRole('checkbox', { name: /Laporan uji fungsi/ }));
    const brief = screen.getByRole('textbox', { name: /Brief pitching/ });
    await user.clear(brief);
    await user.type(brief, 'Brief saya sendiri.');
    await user.click(screen.getByRole('button', { name: 'Kirim pitching kepada Mitra A' }));

    const conflict = await screen.findByRole('group', { name: 'Versi berubah' });
    expect(within(conflict).getByText('Mandat berubah setelah pemeriksaan. Periksa ulang sebelum mengirim.')).toBeInTheDocument();
    expect(within(conflict).getByText('Brief saya sendiri.')).toBeInTheDocument();
    await user.click(within(conflict).getByRole('button', { name: 'Periksa ulang' }));

    expect(await screen.findByText('Mitra A · Validasi prototipe enam bulan, versi 2')).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /Brief pitching/ })).toHaveValue('Brief saya sendiri.');
  });

  it('says a lost answer is safe to retry and reuses the same key', async () => {
    const user = userEvent.setup();
    replies = [{ status: 200, body: preflight() }, 'network', { status: 201, body: { pitch_id: 'pitch-1', status: 'SUBMITTED' } }];
    render(<PreflightView me={makeMe()} source={SOURCE} targetId={TARGET} />);
    await user.click(await screen.findByRole('checkbox', { name: /Laporan uji fungsi/ }));
    await user.click(screen.getByRole('button', { name: 'Kirim pitching kepada Mitra A' }));

    expect(await screen.findByText('Status pengiriman belum diketahui')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Coba kirim lagi' }));

    await waitFor(() => expect(router.push).toHaveBeenCalledWith('/pitches/pitch-1?terkirim=1'));
    expect(sent(2).key).toBe(sent(1).key);
  });

  it('opens the existing pitch on a duplicate', async () => {
    const user = userEvent.setup();
    replies = [{ status: 200, body: preflight() }, { status: 409, body: failure('DUPLICATE_PITCH', 'Pitching untuk kebutuhan dan mandat ini sudah ada.', { pitch_id: 'pitch-0' }) }];
    render(<PreflightView me={makeMe()} source={SOURCE} targetId={TARGET} />);
    await user.click(await screen.findByRole('checkbox', { name: /Laporan uji fungsi/ }));
    await user.click(screen.getByRole('button', { name: 'Kirim pitching kepada Mitra A' }));

    expect(await screen.findByRole('link', { name: 'Buka pitching yang ada' })).toHaveAttribute('href', '/pitches/pitch-0');
  });

  it('disables sending with its reason when the target needs information, and offers an existing pitch', async () => {
    replies = [{ status: 200, body: preflight({ readiness: 'NEEDS_INFORMATION', gap: row('Kisaran biaya pilot', 'budget', 'UNKNOWN'), duplicate_pitch_id: 'pitch-0' }) }];
    render(<PreflightView me={makeMe()} source={SOURCE} targetId={TARGET} />);

    const button = await screen.findByRole('button', { name: 'Kirim pitching kepada Mitra A' });
    expect(button).toHaveAttribute('aria-disabled', 'true');
    expect(screen.getByText('Belum siap dikirim: Kisaran biaya pilot alasan.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Buka pitching yang ada' })).toHaveAttribute('href', '/pitches/pitch-0');
  });

  it('keeps the screen and offers a retry when the check fails', async () => {
    const user = userEvent.setup();
    replies = [{ status: 404, body: failure('NOT_FOUND', 'Data yang diminta tidak ditemukan.') }, { status: 200, body: preflight() }];
    render(<PreflightView me={makeMe()} source={SOURCE} targetId={TARGET} />);

    expect(await screen.findByRole('alert')).toHaveTextContent('Data yang diminta tidak ditemukan.');
    await user.click(screen.getByRole('button', { name: 'Coba lagi' }));
    expect(await screen.findByText('Siap dikirim')).toBeInTheDocument();
  });

  it.each([false, true])('has no axe violations when summary availability is %s', async (summaryAvailable) => {
    const checked = preflight();
    replies = [
      { status: 200, body: checked },
      { status: 200, body: { ...checked.brief, text: 'Masalah: Air keruh.', summarizer_status: 'used' } },
    ];
    const { container } = render(<PreflightView me={makeMe()} source={SOURCE} targetId={TARGET} summaryAvailable={summaryAvailable} />);
    await screen.findByText('Siap dikirim');
    if (summaryAvailable) {
      await userEvent.setup().click(screen.getByRole('button', { name: 'Buat ringkasan otomatis' }));
      await screen.findByText('Ringkasan siap ditinjau');
    }
    let result: axe.AxeResults | undefined;
    await act(async () => {
      result = await axe.run(container, { rules: { 'color-contrast': { enabled: false }, region: { enabled: false }, 'landmark-unique': { enabled: false } } });
    });
    expect(result!.violations.map((violation) => violation.id)).toEqual([]);
  });
});

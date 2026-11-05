import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';

import { MandateEditView } from '@/views/intake/MandateEditView';

import { makeMe, PERSONAL } from './fixtures';
import { A1, DRAFT, OTHER_PARTY } from './intake-fixtures';

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

function open(mandate = A1) {
  return render(<MandateEditView me={makeMe({ persona: 'mitra' })} mandate={mandate} />);
}

async function toReview() {
  await userEvent.click(screen.getByRole('button', { name: 'Tinjau mandat' }));
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

describe('adding requirements (scenario 1)', () => {
  it('chooses stage and mode for a narrative requirement and labels it as manual review', async () => {
    open();

    await userEvent.type(screen.getByRole('textbox', { name: /Syarat baru/ }), 'Pengalaman di desa');
    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Tahap berlaku' }), 'DISCUSSION');
    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Cara pemeriksaan' }), 'REVIEWER_CONFIRMED');
    await userEvent.click(screen.getByRole('button', { name: 'Tambah syarat' }));

    const row = screen.getByRole('heading', { name: 'Pengalaman di desa' }).closest('[data-requirement]') as HTMLElement;
    expect(within(row).getByText('Ditinjau manual')).toBeInTheDocument();
    expect(within(row).getByText('Tidak berlaku')).toBeInTheDocument();
    expect(within(row).getByText('Saat diskusi · Preferensi · Diperiksa peninjau')).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /Syarat baru/ })).toHaveValue('');
  });

  it('refuses to add a requirement with no name, without sending anything', async () => {
    open();

    await userEvent.click(screen.getByRole('button', { name: 'Tambah syarat' }));

    expect(screen.getByText('Isi nama syarat.')).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it.each([
    ['stage', { field: 'stage', operator: 'in_set', value: ['PILOT'], mandatory: true }],
    ['relationship', { field: 'relationship', operator: 'equals', value: 'PROJECT', mandatory: true }],
    ['document', { field: 'document:function', operator: 'exists', value: true, mandatory: true }],
    ['feature', { field: 'feature:sso-korporasi', operator: 'equals', value: 'CURRENT', mandatory: true }],
    ['budget', { field: 'budget', operator: 'range_overlap', value: null, mandatory: true }],
    ['contribution', { field: 'contribution', operator: 'range_overlap', value: null, mandatory: true }],
    ['authority', { field: 'authority', operator: 'equals', value: 'REVIEWED', mandatory: true }],
    ['entity', { field: 'entity', operator: 'equals', value: 'IDENTIFIED', mandatory: true }],
  ])('builds a typed %s requirement for the service to validate', async (kind, expected) => {
    replies = [{ status: 200, body: { ...A1, number: 2, version: 3 } }];
    open();

    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Jenis syarat' }), kind);
    if (kind === 'stage') await userEvent.click(within(screen.getByRole('group', { name: 'Tahap yang dipersyaratkan' })).getByRole('checkbox', { name: 'Pilot' }));
    if (kind === 'feature') await userEvent.type(screen.getByRole('textbox', { name: /Nama fitur/ }), 'SSO korporasi');
    await userEvent.type(screen.getByRole('textbox', { name: /Syarat baru/ }), 'Syarat bertipe');
    await userEvent.type(screen.getByRole('textbox', { name: /Alasan syarat baru/ }), 'Alasannya');
    await userEvent.click(screen.getByRole('button', { name: 'Tambah syarat' }));
    await toReview();
    await userEvent.click(screen.getByRole('button', { name: 'Aktifkan versi 2' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(sent(0).body.requirements.at(-1)).toMatchObject({ label: 'Syarat bertipe', reason: 'Alasannya', ...expected });
  });

  it('lets a stored requirement change stage, mode and reason, and be removed', async () => {
    replies = [{ status: 200, body: { ...A1, number: 2, version: 3 } }, { status: 200, body: { ...A1, number: 3, version: 4 } }];
    open();

    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Tahap berlaku: Tahap inovasi' }), 'PILOT');
    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Cara pemeriksaan: Tahap inovasi' }), 'DOCUMENT_PRESENT');
    const reason = screen.getByRole('textbox', { name: /Alasan: Tahap inovasi/ });
    await userEvent.clear(reason);
    await userEvent.type(reason, 'Alasan baru');
    await toReview();
    await userEvent.click(screen.getByRole('button', { name: 'Aktifkan versi 2' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(sent(0).body.requirements[0]).toEqual({
      label: 'Tahap inovasi',
      field: 'stage',
      operator: 'in_set',
      value: ['PROTOTYPE', 'PILOT'],
      mandatory: true,
      applies_at: 'PILOT',
      verification_mode: 'DOCUMENT_PRESENT',
      visibility: 'PUBLIC',
      reason: 'Alasan baru',
    });
  });

  it('removes a requirement from what is saved', async () => {
    replies = [{ status: 200, body: A1 }];
    open();

    await userEvent.click(screen.getByRole('button', { name: 'Hapus syarat Tahap inovasi' }));
    await toReview();
    await userEvent.click(screen.getByRole('button', { name: 'Aktifkan versi 2' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(sent(0).body.requirements).toEqual([]);
  });
});

describe('review and activate (scenario 2)', () => {
  it('shows a summary before activating, sends nothing until then, and can go back', async () => {
    open();

    await userEvent.clear(screen.getByRole('textbox', { name: /Judul mandat/ }));
    await userEvent.type(screen.getByRole('textbox', { name: /Judul mandat/ }), 'Judul baru');
    await toReview();

    expect(fetchMock).not.toHaveBeenCalled();
    const summary = screen.getByRole('region', { name: 'Tinjau mandat' });
    expect(within(summary).getByText('Judul baru')).toBeInTheDocument();
    expect(within(summary).getByText(A1.outcome)).toBeInTheDocument();
    expect(within(summary).getByText('USD 15.000–40.000')).toBeInTheDocument();
    expect(within(summary).getByText('Tahap inovasi')).toBeInTheDocument();
    expect(document.activeElement).toBe(screen.getByRole('heading', { name: 'Tinjau mandat' }));
    expect(screen.getByRole('button', { name: 'Aktifkan versi 2' })).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Kembali mengubah' }));
    expect(screen.getByRole('textbox', { name: /Judul mandat/ })).toHaveValue('Judul baru');
  });

  it('a live mandate is saved as the next version and needs no activation', async () => {
    replies = [{ status: 200, body: { ...A1, number: 2, version: 3 } }];
    open();

    await toReview();
    await userEvent.click(screen.getByRole('button', { name: 'Aktifkan versi 2' }));

    await waitFor(() => expect(router.push).toHaveBeenCalledWith('/opportunities?aktif=2'));
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(sent(0)).toMatchObject({ path: '/api/v1/opportunities/a1', method: 'PUT', key: expect.any(String) });
    expect(sent(0).body).toMatchObject({
      acting_party_id: PERSONAL,
      expected_version: 2,
      title: A1.title,
      accepted_stages: A1.accepted_stages,
      relationship_forms: A1.relationship_forms,
      sectors: A1.sectors,
      keywords: A1.keywords,
      closes_at: A1.closes_at,
      financial: { subject: 'partner', basis: 'total_period', min: '15000', max: '40000', currency: 'USD', period: '6 bulan', months: 6, scope: 'biaya pilot enam bulan' },
    });
    expect(sent(0).body.requirements[0]).toMatchObject({ field: 'stage', operator: 'in_set', value: ['PROTOTYPE', 'PILOT'] });
  });

  it('a draft is saved, then activated against the version the save returned', async () => {
    replies = [{ status: 200, body: { ...DRAFT, version: 2 } }, { status: 200, body: { ...DRAFT, version: 3, status: 'ACTIVE' } }];
    open(DRAFT);

    await toReview();
    await userEvent.click(screen.getByRole('button', { name: 'Aktifkan versi 1' }));

    await waitFor(() => expect(router.push).toHaveBeenCalledWith('/opportunities?aktif=1'));
    expect(sent(0)).toMatchObject({ path: '/api/v1/opportunities/d1', method: 'PUT', body: { expected_version: 1 } });
    expect(sent(1)).toMatchObject({ path: '/api/v1/opportunities/d1/activate', method: 'POST', body: { acting_party_id: PERSONAL, expected_version: 2 }, key: expect.any(String) });
    expect(sent(1).key).not.toBe(sent(0).key);
  });

  it('a paused mandate is saved as the next version, then activated', async () => {
    const paused = { ...A1, status: 'PAUSED' as const };
    replies = [{ status: 200, body: { ...paused, number: 2, version: 3 } }, { status: 200, body: { ...A1, number: 2, version: 4 } }];
    open(paused);

    await toReview();
    await userEvent.click(screen.getByRole('button', { name: 'Aktifkan versi 2' }));

    await waitFor(() => expect(router.push).toHaveBeenCalledWith('/opportunities?aktif=2'));
    expect(sent(1)).toMatchObject({ path: '/api/v1/opportunities/a1/activate', body: { expected_version: 3 } });
  });

  it('a retry after a lost activation does not save again, and keeps both keys sensible', async () => {
    fetchMock.mockImplementationOnce(async () => new Response(JSON.stringify({ ...DRAFT, version: 2 }), { status: 200 }));
    fetchMock.mockRejectedValueOnce(new TypeError('offline'));
    replies = [{ status: 200, body: { ...DRAFT, version: 3, status: 'ACTIVE' } }];
    open(DRAFT);

    await toReview();
    await userEvent.click(screen.getByRole('button', { name: 'Aktifkan versi 1' }));
    expect(await screen.findByText(/Layanan belum dapat dihubungi/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Aktifkan versi 1' }));

    await waitFor(() => expect(router.push).toHaveBeenCalled());
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(sent(2).path).toBe('/api/v1/opportunities/d1/activate');
    expect(sent(2).key).toBe(sent(1).key);
    expect(sent(2).body.expected_version).toBe(2);
  });

  it('a draft can be saved incomplete without going live', async () => {
    replies = [{ status: 200, body: { ...DRAFT, version: 2, title: 'Baru' } }];
    open(DRAFT);

    await userEvent.click(screen.getByRole('button', { name: 'Simpan draf' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    expect(sent(0).method).toBe('PUT');
    expect(router.push).not.toHaveBeenCalled();
    expect(await screen.findByText('Tersimpan')).toBeInTheDocument();
  });

  it('a live mandate offers no plain save, because any save goes live', () => {
    open();

    expect(screen.queryByRole('button', { name: 'Simpan draf' })).not.toBeInTheDocument();
  });

  it('returns to the form with a linked summary when the service refuses, keeping every value', async () => {
    replies = [
      {
        status: 422,
        body: failure('VALIDATION_FAILED', 'Ada isian yang belum valid.', [
          { loc: ['body', 'outcome'], msg: 'Isi hasil yang dicari.', type: 'activation' },
          { loc: ['body', 'financial', 'months'], msg: 'Isi jumlah bulan yang dicakup.', type: 'financial' },
          { loc: ['body', 'requirements', 0, 'reason'], msg: 'Jelaskan alasan syarat wajib ini.', type: 'activation' },
          { loc: ['partner_profile'], msg: 'Simpan profil mitra sebelum mengaktifkan mandat.', type: 'activation' },
        ]),
      },
    ];
    open();

    await userEvent.clear(screen.getByRole('textbox', { name: /Hasil yang dicari/ }));
    await toReview();
    await userEvent.click(screen.getByRole('button', { name: 'Aktifkan versi 2' }));

    expect(await screen.findByRole('link', { name: 'Isi hasil yang dicari.' })).toHaveAttribute('href', '#m-outcome');
    expect(screen.getByRole('link', { name: 'Isi jumlah bulan yang dicakup.' })).toHaveAttribute('href', '#m-months');
    expect(screen.getByRole('link', { name: 'Jelaskan alasan syarat wajib ini.' })).toHaveAttribute('href', '#m-req-reason-0');
    expect(screen.getByRole('link', { name: 'Simpan profil mitra sebelum mengaktifkan mandat.' })).toHaveAttribute('href', '#m-profile');
    expect(screen.getByRole('link', { name: 'Buka profil mitra' })).toHaveAttribute('href', `/partners/${PERSONAL}`);
    expect(screen.getByRole('textbox', { name: /Judul mandat/ })).toHaveValue(A1.title);
  });

  it('shows a failure the form cannot place, with its reference', async () => {
    replies = [{ status: 409, body: failure('INVALID_TRANSITION', 'Status ini tidak dapat diubah.') }];
    open();

    await toReview();
    await userEvent.click(screen.getByRole('button', { name: 'Aktifkan versi 2' }));

    expect(await screen.findByText('Status ini tidak dapat diubah. Kode rujukan: ref_1.')).toBeInTheDocument();
  });
});

describe('stale version (scenario 3)', () => {
  it('keeps the edits, loads the latest version, and targets it on the next attempt', async () => {
    replies = [
      { status: 409, body: { error: { code: 'STALE_VERSION', message: 'Data ini sudah diubah.', request_id: 'r', recovery: { retryable: false }, current_version: 5 } } },
      { status: 200, body: { ...A1, version: 5, number: 3, title: 'Tab lain' } },
      { status: 200, body: { ...A1, version: 6, number: 4 } },
    ];
    open();

    await userEvent.clear(screen.getByRole('textbox', { name: /Judul mandat/ }));
    await userEvent.type(screen.getByRole('textbox', { name: /Judul mandat/ }), 'Isian saya');
    await toReview();
    await userEvent.click(screen.getByRole('button', { name: 'Aktifkan versi 2' }));

    const conflict = await screen.findByRole('group', { name: 'Versi berubah' });
    expect(within(conflict).getByText('Isian saya')).toBeInTheDocument();
    await userEvent.click(within(conflict).getByRole('button', { name: 'Pakai versi terbaru, pertahankan isian saya' }));

    await userEvent.click(await screen.findByRole('button', { name: 'Aktifkan versi 4' }));

    await waitFor(() => expect(router.push).toHaveBeenCalledWith('/opportunities?aktif=4'));
    expect(sent(1)).toMatchObject({ path: '/api/v1/opportunities/a1' });
    expect(sent(2).body).toMatchObject({ expected_version: 5, title: 'Isian saya' });
    expect(screen.queryByRole('group', { name: 'Versi berubah' })).not.toBeInTheDocument();
  });

  it('reports when the latest version cannot be loaded, and keeps the edits', async () => {
    replies = [{ status: 409, body: failure('STALE_VERSION', 'Data ini sudah diubah.') }];
    open();

    await toReview();
    await userEvent.click(screen.getByRole('button', { name: 'Aktifkan versi 2' }));
    await userEvent.click(await screen.findByRole('button', { name: 'Pakai versi terbaru, pertahankan isian saya' }));

    expect(await screen.findByText(/Kode rujukan/)).toBeInTheDocument();
    expect(screen.getByRole('group', { name: 'Versi berubah' })).toBeInTheDocument();
  });
});

describe('money on the form', () => {
  it('sends null for a mandate with nothing stated, and non-cash text without amounts', async () => {
    const empty = { ...DRAFT, financial: null };
    replies = [{ status: 200, body: empty }, { status: 200, body: empty }];
    open(empty);

    await userEvent.click(screen.getByRole('button', { name: 'Simpan draf' }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    expect(sent(0).body.financial).toBeNull();

    await userEvent.type(await screen.findByRole('textbox', { name: /Dukungan nontunai/ }), 'Fasilitas uji');
    await userEvent.click(screen.getByRole('button', { name: 'Simpan draf' }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(sent(1).body.financial).toMatchObject({ noncash: 'Fasilitas uji', min: null, max: null, basis: null, currency: null, months: null });
  });

  it('fills the per-investment period and leaves months out', async () => {
    const empty = { ...DRAFT, financial: null };
    replies = [{ status: 200, body: empty }];
    open(empty);

    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Dasar keuangan' }), 'investorCheck');
    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Mata uang' }), 'USD');
    await userEvent.type(screen.getByRole('textbox', { name: /Jumlah minimum/ }), '50000');
    await userEvent.type(screen.getByRole('textbox', { name: /Jumlah maksimum/ }), '150000');
    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Dasar perhitungan' }), 'per_investment');
    await userEvent.click(screen.getByRole('button', { name: 'Simpan draf' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(sent(0).body.financial).toMatchObject({ subject: 'investorCheck', basis: 'per_investment', min: '50000', max: '150000', currency: 'USD', period: 'per investasi', months: null });
  });

  it('sends the reason for an unknown amount, never zero', async () => {
    const empty = { ...DRAFT, financial: null };
    replies = [{ status: 200, body: empty }];
    open(empty);

    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Bila kisaran belum diketahui' }), 'not_determined');
    await userEvent.click(screen.getByRole('button', { name: 'Simpan draf' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(sent(0).body.financial).toMatchObject({ min: null, max: null, unknown_reason: 'not_determined' });
  });
});

describe('who may edit', () => {
  it('shows a closed mandate as read-only', () => {
    open({ ...A1, status: 'CLOSED' });

    expect(screen.getByText(/Mandat ini sudah ditutup/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Tinjau mandat' })).not.toBeInTheDocument();
    expect(screen.getByRole('article', { name: A1.title })).toBeInTheDocument();
  });

  it('denies another party and a member without the edit capability', () => {
    const { unmount } = open({ ...A1, partner_party_id: OTHER_PARTY });
    expect(screen.getByRole('heading', { name: 'Akses dibatasi' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Tinjau mandat' })).not.toBeInTheDocument();
    unmount();

    render(<MandateEditView me={{ ...makeMe({ persona: 'mitra' }), capabilities: ['schedule'] }} mandate={A1} />);
    expect(screen.getByRole('heading', { name: 'Akses dibatasi' })).toBeInTheDocument();
  });

  it('has no axe violations while editing, reviewing and denied', async () => {
    const check = async (container: HTMLElement) => {
      let result: axe.AxeResults | undefined;
      await act(async () => {
        result = await axe.run(container, { rules: { 'color-contrast': { enabled: false }, region: { enabled: false }, 'landmark-unique': { enabled: false } } });
      });
      return result!.violations.map((violation) => `${violation.id}: ${violation.nodes.map((node) => node.target).join(', ')}`);
    };
    const { container, unmount } = open();
    expect(await check(container)).toEqual([]);
    await toReview();
    expect(await check(container)).toEqual([]);
    unmount();
    const denied = open({ ...A1, partner_party_id: OTHER_PARTY });
    expect(await check(denied.container)).toEqual([]);
  });
});

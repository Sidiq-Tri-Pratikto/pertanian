import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';
import type { ReactElement } from 'react';

import type { Pitch, PitchSummary } from '@/features/pitches/model';
import { filterPitches, tabOf, turnOf } from '@/features/pitches/workspace';
import { PitchesView } from '@/views/pitches/PitchesView';
import { NoAccessView, WorkspaceView } from '@/views/pitches/WorkspaceView';

import { makeMe, PERSONAL } from './fixtures';

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
  router.push.mockClear();
  router.refresh.mockClear();
  vi.stubGlobal('fetch', fetchMock);
  // jsdom has no modal dialog; open and close just toggle the attribute.
  HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement) {
    this.setAttribute('open', '');
  };
  HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement) {
    this.removeAttribute('open');
  };
});

afterEach(() => vi.unstubAllGlobals());

function sent(index: number) {
  const [path, init] = fetchMock.mock.calls[index] as unknown as [string, RequestInit];
  return { path, method: init.method, key: (init.headers as Record<string, string>)['Idempotency-Key'], body: init.body ? JSON.parse(String(init.body)) : undefined };
}

function failure(code: string, message: string, extra: Record<string, unknown> = {}) {
  return { error: { code, message, request_id: 'ref_7', recovery: { retryable: false }, ...extra } };
}

const MITRA = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
const ITEM_1 = '11111111-0000-4000-8000-000000000001';
const ITEM_2 = '11111111-0000-4000-8000-000000000002';

const SUMMARY: PitchSummary = {
  id: 'pitch-1',
  status: 'SUBMITTED',
  subject_type: 'SUPPORT_REQUEST',
  subject_id: 's1',
  subject_title: 'ClearSpring',
  opportunity_id: 'o1',
  opportunity_title: 'Validasi prototipe enam bulan',
  requester_party_id: PERSONAL,
  requester_name: 'Rani',
  recipient_party_id: MITRA,
  recipient_name: 'Mitra A',
  purpose: 'PROJECT',
  submitted_at: '2026-11-06T09:00:00Z',
  updated_at: '2026-11-06T10:00:00Z',
  waiting_on_party_id: MITRA,
};

const SUBMISSION = {
  number: 1,
  brief: 'Masalah: Air keruh.\nSaat ini: Kapasitas saring 10 L/jam.',
  snapshot: { opportunity: { version: 1 }, inventions: [{ title: 'ClearSpring', number: 1 }] },
  files: [{ document_id: 'd1', version: 1, title: 'Laporan uji fungsi ClearSpring' }],
  submitted_at: '2026-11-06T09:00:00Z',
};

function item(id: string, position: number, required: boolean, answer: Pitch['rounds'][number]['items'][number]['answer'] = null) {
  return {
    id,
    position,
    category: required ? 'Anggaran' : 'Fitur',
    question: required ? 'Apakah biaya pilot mencakup dua lokasi?' : 'Kapan 20 L/jam tersedia?',
    reason: 'Perlu untuk menyiapkan uji.',
    required,
    due_date: required ? '2026-11-09' : null,
    expected_evidence: '',
    review: null,
    review_note: null,
    version: 1,
    answer,
  };
}

function pitch(overrides: Partial<Pitch> = {}): Pitch {
  return { ...SUMMARY, version: 1, submissions: [SUBMISSION], decisions: [], rounds: [], allowed_actions: ['withdraw'], ...overrides };
}

/** The same pitch as Mitra A reads it. */
function incoming(overrides: Partial<Pitch> = {}): Pitch {
  return pitch({ requester_party_id: 'r1', recipient_party_id: PERSONAL, waiting_on_party_id: PERSONAL, allowed_actions: ['begin_review', 'approve', 'reject', 'request_revision', 'review_items'], ...overrides });
}

const MITRA_ME = makeMe({ persona: 'mitra' });

async function violations(element: ReactElement): Promise<string[]> {
  const { container } = render(element);
  let result: axe.AxeResults | undefined;
  await act(async () => {
    result = await axe.run(container, { rules: { 'color-contrast': { enabled: false }, region: { enabled: false }, 'landmark-unique': { enabled: false } } });
  });
  return result!.violations.map((violation) => `${violation.id}: ${violation.nodes.map((node) => node.target).join(', ')}`);
}

describe('pitch lists (S12)', () => {
  it('says whose turn it is from the API, with the update time and one open action', () => {
    render(
      <PitchesView
        me={MITRA_ME}
        box="masuk"
        pitches={[{ ...SUMMARY, requester_party_id: 'r1', recipient_party_id: PERSONAL, waiting_on_party_id: PERSONAL }]}
        total={1}
        filters={{}}
        capabilities={['core']}
      />,
    );
    expect(within(screen.getByRole('listitem')).getByText('Menunggu Anda')).toBeInTheDocument();
    expect(screen.getByText('Dukungan Proyek · dari Rani')).toBeInTheDocument();
    expect(screen.getByText(/^Diperbarui /)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Buka pitching ClearSpring → Validasi prototipe enam bulan' })).toHaveAttribute('href', '/pitches/pitch-1');
  });

  it('keeps the filters in a GET form and says when they hide everything', () => {
    render(<PitchesView me={makeMe()} box="outgoing" pitches={[]} total={2} filters={{ giliran: 'anda' }} capabilities={['core']} />);
    expect(screen.getByRole('form', { name: 'Saring pitching' })).toHaveAttribute('method', 'get');
    expect(screen.getByLabelText('Giliran')).toHaveValue('anda');
    expect(screen.getByRole('heading', { name: 'Tidak ada pitching dengan filter ini' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Hapus semua filter' })).toHaveAttribute('href', '/pitches');
  });

  it('filters by turn and status the same way for both sides', () => {
    const other = { ...SUMMARY, id: 'pitch-2', status: 'REVISION_REQUESTED', waiting_on_party_id: PERSONAL };
    expect(filterPitches([SUMMARY, other], { giliran: 'anda' }, PERSONAL).map((p) => p.id)).toEqual(['pitch-2']);
    expect(filterPitches([SUMMARY, other], { giliran: 'lain' }, PERSONAL).map((p) => p.id)).toEqual(['pitch-1']);
    expect(filterPitches([SUMMARY, other], { status: 'SUBMITTED' }, PERSONAL).map((p) => p.id)).toEqual(['pitch-1']);
    expect(turnOf({ waiting_on_party_id: null }, PERSONAL)).toBeNull();
    expect([tabOf('revisi'), tabOf('lain'), tabOf(undefined)]).toEqual(['revisi', 'ringkasan', 'ringkasan']);
  });

  it('says when nothing has been sent yet', () => {
    render(<PitchesView me={MITRA_ME} box="masuk" pitches={[]} total={0} filters={{}} capabilities={['core']} />);
    expect(screen.getByRole('heading', { name: 'Belum ada pitching masuk' })).toBeInTheDocument();
    expect(screen.queryByRole('form')).not.toBeInTheDocument();
  });

  it('has no axe violations', async () => {
    expect(await violations(<PitchesView me={makeMe()} box="outgoing" pitches={[SUMMARY]} total={1} filters={{}} capabilities={['core']} />)).toEqual([]);
  });
});

describe('pitch workspace (S13)', () => {
  it('shows the frozen submission, whose turn it is and the tabs, keeping the tab in the address', async () => {
    render(<WorkspaceView me={makeMe()} pitch={pitch()} tab="ringkasan" files={[]} justSent />);

    expect(screen.getByText('Pitching terkirim kepada Mitra A')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Menunggu Mitra A' })).toBeInTheDocument();
    expect(screen.getByText('Mandat versi 1 · ClearSpring versi 1')).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Ringkasan' })).toHaveAttribute('aria-selected', 'true');

    await userEvent.click(screen.getByRole('tab', { name: 'Dokumen' }));
    expect(router.push).toHaveBeenCalledWith('/pitches/pitch-1?tab=dokumen', { scroll: false });
    expect(screen.getByText('Laporan uji fungsi ClearSpring, versi 1 · kiriman 1')).toBeInTheDocument();

    screen.getByRole('tab', { name: 'Dokumen' }).focus();
    await userEvent.keyboard('{End}');
    expect(screen.getByRole('tab', { name: 'Riwayat' })).toHaveFocus();
    expect(screen.getByText(/^Kiriman 1 · /)).toBeInTheDocument();
  });

  it('approves through a dialog that names the acting party and what approval means', async () => {
    replies = [{ status: 200, body: { pitch_id: 'pitch-1', status: 'APPROVED_FOR_DISCUSSION', version: 2 } }];
    render(<WorkspaceView me={MITRA_ME} pitch={incoming()} tab="ringkasan" files={[]} justSent={false} />);
    expect(screen.getByRole('heading', { name: 'Tinjau pitching ini' })).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Setujui untuk diskusi' }));
    const dialog = screen.getByRole('dialog', { name: 'Setujui untuk diskusi' });
    expect(within(dialog).getByText('Anda bertindak sebagai Mitra A.')).toBeInTheDocument();
    expect(within(dialog).getByText('Persetujuan ini membuka diskusi; belum merupakan pendanaan atau kerja sama.')).toBeInTheDocument();
    await userEvent.click(within(dialog).getByRole('button', { name: 'Setujui untuk diskusi' }));

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(sent(0)).toMatchObject({ path: '/api/v1/pitches/pitch-1/decisions', body: { decision: 'APPROVE', submission: 1, expected_version: 1, acting_party_id: PERSONAL } });
    expect(sent(0).key).toBeTruthy();
  });

  it('refuses a rejection without a reason, then sends it, and shows a stale version as a conflict', async () => {
    replies = [{ status: 409, body: failure('STALE_VERSION', 'Data ini sudah diubah.', { current_version: 2 }) }];
    render(<WorkspaceView me={MITRA_ME} pitch={incoming()} tab="ringkasan" files={[]} justSent={false} />);

    await userEvent.click(screen.getByRole('button', { name: 'Tolak' }));
    const dialog = screen.getByRole('dialog', { name: 'Tolak pitching' });
    await userEvent.click(within(dialog).getByRole('button', { name: 'Tolak pitching' }));
    expect(within(dialog).getByText('Tuliskan alasan singkat.')).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();

    await userEvent.type(within(dialog).getByLabelText(/Alasan singkat/), 'Di luar fokus.');
    await userEvent.click(within(dialog).getByRole('button', { name: 'Tolak pitching' }));

    expect(await screen.findByText('Pitching ini baru saja berubah. Muat versi terbaru sebelum memutuskan.')).toBeInTheDocument();
    expect(sent(0).body).toMatchObject({ decision: 'REJECT', reason: 'Di luar fokus.' });
  });

  it('replaces decisions with a view-only notice for a member without decide_pitch', () => {
    render(<WorkspaceView me={MITRA_ME} pitch={incoming({ allowed_actions: [] })} tab="ringkasan" files={[]} justSent={false} />);
    expect(screen.getByText('Akun Anda hanya dapat melihat pitching ini')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Setujui untuk diskusi' })).not.toBeInTheDocument();
  });

  it('shows an unrelated account no title at all', () => {
    render(<NoAccessView me={makeMe()} />);
    expect(screen.getByRole('heading', { name: 'Anda belum memiliki akses' })).toBeInTheDocument();
    expect(screen.queryByText('ClearSpring')).not.toBeInTheDocument();
  });

  it('shows the rejection reason to the sender and nothing left to do', () => {
    const rejected = pitch({ status: 'REJECTED', waiting_on_party_id: null, allowed_actions: [], decisions: [{ decision: 'REJECT', reason: 'Di luar fokus.', submission_number: 1, decided_at: '2026-11-06T11:00:00Z' }] });
    render(<WorkspaceView me={makeMe()} pitch={rejected} tab="ringkasan" files={[]} justSent={false} />);
    expect(screen.getByText('Di luar fokus.')).toBeInTheDocument();
    expect(screen.queryByText('Akun Anda hanya dapat melihat pitching ini')).not.toBeInTheDocument();
  });

  it('has no axe violations', async () => {
    expect(await violations(<WorkspaceView me={MITRA_ME} pitch={incoming()} tab="ringkasan" files={[]} justSent={false} />)).toEqual([]);
  });
});

describe('revision tab (UX-11)', () => {
  const round = { number: 1, submission_number: 1, requested_at: '2026-11-06T10:00:00Z', open: true, items: [item(ITEM_1, 1, true), item(ITEM_2, 2, false)] };
  const inRevision = () => pitch({ status: 'REVISION_REQUESTED', waiting_on_party_id: PERSONAL, rounds: [round], allowed_actions: ['resubmit', 'withdraw', 'answer'] });
  const FILES = [{ document_id: 'd1', version: 2, title: 'Laporan uji fungsi ClearSpring' }];

  it('focuses the error summary when a required answer is not saved, and sends nothing', async () => {
    render(<WorkspaceView me={makeMe()} pitch={inRevision()} tab="revisi" files={FILES} justSent={false} />);
    expect(screen.getByRole('heading', { name: 'Jawab revisi putaran 1' })).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Kirim ulang kepada Mitra A' }));

    const summary = screen.getByRole('group', { name: 'Jawaban wajib belum tersimpan' });
    await waitFor(() => expect(summary).toHaveFocus());
    expect(within(summary).getByRole('link', { name: 'Simpan jawaban untuk “Apakah biaya pilot mencakup dua lokasi?”.' })).toHaveAttribute('href', `#item-${ITEM_1}-response-CAN`);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('saves an honest answer, keeps it when an attachment fails, then resubmits with the chosen file', async () => {
    replies = [
      { status: 422, body: failure('VALIDATION_FAILED', 'Ada isian yang belum valid.', { details: [{ loc: ['body', 'files', 0], msg: 'Pilih versi berkas Anda yang tersedia.' }] }) },
      { status: 200, body: { response: 'CANNOT', text: 'Belum.', files: [], version: 1, saved_at: '2026-11-06T10:05:00Z' } },
      { status: 200, body: { pitch_id: 'pitch-1', status: 'SUBMITTED', version: 3, submission: 2 } },
    ];
    render(<WorkspaceView me={makeMe()} pitch={inRevision()} tab="revisi" files={FILES} justSent={false} />);
    await userEvent.click(screen.getAllByLabelText(/Belum dapat dipenuhi/)[0]);
    await userEvent.type(screen.getAllByLabelText('Penjelasan')[0], 'Belum.');
    await userEvent.click(screen.getByLabelText('Laporan uji fungsi ClearSpring, versi 2', { selector: `#item-${ITEM_1}-file-d1-v2` }));
    await userEvent.click(screen.getByRole('button', { name: 'Simpan jawaban 1' }));
    expect(await screen.findByText('Pilih versi berkas Anda yang tersedia.')).toBeInTheDocument();
    expect(screen.getAllByLabelText('Penjelasan')[0]).toHaveValue('Belum.');

    await userEvent.click(screen.getByLabelText('Laporan uji fungsi ClearSpring, versi 2', { selector: `#item-${ITEM_1}-file-d1-v2` }));
    await userEvent.click(screen.getByRole('button', { name: 'Simpan jawaban 1' }));
    await waitFor(() => expect(screen.getAllByText('Tersimpan')).toHaveLength(1));
    await userEvent.click(screen.getByLabelText('Laporan uji fungsi ClearSpring, versi 2', { selector: '#share-d1-v2' }));
    await userEvent.click(screen.getByRole('button', { name: 'Kirim ulang kepada Mitra A' }));

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(sent(1)).toMatchObject({ method: 'PUT', body: { response: 'CANNOT', text: 'Belum.', files: [], expected_version: null } });
    expect(sent(2)).toMatchObject({ path: '/api/v1/pitches/pitch-1/resubmit', body: { files: [{ document_id: 'd1', version: 2 }] } });
  });

  it('lets the recipient open a round only with complete items', async () => {
    replies = [{ status: 201, body: { pitch_id: 'pitch-1', status: 'REVISION_REQUESTED', version: 2, round: 1 } }];
    render(<WorkspaceView me={MITRA_ME} pitch={incoming()} tab="revisi" files={[]} justSent={false} />);

    await userEvent.click(screen.getByRole('button', { name: 'Kirim permintaan revisi kepada Rani' }));
    expect(screen.getByRole('link', { name: 'Butir 1: tulis pertanyaan.' })).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText(/Kategori/), 'Anggaran');
    await userEvent.type(screen.getByLabelText(/^Pertanyaan/), 'Apakah biaya pilot mencakup dua lokasi?');
    await userEvent.type(screen.getByLabelText(/^Alasan/), 'Perlu untuk uji.');
    await userEvent.click(screen.getByRole('button', { name: 'Kirim permintaan revisi kepada Rani' }));

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(sent(0)).toMatchObject({ path: '/api/v1/pitches/pitch-1/revision-rounds', body: { submission: 1, items: [{ category: 'Anggaran', required: true, due_date: null }] } });
  });

  it('keeps earlier rounds visible and lets the recipient mark each answer', async () => {
    replies = [{ status: 200, body: { id: ITEM_1, review: 'ACCEPTED', review_note: null, version: 2 } }];
    const answered = { ...round, open: false, items: [item(ITEM_1, 1, true, { response: 'CANNOT', text: 'Belum.', files: [], version: 1, saved_at: '2026-11-06T10:05:00Z' })] };
    render(<WorkspaceView me={MITRA_ME} pitch={incoming({ rounds: [answered], submissions: [SUBMISSION, { ...SUBMISSION, number: 2 }] })} tab="revisi" files={[]} justSent={false} />);

    expect(screen.getByText('Belum dapat dipenuhi')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Terima jawaban 1' }));

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(sent(0)).toMatchObject({ method: 'PUT', path: `/api/v1/pitches/pitch-1/revision-items/${ITEM_1}/review`, body: { result: 'ACCEPTED', expected_version: 1 } });
  });

  it('hides draft answers of an open round from the recipient', () => {
    const drafted = { ...round, items: [item(ITEM_1, 1, true)] };
    render(<WorkspaceView me={MITRA_ME} pitch={incoming({ status: 'REVISION_REQUESTED', waiting_on_party_id: 'r1', allowed_actions: [], rounds: [drafted] })} tab="revisi" files={[]} justSent={false} />);
    expect(screen.getByText('Jawaban terlihat setelah pengirim mengirim ulang.')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Menunggu Rani' })).toBeInTheDocument();
  });

  it('has no axe violations while answering', async () => {
    expect(await violations(<WorkspaceView me={makeMe()} pitch={inRevision()} tab="revisi" files={FILES} justSent={false} />)).toEqual([]);
  });
});

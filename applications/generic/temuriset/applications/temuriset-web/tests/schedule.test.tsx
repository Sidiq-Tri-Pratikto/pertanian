import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';

import { DiscussionPanel, POLL_MS, type Message } from '@/features/discussion/DiscussionPanel';
import { destinationFor } from '@/features/destinations';
import type { Meeting, Proposal, Schedule } from '@/features/scheduling/api';
import { SchedulePanel } from '@/features/scheduling/SchedulePanel';
import { DestinationView } from '@/views/DestinationView';

import { makeMe, PERSONAL } from './fixtures';

const router = { push: vi.fn(), replace: vi.fn(), refresh: vi.fn() };
vi.mock('next/navigation', () => ({ useRouter: () => router }));

type Reply = { status: number; body?: unknown; text?: string } | 'network';
let replies: Reply[] = [];
const fetchMock = vi.fn(async (path: string) => {
  if (String(path).endsWith('calendar.ics')) return new Response('BEGIN:VCALENDAR\r\nDTSTART:20261104T100000Z\r\nEND:VCALENDAR\r\n', { status: 200 });
  const reply = replies.shift() ?? { status: 500, body: {} };
  if (reply === 'network') throw new TypeError('Failed to fetch');
  return new Response(reply.body === undefined ? null : JSON.stringify(reply.body), { status: reply.status });
});

beforeEach(() => {
  replies = [];
  fetchMock.mockClear();
  router.refresh.mockClear();
  vi.stubGlobal('fetch', fetchMock);
  HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement) {
    this.setAttribute('open', '');
  };
  HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement) {
    this.removeAttribute('open');
  };
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

function sentBodies() {
  return fetchMock.mock.calls
    .map((call) => call as unknown as [string, RequestInit | undefined])
    .filter(([path, init]) => init?.method && !path.endsWith('calendar.ics'))
    .map(([path, init]) => ({ path, body: JSON.parse(String(init!.body)) }));
}

const failure = (code: string, message: string, extra: Record<string, unknown> = {}) => ({ error: { code, message, request_id: 'ref_5', recovery: { retryable: false }, ...extra } });

const MITRA = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
const slot = (id: string, start: string, end: string, position: number) => ({ id, position, starts_at: start, ends_at: end });

function proposal(overrides: Partial<Proposal> = {}): Proposal {
  return {
    id: 'p1',
    proposed_by_party_id: MITRA,
    proposed_by_name: 'Mitra A',
    mine: false,
    minutes: 60,
    time_zone: 'Asia/Makassar',
    agenda: 'Membahas rencana validasi enam bulan',
    link: null,
    state: 'OPEN',
    expired_reason: null,
    replaces_meeting_id: null,
    accepted_slot_id: null,
    version: 1,
    created_at: '2026-11-02T08:00:00Z',
    expires_at: '2026-11-04T09:00:00Z',
    slots: [
      slot('s1', '2026-11-04T09:00:00Z', '2026-11-04T10:00:00Z', 1),
      slot('s2', '2026-11-04T11:00:00Z', '2026-11-04T12:00:00Z', 2),
      slot('s3', '2026-11-04T13:00:00Z', '2026-11-04T14:00:00Z', 3),
    ],
    ...overrides,
  };
}

function meeting(overrides: Partial<Meeting> = {}): Meeting {
  return {
    id: 'm1',
    proposal_id: 'p1',
    starts_at: '2026-11-04T10:00:00Z',
    ends_at: '2026-11-04T11:00:00Z',
    time_zone: 'Asia/Makassar',
    agenda: 'Membahas rencana validasi enam bulan',
    link: null,
    state: 'CONFIRMED',
    version: 1,
    started: false,
    outcomes: [],
    disagreement: false,
    ...overrides,
  };
}

const schedule = (overrides: Partial<Schedule> = {}): Schedule => ({ proposals: [], meetings: [], can_schedule: true, external_calendar: 'unknown', ...overrides });

function panel(value: Schedule, approved = true) {
  return <SchedulePanel pitchId="pitch-1" approved={approved} schedule={value} actingPartyId={PERSONAL} zone="Asia/Jakarta" />;
}

describe('schedule tab (S14, UX-13, UX-14)', () => {
  it('shows each slot in the reader zone and the proposer zone, and a choice is not yet a booking', async () => {
    render(panel(schedule({ proposals: [proposal()] })));

    expect(screen.getByText('Waktu ditampilkan dalam WIB (Asia/Jakarta).')).toBeInTheDocument();
    expect(screen.getByText('16.00–17.00 WIB (Asia/Jakarta)')).toBeInTheDocument();
    expect(screen.getAllByText(/Pihak lain: 17\.00–18\.00 WITA \(Asia\/Makassar\)/)).toHaveLength(1);
    expect(screen.getByRole('button', { name: 'Konfirmasi waktu' })).toHaveAttribute('aria-disabled', 'true');

    await userEvent.click(screen.getByRole('radio', { name: /18\.00–19\.00 WIB/ }));
    expect(screen.getByText('Dipilih, belum dikonfirmasi')).toBeInTheDocument();
    expect(fetchMock.mock.calls.filter(([path]) => !String(path).endsWith('.ics'))).toHaveLength(0);
  });

  it('explains a conflict in a live alert, keeps the agenda and other slots, and pre-fills the alternatives', async () => {
    replies = [{ status: 409, body: failure('BOOKING_CONFLICT', 'Waktu ini bentrok dengan jadwal peserta. Pilih waktu lain atau usulkan waktu baru.', { slot_id: 's1' }) }];
    render(panel(schedule({ proposals: [proposal()] })));

    await userEvent.click(screen.getByRole('radio', { name: /16\.00–17\.00 WIB/ }));
    await userEvent.click(screen.getByRole('button', { name: 'Konfirmasi waktu' }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('Waktu ini bentrok dengan jadwal peserta.');
    expect(screen.getByText('Waktu sudah bentrok')).toBeInTheDocument();
    expect(screen.getByText('Membahas rencana validasi enam bulan')).toBeInTheDocument();
    expect(sentBodies()[0]).toMatchObject({ path: '/api/v1/schedule-proposals/p1/accept', body: { slot_id: 's1', expected_version: 1 } });

    await userEvent.click(screen.getByRole('button', { name: 'Usulkan waktu lain' }));
    expect(screen.getByLabelText('Waktu 1')).toHaveValue('2026-11-04T18:00');
    expect(screen.getByLabelText('Waktu 2')).toHaveValue('2026-11-04T20:00');
  });

  it('sends a proposal as UTC instants from the reader zone and refuses an incomplete one', async () => {
    replies = [{ status: 201, body: proposal({ mine: true }) }];
    render(panel(schedule()));

    await userEvent.click(screen.getByRole('button', { name: 'Kirim usulan waktu' }));
    expect(screen.getByRole('link', { name: 'Usulkan setidaknya 2 waktu.' })).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText('Waktu 1'), '2026-11-04T16:00');
    await userEvent.type(screen.getByLabelText('Waktu 2'), '2026-11-04T18:00');
    await userEvent.type(screen.getByLabelText(/Agenda/), 'Membahas rencana');
    await userEvent.click(screen.getByRole('button', { name: 'Kirim usulan waktu' }));

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(sentBodies()[0].body).toMatchObject({ slots: ['2026-11-04T09:00:00.000Z', '2026-11-04T11:00:00.000Z'], minutes: 60, time_zone: 'Asia/Jakarta', replaces_meeting_id: null });
  });

  it('states why a proposal expired and that the pitch stays approved', () => {
    render(panel(schedule({ proposals: [proposal({ state: 'EXPIRED', expired_reason: 'ALL_PAST' })] })));
    expect(screen.getByText('Semua waktu yang diusulkan sudah lewat. Pitching tetap disetujui untuk diskusi.')).toBeInTheDocument();
  });

  it('keeps the confirmed meeting beside a pending replacement, with the calendar file readable', async () => {
    render(panel(schedule({ meetings: [meeting()], proposals: [proposal({ id: 'p2', replaces_meeting_id: 'm1' })] })));

    expect(screen.getByRole('heading', { name: 'Pertemuan dikonfirmasi' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Usulan jadwal pengganti' })).toBeInTheDocument();
    expect(screen.getByText(/pertemuan ini tetap berlaku sampai penggantinya dikonfirmasi/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Unduh ICS' })).toHaveAttribute('href', '/api/v1/meetings/m1/calendar.ics');
    expect(await screen.findByText(/DTSTART:20261104T100000Z/)).toBeInTheDocument();
  });

  it('asks for an outcome once the meeting started, and shows a disagreement', async () => {
    replies = [{ status: 200, body: meeting({ started: true }) }];
    const outcomes = [
      { party_id: PERSONAL, party_name: 'Rani', result: 'COMPLETED' as const, note: '' },
      { party_id: MITRA, party_name: 'Mitra A', result: 'NO_SHOW' as const, note: '' },
    ];
    render(panel(schedule({ meetings: [meeting({ started: true, outcomes, disagreement: true })] })));

    expect(screen.getByText('Catatan kedua pihak berbeda')).toBeInTheDocument();
    expect(screen.getByText('Mitra A: Tidak terlaksana')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Pertemuan selesai' }));
    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(sentBodies()[0]).toMatchObject({ path: '/api/v1/meetings/m1/outcome', body: { result: 'COMPLETED' } });
  });

  it('shows a completed panel instead of the proposal form, and waits for approval first', () => {
    const { unmount } = render(panel(schedule({ meetings: [meeting({ state: 'COMPLETED' })] })));
    expect(screen.getByRole('heading', { name: 'Pertemuan selesai dicatat kedua pihak' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Kirim usulan waktu' })).not.toBeInTheDocument();
    unmount();

    render(panel(schedule({ can_schedule: false }), false));
    expect(screen.getByText('Jadwal tersedia setelah pitching disetujui untuk diskusi.')).toBeInTheDocument();
  });

  it('has no axe violations with an open proposal', async () => {
    const { container } = render(panel(schedule({ proposals: [proposal()] })));
    let result: axe.AxeResults | undefined;
    await act(async () => {
      result = await axe.run(container, { rules: { 'color-contrast': { enabled: false }, region: { enabled: false } } });
    });
    expect(result!.violations.map((violation) => violation.id)).toEqual([]);
  });
});

describe('discussion tab', () => {
  const MESSAGE: Message = { id: 'msg1', author_party_id: MITRA, author_name: 'Mitra A', mine: false, text: 'Halo Rani.', created_at: '2026-11-06T09:00:00Z' };
  const parties = [
    { id: PERSONAL, name: 'Rani' },
    { id: MITRA, name: 'Mitra A' },
  ];

  it('keeps the text when a send fails, then sends it once', async () => {
    replies = [
      { status: 503, body: failure('SERVICE_UNAVAILABLE', 'Layanan sedang sibuk.') },
      { status: 201, body: { ...MESSAGE, id: 'msg2', mine: true, author_party_id: PERSONAL, author_name: 'Rani', text: 'Bisa minggu depan?' } },
    ];
    render(<DiscussionPanel pitchId="pitch-1" open messages={[MESSAGE]} tasks={[]} parties={parties} actingPartyId={PERSONAL} zone="Asia/Jakarta" />);

    await userEvent.type(screen.getByLabelText('Pesan baru'), 'Bisa minggu depan?');
    await userEvent.click(screen.getByRole('button', { name: 'Kirim pesan' }));
    expect(await screen.findByText(/Pesan Anda masih ada di kotak isian/)).toBeInTheDocument();
    expect(screen.getByLabelText('Pesan baru')).toHaveValue('Bisa minggu depan?');

    await userEvent.click(screen.getByRole('button', { name: 'Kirim pesan' }));
    expect(await screen.findByText('Bisa minggu depan?', { selector: 'p' })).toBeInTheDocument();
    expect(screen.getByLabelText('Pesan baru')).toHaveValue('');
  });

  it('polls for newer messages every 30 seconds', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    replies = [{ status: 200, body: [{ ...MESSAGE, id: 'msg3', text: 'Pesan baru dari Mitra A.' }] }];
    render(<DiscussionPanel pitchId="pitch-1" open messages={[MESSAGE]} tasks={[]} parties={parties} actingPartyId={PERSONAL} zone="Asia/Jakarta" />);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(POLL_MS);
    });

    expect(await screen.findByText('Pesan baru dari Mitra A.')).toBeInTheDocument();
    expect(String(fetchMock.mock.calls[0][0])).toBe(`/api/v1/pitches/pitch-1/messages?since=${encodeURIComponent(MESSAGE.created_at)}`);
  });

  it('adds a task for one of the two parties and completes it', async () => {
    replies = [{ status: 201, body: {} }, { status: 200, body: {} }];
    const task = { id: 't1', title: 'Kirim rincian biaya', owner_party_id: PERSONAL, owner_name: 'Rani', due_date: '2026-11-20', reference: 'Butir 1', status: 'OPEN' as const, version: 1, created_at: '2026-11-06T09:00:00Z' };
    render(<DiscussionPanel pitchId="pitch-1" open messages={[]} tasks={[task]} parties={parties} actingPartyId={PERSONAL} zone="Asia/Jakarta" />);

    expect(screen.getByText('Untuk Rani · batas 2026-11-20 · Butir 1')).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText('Tugas baru'), 'Siapkan lokasi uji');
    await userEvent.selectOptions(screen.getByLabelText('Penanggung jawab'), MITRA);
    await userEvent.click(screen.getByRole('button', { name: 'Tambah tugas' }));
    await waitFor(() => expect(router.refresh).toHaveBeenCalledTimes(1));
    await userEvent.click(screen.getByRole('button', { name: 'Tandai selesai: Kirim rincian biaya' }));
    await waitFor(() => expect(router.refresh).toHaveBeenCalledTimes(2));

    expect(sentBodies().map((item) => item.path)).toEqual(['/api/v1/pitches/pitch-1/tasks', '/api/v1/tasks/t1/complete']);
    expect(sentBodies()[0].body).toMatchObject({ title: 'Siapkan lokasi uji', owner_party_id: MITRA, due_date: null });
  });
});

describe('Beranda (S02)', () => {
  it('leads with what waits on the reader and marks the rest by turn, with notifications', () => {
    render(
      <DestinationView
        me={makeMe()}
        destination={destinationFor('home', 'inovator')}
        capabilities={['core']}
        queue={[
          { href: '/pitches/p1?tab=revisi', label: 'Jawab permintaan revisi', context: 'ClearSpring → Validasi', who: 'you', text: 'Pertanyaan wajib perlu dijawab.' },
          { href: '/pitches/p2?tab=jadwal', label: 'Menunggu pihak lain memilih waktu', context: 'GridShare → Uji', who: 'other' },
        ]}
        notifications={[{ id: 'n1', pitch_id: 'p1', text: 'Revisi diminta: ClearSpring → Validasi', tab: 'revisi', created_at: '2026-11-06T09:00:00Z', read: false }]}
      />,
    );

    expect(screen.getByRole('heading', { name: 'Jawab permintaan revisi' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Kerjakan sekarang: ClearSpring → Validasi' })).toHaveAttribute('href', '/pitches/p1?tab=revisi');
    const rest = screen.getByRole('region', { name: 'Perlu diperhatikan' });
    expect(within(rest).getByText('Menunggu pihak lain')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Revisi diminta: ClearSpring → Validasi' })).toHaveAttribute('href', '/pitches/p1?tab=revisi');
    expect(screen.getByText(/Belum dibaca/)).toBeInTheDocument();
  });
});

it('announces viewer-only calendar advice without disabling an externally busy slot', async () => {
  const ordinary = proposal();
  const { container } = render(panel(schedule({
    external_calendar: 'advisory',
    proposals: [{
      ...ordinary,
      slots: [
        { ...ordinary.slots[0], external_availability: 'busy' },
        { ...ordinary.slots[1], external_availability: 'free' },
        ordinary.slots[2],
      ],
    }],
  })));

  expect(screen.getByText(/berasal dari kalender Anda/)).toBeVisible();
  const busy = screen.getByRole('radio', { name: /Kalender Anda: sibuk/ });
  expect(busy).toBeEnabled();
  expect(screen.getByRole('radio', { name: /Kalender Anda: kosong/ })).toBeEnabled();
  await userEvent.click(busy);
  expect(busy).toBeChecked();
  expect(screen.getByRole('button', { name: 'Konfirmasi waktu' })).not.toHaveAttribute('aria-disabled', 'true');
  expect((await axe.run(container)).violations).toEqual([]);
});

it('states external availability is unknown when the adapter cannot determine it', () => {
  render(panel(schedule({ proposals: [proposal()] })));
  expect(screen.getByText(/Ketersediaan di kalender luar belum diketahui/)).toBeVisible();
  expect(screen.queryByText(/Kalender Anda: (sibuk|kosong)/)).not.toBeInTheDocument();
});

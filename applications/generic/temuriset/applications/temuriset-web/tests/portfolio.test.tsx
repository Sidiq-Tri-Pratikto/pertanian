import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { draftRequest, initialState, reduce } from '@/features/portfolio/editor-state';
import type { Invention, PublicInvention } from '@/features/portfolio/model';
import { EditorView } from '@/views/portfolio/EditorView';
import { InventionsView, InventionView } from '@/views/portfolio/InventionViews';

import { makeMe } from './fixtures';

const router = { push: vi.fn(), replace: vi.fn(), refresh: vi.fn() };
vi.mock('next/navigation', () => ({ useRouter: () => router }));

const ID = '00000000-0000-4000-8000-00000000cafe';

function version(overrides: Partial<NonNullable<Invention['draft']>> = {}): NonNullable<Invention['draft']> {
  return {
    number: 1,
    state: 'draft',
    title: 'Saringan air keramik desa',
    summary: 'Saringan untuk desa.',
    problem: 'Air keruh.',
    solution: 'Saringan keramik.',
    intended_users: 'Rumah tangga',
    sector: 'Air bersih',
    stage: 'PROTOTYPE',
    keywords: ['air'],
    facts: [
      { label: 'Kapasitas saring', value: '10', unit: 'L/jam', timing: 'CURRENT', provenance: 'SELF_DECLARED', key: null, document_version_id: null },
      { label: 'Kapasitas saring', value: '20', unit: 'L/jam', timing: 'PLANNED', provenance: 'SELF_DECLARED', key: null, document_version_id: null },
    ],
    claims: [{ kind: 'authority', subject_name: 'Rani', party_id: null, scope: '', status: 'not_established', source: '', asserted_at: null }],
    private_notes: 'Biaya rahasia',
    published_at: null,
    ...overrides,
  };
}

function invention(overrides: Partial<Invention> = {}): Invention {
  return { id: ID, managing_party_id: 'p', status: 'DRAFT', version: 2, draft: version(), published: null, history: [1], operation_id: null, ...overrides };
}

type Reply = { status: number; body?: unknown };
let replies: Reply[] = [];
const fetchMock = vi.fn(async () => {
  const reply = replies.shift() ?? { status: 500, body: {} };
  return new Response(reply.body === undefined ? null : JSON.stringify(reply.body), { status: reply.status });
});

function sent(index: number) {
  const [path, init] = fetchMock.mock.calls[index] as unknown as [string, RequestInit];
  return { path, method: init?.method, key: (init?.headers as Record<string, string> | undefined)?.['Idempotency-Key'], body: init?.body ? JSON.parse(String(init.body)) : undefined };
}

function failure(code: string, extra: Record<string, unknown> = {}) {
  return { error: { code, message: 'Gagal.', request_id: 'ref_1', recovery: { retryable: false }, ...extra } };
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

describe('editor state machine', () => {
  it('keeps one key across a failed save and its retry, and drops it after an edit', () => {
    let state = initialState(invention());
    state = reduce(state, { type: 'save', key: 'k1' });
    state = reduce(state, { type: 'failed' });
    expect(state).toMatchObject({ status: 'failed', pendingKey: 'k1', values: { title: 'Saringan air keramik desa' } });

    state = reduce(state, { type: 'save', key: 'k2' });
    expect(state.pendingKey).toBe('k1');

    state = reduce(reduce(state, { type: 'failed' }), { type: 'edit', values: { ...state.values, title: 'Baru' } });
    expect(state).toMatchObject({ status: 'local', pendingKey: null });

    state = reduce(reduce(state, { type: 'save', key: 'k3' }), { type: 'saved', version: 3 });
    expect(state).toMatchObject({ status: 'saved', version: 3, pendingKey: null });
  });

  it('records the current version on a conflict and starts again from a reload', () => {
    const conflict = reduce(initialState(invention()), { type: 'conflict', currentVersion: 5 });
    expect(conflict).toMatchObject({ status: 'conflict', currentVersion: 5 });

    const reloaded = reduce(conflict, { type: 'reloaded', invention: invention({ version: 5, draft: version({ title: 'Dari tab lain' }) }) });
    expect(reloaded).toMatchObject({ status: 'saved', version: 5, values: { title: 'Dari tab lain' } });
  });

  it('sends the whole draft and drops unfinished rows', () => {
    const values = { ...initialState(invention()).values, keywords: ' air, ,keramik ', facts: [...version().facts, { label: '', value: '', timing: 'CURRENT' as const }] };

    const body = draftRequest(values, 2, 'party');

    expect(body).toMatchObject({ acting_party_id: 'party', expected_version: 2, keywords: ['air', 'keramik'], stage: 'PROTOTYPE' });
    expect(body.facts).toHaveLength(2);
  });
});

describe('the four-step editor (S05)', () => {
  it('saves step 1, says Tersimpan and opens step 2 with focus on its heading', async () => {
    const user = userEvent.setup();
    replies = [{ status: 200, body: invention({ version: 3 }) }];
    render(<EditorView me={makeMe()} invention={invention()} initialStep={1} />);

    await user.clear(screen.getByRole('textbox', { name: /Judul/ }));
    await user.type(screen.getByRole('textbox', { name: /Judul/ }), 'Judul baru');
    expect(screen.getByRole('status', { name: '' })).toHaveTextContent('Belum tersimpan');
    await user.click(screen.getByRole('button', { name: 'Simpan dan lanjutkan' }));

    await waitFor(() => expect(screen.getByRole('heading', { level: 2, name: 'Yang sudah ada dan bukti' })).toHaveFocus());
    expect(screen.getByText('Tersimpan')).toBeInTheDocument();
    expect(sent(0)).toMatchObject({ path: `/api/v1/inventions/${ID}/draft`, method: 'PUT', body: { title: 'Judul baru', expected_version: 2 } });
    expect(sent(0).key).toBeTruthy();
  });

  it('keeps every value after a failed save and retries with the same key', async () => {
    const user = userEvent.setup();
    replies = [{ status: 503, body: failure('DATABASE_UNAVAILABLE') }, { status: 200, body: invention({ version: 3 }) }];
    render(<EditorView me={makeMe()} invention={invention()} initialStep={1} />);

    await user.type(screen.getByRole('textbox', { name: /Siapa penggunanya/ }), ' desa');
    await user.click(screen.getByRole('button', { name: 'Simpan dan lanjutkan' }));
    expect(await screen.findByText('Gagal menyimpan')).toBeInTheDocument();
    expect(screen.getByText('Isian Anda masih ada di halaman ini.')).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /Siapa penggunanya/ })).toHaveValue('Rumah tangga desa');

    await user.click(screen.getByRole('button', { name: 'Coba lagi' }));

    expect(await screen.findByText('Tersimpan')).toBeInTheDocument();
    expect(sent(1).key).toBe(sent(0).key);
  });

  it('shows the conflict with the local text and reloads the current revision (UX-03)', async () => {
    const user = userEvent.setup();
    replies = [
      { status: 409, body: failure('STALE_VERSION', { current_version: 4 }) },
      { status: 200, body: invention({ version: 4, draft: version({ title: 'Dari tab lain' }) }) },
    ];
    render(<EditorView me={makeMe()} invention={invention()} initialStep={1} />);

    await user.click(screen.getByRole('button', { name: 'Simpan dan lanjutkan' }));
    const conflict = await screen.findByRole('group', { name: 'Versi berubah' });
    expect(conflict).toHaveTextContent('Versi terbaru: 4');
    expect(conflict).toHaveTextContent('Saringan air keramik desa');
    await user.click(within(conflict).getByRole('button', { name: 'Muat versi terbaru' }));

    await waitFor(() => expect(screen.getByRole('textbox', { name: /Judul/ })).toHaveValue('Dari tab lain'));
  });

  it('sends publication errors to the first step with an error and links each field', async () => {
    const user = userEvent.setup();
    replies = [
      {
        status: 422,
        body: failure('VALIDATION_FAILED', {
          details: [
            { loc: ['body', 'facts'], msg: 'Tambahkan setidaknya satu kemampuan yang sudah ada saat ini.', type: 'publication' },
            { loc: ['body', 'title'], msg: 'Judul perlu 5 sampai 120 karakter.', type: 'publication' },
          ],
        }),
      },
    ];
    render(<EditorView me={makeMe()} invention={invention({ draft: version({ title: 'Ide' }) })} initialStep={4} />);

    await user.click(screen.getByRole('button', { name: 'Terbitkan versi 1' }));

    const summary = await screen.findByRole('group', { name: 'Masih ada yang perlu diperbaiki' });
    expect(summary).toHaveFocus();
    expect(screen.getByRole('heading', { level: 2, name: 'Dasar' })).toBeInTheDocument();
    expect(within(summary).getByRole('link', { name: 'Judul perlu 5 sampai 120 karakter.' })).toHaveAttribute('href', '#judul');
    expect(within(summary).getByRole('link', { name: /satu kemampuan/ })).toHaveAttribute('href', '#fakta-0-label');
    expect(screen.getByRole('textbox', { name: /Judul/ })).toHaveAttribute('aria-invalid', 'true');
  });

  it('previews the public card, what stays private and the effect, then publishes (AC12)', async () => {
    const user = userEvent.setup();
    replies = [{ status: 200, body: { version: 1, status: 'PUBLISHED' } }];
    render(<EditorView me={makeMe()} invention={invention()} initialStep={4} />);

    expect(screen.getByRole('heading', { level: 3, name: 'Saringan air keramik desa' })).toBeInTheDocument();
    expect(screen.getByText('Catatan pribadi')).toBeInTheDocument();
    expect(screen.queryByText('Biaya rahasia')).toBeNull();
    expect(screen.getByText(/Versi 1 dapat dilihat semua pengguna/)).toBeInTheDocument();
    expect(screen.getByText(/Diterbitkan atas nama:/)).toHaveTextContent('Rani · Pribadi');
    await user.click(screen.getByRole('button', { name: 'Terbitkan versi 1' }));

    await waitFor(() => expect(router.push).toHaveBeenCalledWith(`/inventions/${ID}?terbit=1`));
    expect(sent(0)).toMatchObject({ path: `/api/v1/inventions/${ID}/publish`, body: { expected_version: 2 } });
  });

  it('adds and removes facts and claims, and keeps them across steps', async () => {
    const user = userEvent.setup();
    render(<EditorView me={makeMe()} invention={invention({ draft: version({ facts: [], claims: [] }) })} initialStep={2} />);

    await user.click(screen.getByRole('button', { name: 'Tambah fakta' }));
    await user.type(screen.getByRole('textbox', { name: 'Apa yang diukur' }), 'Kapasitas');
    await user.click(screen.getByRole('button', { name: 'Tambah klaim' }));
    await user.type(screen.getByRole('textbox', { name: 'Nama' }), 'Rani');
    await user.click(screen.getByRole('button', { name: /Dasar/ }));
    await user.click(screen.getByRole('button', { name: /Yang sudah ada dan bukti/ }));

    expect(screen.getByRole('textbox', { name: 'Apa yang diukur' })).toHaveValue('Kapasitas');
    await user.click(screen.getByRole('button', { name: /Hapus klaim/ }));
    expect(screen.queryByRole('textbox', { name: 'Nama' })).toBeNull();
    expect(screen.getByText(/Dokumen bukti dapat diunggah/)).toBeInTheDocument();
  });
});

describe('Inovasi Saya and the detail (S04)', () => {
  it('explains publication and offers to add one when there is none', () => {
    render(<InventionsView me={makeMe()} inventions={[]} />);

    expect(screen.getByText('Belum ada inovasi')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Tambah inovasi' })).toBeInTheDocument();
  });

  it('marks a published invention with a pending draft', () => {
    render(<InventionsView me={makeMe()} inventions={[{ id: ID, status: 'PUBLISHED', title: 'Saringan', version: 4, has_draft: true, published_number: 1 }]} />);

    expect(screen.getByText('Ada draf perubahan')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Buka\s*Saringan/ })).toHaveAttribute('href', `/inventions/${ID}`);
  });

  it('starts a new invention and opens step 1', async () => {
    const user = userEvent.setup();
    replies = [{ status: 201, body: invention() }];
    render(<InventionsView me={makeMe()} inventions={[]} />);

    await user.click(screen.getByRole('button', { name: 'Tambah inovasi' }));

    await waitFor(() => expect(router.push).toHaveBeenCalledWith(`/inventions/${ID}/edit?step=1`));
  });

  it('shows the owner current and planned facts with provenance, and claims not yet established (UX-04)', () => {
    render(<InventionView me={makeMe()} invention={invention({ status: 'PUBLISHED', published: version({ state: 'published' }), draft: null })} justPublished={1} />);

    expect(screen.getByText('Versi 1 sudah terbit')).toBeInTheDocument();
    expect(screen.getAllByText('Saat ini')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Direncanakan').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Dinyatakan sendiri')).toHaveLength(2);
    expect(screen.getByText(/Belum ditetapkan/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Ubah inovasi' })).toHaveAttribute('href', `/inventions/${ID}/edit?step=1`);
  });

  it('shows a partner only the public projection and "Simpan inovasi"', () => {
    const publicView: PublicInvention = {
      id: ID,
      managing_party_name: 'Rani',
      number: 1,
      title: 'Saringan air keramik desa',
      summary: '',
      problem: 'Air keruh.',
      solution: 'Saringan keramik.',
      intended_users: 'Rumah tangga',
      sector: 'Air bersih',
      stage: 'PROTOTYPE',
      keywords: [],
      facts: [],
      claims: [],
      published_at: null,
    };
    render(<InventionView me={makeMe({ persona: 'mitra' })} publicView={publicView} />);

    expect(screen.getByText('Dikelola Rani')).toBeInTheDocument();
    expect(screen.getByText(/Dokumen dibagikan per pitching/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Simpan inovasi' })).toHaveAttribute('aria-disabled', 'true');
    expect(screen.queryByRole('link', { name: 'Ubah inovasi' })).toBeNull();
  });

  it('says so when the invention is not available', () => {
    render(<InventionView me={makeMe()} />);

    expect(screen.getByText('Inovasi ini tidak tersedia')).toBeInTheDocument();
  });
});

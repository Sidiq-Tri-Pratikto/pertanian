// Recorded on 2026-11-07 from the merged hematdaya-api at 42aeebc (Alembic head 0009), by real `empty` and `h-base` demo sessions.
import * as DocumentPicker from 'expo-document-picker';
import { router } from 'expo-router';
import { act, fireEvent, renderRouter, screen, waitFor, within } from 'expo-router/testing-library';
import { AccessibilityInfo, Platform, StyleSheet } from 'react-native';
import { seedConfirmedWorkspace } from './fixtures/workspaces';

import type { ImportCommit, ImportPreview } from '@/api/client';
import { tokens } from '@/design/tokens.generated';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { storeDraft, writeRecovery, type CommitIntent, type DraftSnapshot } from '@/features/imports/draft-store';
import { ownerStorageKey } from '@/features/offline/owner-storage';
import { saveWorkspace, type Workspace } from '@/features/workspace/workspace-store';
import { EXAMPLES } from '@/features/imports/examples';

import recorded from './fixtures/imports.json';

type Envelope = { error: { code: string; message: string; request_id: string; recovery: object; details?: { loc: unknown[]; msg: string; type: string }[] } };
type Summary = Record<string, unknown> & { window: unknown };
type Entry = {
  first?: ImportPreview;
  answered?: ImportPreview;
  commit?: ImportCommit;
  get?: ImportPreview;
  landing?: Summary | Envelope;
  initial_after?: Summary;
  assets?: unknown;
  ack_required?: Envelope;
  blocked_commit?: Envelope;
};
const Recorded = recorded as unknown as Record<string, Entry> & {
  created: Record<string, unknown>;
  empty_summary: Summary;
  value_kind: ImportPreview;
  instant: ImportPreview;
  streams_101: ImportPreview;
  reimport: { answered: ImportPreview; commit: ImportCommit };
  pages: { preview: ImportPreview; page: unknown };
  hostile_text: string;
  hostile: Entry & { file_first: ImportPreview };
} & Record<string, unknown>;

const FAKE_SECRET = 'fake-secret-123';
const EXAMPLE = Object.fromEntries(EXAMPLES('household').map((example) => [example.id, example]));
const KEY_PATTERN = /^[A-Za-z0-9_-]{22,128}$/;
/** Matches text with its line breaks, for CSV content. */
const AS_WRITTEN = (text: string) => text;

function respond(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status });
}

/** A failure envelope from the service, with a fake secret where a leak would show. */
function failure(status: number, code: string, details?: Envelope['error']['details'], recovery: object = { retryable: false }) {
  return respond(status, {
    error: { code, message: 'Permintaan belum dapat diselesaikan. Coba lagi nanti.', request_id: 'ref_1', recovery, details, debug_info: FAKE_SECRET },
  });
}

function replay(envelope: Envelope, status: number) {
  return respond(status, { ...envelope, error: { ...envelope.error, debug_info: FAKE_SECRET } });
}

type Call = { url: URL; init: RequestInit };
type Handler = (call: Call) => Response | Promise<Response>;
type Handlers = Partial<Record<'create' | 'site' | 'summary' | 'insights' | 'assets' | 'preview' | 'errors' | 'commit' | 'get', Handler>>;

const ROUTES: [keyof Handlers, RegExp][] = [
  ['create', /^\/api\/v1\/demo\/sessions$/],
  ['site', /^\/api\/v1\/sites\/[^/]+$/],
  ['summary', /^\/api\/v1\/sites\/[^/]+\/summary$/],
  ['insights', /^\/api\/v1\/sites\/[^/]+\/insights$/],
  ['assets', /^\/api\/v1\/sites\/[^/]+\/assets$/],
  ['preview', /^\/api\/v1\/sites\/[^/]+\/imports\/preview$/],
  ['errors', /^\/api\/v1\/imports\/[^/]+\/errors$/],
  ['commit', /^\/api\/v1\/imports\/[^/]+\/commit$/],
  ['get', /^\/api\/v1\/imports\/[^/]+$/],
];

function mapping(call: Call): Record<string, unknown> {
  return JSON.parse(String((call.init.body as FormData).get('mapping')));
}

/** A fake service answering from one recorded entry, in the order of the import flow. */
function mockImportApi(name: string, overrides: Handlers = {}) {
  const entry = Recorded[name] as Entry;
  let committed = false;
  const calls: Call[] = [];
  const defaults: Required<Handlers> = {
    create: () => respond(201, Recorded.created),
    site: ({ url }) => respond(200, { id: url.pathname.split('/').at(-1), kind: 'demo', name: 'Fixture', timezone: 'Asia/Jakarta' }),
    summary: ({ url }) => {
      const period = entry.commit?.period;
      if (committed && period && entry.landing && url.searchParams.get('start_date') === period.start_date && url.searchParams.get('end_date') === period.end_date) {
        return respond('error' in entry.landing ? 400 : 200, entry.landing);
      }
      return respond(200, committed && entry.initial_after ? entry.initial_after : Recorded.empty_summary);
    },
    insights: () => respond(200, { window: Recorded.empty_summary.window, observations: [], notices: [], learning_count: 0, comparable_count: 0 }),
    assets: () => respond(200, entry.assets ?? { items: [], next_cursor: null }),
    preview: (call) => respond(201, Object.keys(mapping(call)).length === 0 && entry.first ? entry.first : entry.answered),
    errors: () => respond(200, Recorded.pages.page),
    commit: () => {
      committed = true;
      return respond(200, entry.commit);
    },
    get: () => respond(200, entry.get ?? entry.answered),
  };
  const handlers = { ...defaults, ...overrides };
  const fetchMock = jest.spyOn(globalThis, 'fetch').mockImplementation(async (input, init = {}) => {
    const call = { url: new URL(String(input)), init };
    calls.push(call);
    const route = ROUTES.find(([, pattern]) => pattern.test(call.url.pathname));
    if (!route) {
      return respond(404, {});
    }
    const response = await handlers[route[0]](call);
    if (route[0] === 'commit' && overrides.commit && response.ok) {
      committed = true;
    }
    return response;
  });
  return {
    fetchMock,
    requests: (pattern: RegExp) => calls.filter((call) => pattern.test(call.url.pathname)),
    markCommitted: () => {
      committed = true;
    },
  };
}

const PREVIEW = /\/imports\/preview$/;
const COMMIT = /\/commit$/;
const GET_IMPORT = /^\/api\/v1\/imports\/[^/]+$/;
const IMPORT_CALLS = /\/imports/;

async function storeWorkspace(scenarioId = 'empty') {
  await seedConfirmedWorkspace({
      token: 'token-recorded',
      siteId: 'site-recorded',
      scenarioId,
      expiresAt: '2099-01-01T00:00:00Z',
      initialPeriod: { preset: 'last_7_days', start_date: '2026-10-19', end_date: '2026-10-25' },
    });
}

async function openImport(from = '/beranda', entryButton = 'Tambah data') {
  await renderRouter('./src/app', { initialUrl: from });
  await fireEvent.press(await screen.findByRole('button', { name: entryButton }));
  return screen.findByText('Langkah 1 dari 4 · Berkas');
}

async function useExample(label: string) {
  await fireEvent.press(screen.getByRole('button', { name: 'Contoh berkas yang dapat disalin' }));
  await fireEvent.press(within(screen.getByLabelText(label)).getByRole('button', { name: 'Gunakan contoh ini' }));
}

async function pasteText(text: string) {
  await fireEvent.changeText(screen.getByLabelText('Atau tempel isi CSV'), text);
}

async function press(name: string | RegExp) {
  await fireEvent.press(screen.getByRole('button', { name }));
}

/** Answers every question a recorded first preview asks, as a user would. */
async function answerQuestions(preview: ImportPreview) {
  for (const question of preview.questions) {
    if (question.kind === 'timezone') {
      await fireEvent.press(screen.getByRole('checkbox', { name: 'Waktu dalam berkas adalah waktu lokal Asia/Jakarta' }));
    } else if (question.kind === 'scope') {
      await fireEvent.press(screen.getByRole('radio', { name: 'Ya, terpisah satu sama lain dan dari perangkat lain' }));
    } else if (question.kind === 'power_meaning') {
      await fireEvent.press(screen.getByRole('radio', { name: 'Daya rata-rata selama interval' }));
    } else if (question.kind === 'interval_duration') {
      for (const label of screen.getAllByLabelText(/^Panjang interval untuk .* \(menit\)$/)) {
        await fireEvent.changeText(label, '60');
      }
    }
  }
}

/** Example by paste, through Berkas and Pemetaan, to Pratinjau. */
async function toPreview(label: string, preview: ImportPreview) {
  await useExample(label);
  await press('Periksa berkas');
  await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');
  await answerQuestions(preview);
  await press('Lihat pratinjau');
  await screen.findByText('Langkah 3 dari 4 · Pratinjau');
}

async function toResult() {
  await press('Konfirmasi impor');
  return screen.findByText('Langkah 4 dari 4 · Hasil');
}

/** Buttons drawn as the step's primary action. */
function primaryButtons() {
  return screen
    .getAllByRole('button')
    .filter((button) => StyleSheet.flatten(button.props.style)?.backgroundColor === tokens.component.buttonPrimaryBackground);
}

function nativeAsset(overrides: Partial<DocumentPicker.DocumentPickerAsset> = {}) {
  return { canceled: false as const, assets: [{ uri: 'file:///cache/contoh-valid.csv', name: 'contoh-valid.csv', size: 300, mimeType: 'text/csv', lastModified: 0, ...overrides }] };
}

const pick = DocumentPicker.getDocumentAsync as jest.Mock;
const realOS = Platform.OS;

beforeEach(() => {
  pick.mockReset();
  pick.mockResolvedValue({ canceled: true, assets: null });
});

afterEach(() => {
  Platform.OS = realOS;
  jest.useRealTimers();
  jest.restoreAllMocks();
  globalThis.sessionStorage?.clear?.();
});

describe('first import from a paste', () => {
  // The first render loads the entire Expo route tree under Jest coverage on a cold runner.
  it('goes from an empty Beranda through the four steps and lands on the imported day', async () => {
    const api = mockImportApi('valid');
    await storeWorkspace();
    await renderRouter('./src/app', { initialUrl: '/beranda' });
    await fireEvent.press(await screen.findByRole('button', { name: 'Tambah data' }));

    expect(await screen.findByRole('heading', { name: 'Impor data CSV' })).toBeOnTheScreen();
    expect(screen.getByText('Langkah 1 dari 4 · Berkas')).toBeOnTheScreen();
    expect(screen.getByRole('tab', { name: 'Beranda', selected: true })).toBeOnTheScreen();
    expect(screen.getByLabelText('Info: Syarat berkas')).toBeOnTheScreen();
    expect(
      screen.getByText(
        'CSV UTF-8 (BOM boleh), pemisah koma atau titik koma. Maksimal 10 MiB dan 150.000 baris data. Nama perangkat paling banyak 60 karakter. Energi angka 0 atau lebih; kosong tidak dianggap 0. Zona waktu dan panjang interval dikonfirmasi di langkah berikutnya.',
      ),
    ).toBeOnTheScreen();
    expect(api.requests(IMPORT_CALLS)).toEqual([]);
    expect(pick).not.toHaveBeenCalled();

    await fireEvent.press(screen.getByRole('button', { name: 'Contoh berkas yang dapat disalin' }));
    for (const example of EXAMPLES('unspecified')) {
      const block = screen.getByLabelText(example.label);
      expect(within(block).getByText(example.text, { normalizer: AS_WRITTEN }).props.selectable).toBe(true);
    }
    await fireEvent.press(within(screen.getByLabelText('Valid: dua perangkat, interval 1 jam')).getByRole('button', { name: 'Gunakan contoh ini' }));
    expect(screen.getByLabelText('Atau tempel isi CSV').props.value).toBe(EXAMPLE.valid.text);

    await press('Periksa berkas');
    expect(await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan')).toBeOnTheScreen();
    const [first] = api.requests(PREVIEW);
    expect((first.init.body as FormData).get('text')).toBe(EXAMPLE.valid.text);
    expect(mapping(first)).toEqual({});
    expect(screen.getByText('tempelan.csv · 12 baris data · kolom waktu timestamp · kolom nilai energi_wh (Wh)')).toBeOnTheScreen();
    // The first preview has no interval basis yet (`interval_basis: null`), so none is shown; the answered one says it.
    expect(screen.getByText('Lampu Teras: interval 1 jam')).toBeOnTheScreen();
    expect(screen.getByRole('checkbox', { name: 'Waktu dalam berkas adalah waktu lokal Asia/Jakarta' })).toBeOnTheScreen();
    expect(screen.getByRole('radio', { name: 'Belum tahu' })).toBeOnTheScreen();

    await answerQuestions(Recorded.valid.first!);
    await press('Lihat pratinjau');
    expect(await screen.findByText('Langkah 3 dari 4 · Pratinjau')).toBeOnTheScreen();
    expect(mapping(api.requests(PREVIEW)[1])).toEqual({ timezone_confirmed: true, scope: 'disjoint' });
    expect(screen.getByLabelText('Diterima: 12')).toBeOnTheScreen();
    expect(screen.getByText('12 baris akan disimpan.')).toBeOnTheScreen();
    expect(screen.getByText('Periode data: 20 Oktober 2026 · Asia/Jakarta')).toBeOnTheScreen();
    for (const assumption of Recorded.valid.answered!.assumptions) {
      expect(screen.getByText(assumption)).toBeOnTheScreen();
    }

    await toResult();
    const commits = api.requests(COMMIT);
    expect(commits).toHaveLength(1);
    expect((commits[0].init.headers as Record<string, string>)['Idempotency-Key']).toMatch(KEY_PATTERN);
    expect(commits[0].init.body).toBe('{"acknowledge_skipped":false}');
    expect(screen.getByLabelText('Berhasil: Impor tersimpan')).toBeOnTheScreen();
    expect(screen.getByLabelText('Baris disimpan: 12')).toBeOnTheScreen();
    expect(screen.getByLabelText('Perangkat baru: Lampu Teras, Dispenser')).toBeOnTheScreen();
    expect(screen.getByLabelText('Periode data: 20 Oktober 2026')).toBeOnTheScreen();
    expect(screen.getByText('Asal data: Data historis · Impor CSV')).toBeOnTheScreen();

    await press('Lihat periode data');
    expect(await screen.findByRole('heading', { name: 'Beranda' })).toBeOnTheScreen();
    expect(screen.getByRole('tab', { name: 'Beranda', selected: true })).toBeOnTheScreen();
    expect(await screen.findByText('Periode aktif: 20 Oktober 2026 · Asia/Jakarta')).toBeOnTheScreen();
    expect(screen.getAllByText('0,330 kWh').length).toBeGreaterThan(0);
    expect(screen.getByText('Data historis · Impor CSV')).toBeOnTheScreen();
    const summaries = api.requests(/\/summary$/);
    expect(summaries.at(-1)!.url.search).toBe('?start_date=2026-10-20&end_date=2026-10-20');
    expect(screen.getByRole('button', { name: 'Tambah data' })).toBeOnTheScreen();

    await fireEvent.press(screen.getByRole('tab', { name: 'Perangkat' }));
    await fireEvent.press(await screen.findByRole('button', { name: 'Tambah data' }));
    expect(await screen.findByText('Langkah 1 dari 4 · Berkas')).toBeOnTheScreen();
    expect(screen.getByLabelText('Atau tempel isi CSV').props.value).toBe('');
  }, 20_000);
});

describe('first import from a file', () => {
  it('uploads a native pick by its URI on every preview, and lands as a paste does', async () => {
    const api = mockImportApi('valid');
    await storeWorkspace();
    pick.mockResolvedValue(nativeAsset());
    await openImport();

    await press('Pilih berkas CSV');
    expect(await screen.findByText('Berkas: contoh-valid.csv')).toBeOnTheScreen();
    expect(pick).toHaveBeenCalledWith({ type: '*/*', multiple: false, copyToCacheDirectory: true, base64: false });
    expect(screen.queryByLabelText('Atau tempel isi CSV')).toBeNull();
    expect(screen.getByRole('button', { name: 'Ganti berkas' })).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Hapus berkas' })).toBeOnTheScreen();
    expect(screen.queryByText('Setelah peramban ditutup, berkas perlu dipilih ulang.')).toBeNull();

    const append = jest.spyOn(FormData.prototype, 'append');
    await press('Periksa berkas');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');
    expect(append).toHaveBeenCalledWith('file', { uri: 'file:///cache/contoh-valid.csv', name: 'contoh-valid.csv', type: 'text/csv' });
    expect(append.mock.calls.map(([name]) => name)).not.toContain('text');

    append.mockClear();
    await answerQuestions(Recorded.valid.first!);
    await press('Lihat pratinjau');
    await screen.findByText('Langkah 3 dari 4 · Pratinjau');
    expect(append).toHaveBeenCalledWith('file', { uri: 'file:///cache/contoh-valid.csv', name: 'contoh-valid.csv', type: 'text/csv' });
    expect(api.requests(PREVIEW)).toHaveLength(2);

    await toResult();
    await press('Lihat periode data');
    expect(await screen.findByText('Periode aktif: 20 Oktober 2026 · Asia/Jakarta')).toBeOnTheScreen();
  });

  it('changes nothing on a cancelled pick', async () => {
    const api = mockImportApi('valid');
    await storeWorkspace();
    await openImport();

    await press('Pilih berkas CSV');

    expect(screen.queryByText(/^Berkas: /)).toBeNull();
    expect(screen.getByLabelText('Atau tempel isi CSV')).toBeOnTheScreen();
    expect(api.requests(IMPORT_CALLS)).toEqual([]);
  });

  it('offers a safe next step when the system picker cannot open', async () => {
    const api = mockImportApi('valid');
    pick.mockRejectedValueOnce(new Error(FAKE_SECRET));
    await storeWorkspace();
    await openImport();

    await press('Pilih berkas CSV');

    expect(await screen.findByText('Pemilih berkas tidak dapat dibuka. Coba lagi atau tempel isi CSV.')).toBeOnTheScreen();
    expect(screen.getByLabelText('Atau tempel isi CSV')).toBeOnTheScreen();
    expect(api.requests(PREVIEW)).toEqual([]);
    expectNoSecret();
  });

  it('refuses a file over 10 MiB before uploading, and uploads one with no reported size', async () => {
    const api = mockImportApi('valid');
    await storeWorkspace();
    pick.mockResolvedValue(nativeAsset({ size: 10_485_761 }));
    await openImport();

    await press('Pilih berkas CSV');
    expect(await screen.findByRole('link', { name: 'Ukuran contoh-valid.csv melebihi batas 10 MiB.' })).toBeOnTheScreen();
    await press('Periksa berkas');
    expect(api.requests(IMPORT_CALLS)).toEqual([]);

    pick.mockResolvedValue(nativeAsset({ size: undefined }));
    await press('Pilih berkas CSV');
    expect(await screen.findByText('Berkas: contoh-valid.csv')).toBeOnTheScreen();
    await press('Periksa berkas');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');
    expect(api.requests(PREVIEW)).toHaveLength(1);
  });

  it('uploads the browser File on the web, and says it must be picked again after the browser closes', async () => {
    mockImportApi('valid');
    await storeWorkspace();
    const file = new File([EXAMPLE.valid.text], 'contoh-valid.csv', { type: 'text/csv' });
    pick.mockResolvedValue({ canceled: false, assets: [{ uri: 'blob:x', name: 'contoh-valid.csv', size: file.size, mimeType: 'text/csv', lastModified: 0, file }] });
    await openImport();
    // After rendering: the root layout touches `document` on the web, which Jest's environment does not have.
    Platform.OS = 'web';

    await press('Pilih berkas CSV');
    expect(await screen.findByText('Setelah peramban ditutup, berkas perlu dipilih ulang.')).toBeOnTheScreen();
    const append = jest.spyOn(FormData.prototype, 'append');
    await press('Periksa berkas');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');

    expect(append).toHaveBeenCalledWith('file', file);
  });

  it('asks before a file replaces a paste, and Batal keeps everything', async () => {
    const api = mockImportApi('valid');
    await storeWorkspace();
    await openImport();
    await pasteText(EXAMPLE.valid.text);

    await press('Pilih berkas CSV');
    expect(await screen.findByRole('heading', { name: 'Ganti isi impor?' })).toBeOnTheScreen();
    expect(screen.getByText('Isi sekarang, jawaban pemetaan, dan pratinjau akan diganti. Data yang sudah tersimpan tidak berubah.')).toBeOnTheScreen();
    await press('Batal');
    expect(screen.getByLabelText('Atau tempel isi CSV').props.value).toBe(EXAMPLE.valid.text);
    expect(pick).not.toHaveBeenCalled();
    expect(api.requests(IMPORT_CALLS)).toEqual([]);
  });

  it('replaces a paste and its answers with a file after Ganti', async () => {
    const api = mockImportApi('valid');
    await storeWorkspace();
    await openImport();
    await useExample('Valid: dua perangkat, interval 1 jam');
    await press('Periksa berkas');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');
    await answerQuestions(Recorded.valid.first!);
    await press('Ubah berkas');
    await screen.findByText('Langkah 1 dari 4 · Berkas');

    pick.mockResolvedValue(nativeAsset());
    await press('Pilih berkas CSV');
    await press('Ganti');
    expect(await screen.findByText('Berkas: contoh-valid.csv')).toBeOnTheScreen();
    await press('Periksa berkas');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');

    expect(mapping(api.requests(PREVIEW).at(-1)!)).toEqual({});
    expect(screen.getByRole('checkbox', { name: 'Waktu dalam berkas adalah waktu lokal Asia/Jakarta', checked: false })).toBeOnTheScreen();
  });

  it('asks for a file or a paste before anything is sent', async () => {
    const api = mockImportApi('valid');
    await storeWorkspace();
    await openImport();

    await press('Periksa berkas');

    expect(await screen.findByRole('link', { name: 'Pilih berkas CSV atau tempel isi CSV.' })).toBeOnTheScreen();
    expect(screen.getByLabelText('Periksa 1 hal berikut').props.role).toBe('alert');
    expect(api.requests(IMPORT_CALLS)).toEqual([]);
  });
});

describe('mapping questions', () => {
  beforeEach(() => storeWorkspace());

  it('has one primary action per step, named for the step', async () => {
    mockImportApi('valid');
    await openImport();
    expect(primaryButtons()).toHaveLength(1);
    expect(within(primaryButtons()[0]).getByText('Periksa berkas')).toBeOnTheScreen();

    await useExample('Valid: dua perangkat, interval 1 jam');
    await press('Periksa berkas');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');
    expect(primaryButtons()).toHaveLength(1);
    expect(within(primaryButtons()[0]).getByText('Lihat pratinjau')).toBeOnTheScreen();

    await answerQuestions(Recorded.valid.first!);
    await press('Lihat pratinjau');
    await screen.findByText('Langkah 3 dari 4 · Pratinjau');
    expect(primaryButtons()).toHaveLength(1);
    expect(within(primaryButtons()[0]).getByText('Konfirmasi impor')).toBeOnTheScreen();

    await toResult();
    expect(primaryButtons()).toHaveLength(1);
    expect(within(primaryButtons()[0]).getByText('Lihat periode data')).toBeOnTheScreen();
  });

  it('asks for the minutes of a one-row file, links to the field, and sends whole minutes', async () => {
    const api = mockImportApi('one');
    await openImport();
    await useExample('Satu baris (interval wajib diisi)');
    await press('Periksa berkas');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');
    await fireEvent.press(screen.getByRole('checkbox', { name: 'Waktu dalam berkas adalah waktu lokal Asia/Jakarta' }));
    await fireEvent.press(screen.getByRole('radio', { name: 'Ya, terpisah satu sama lain dan dari perangkat lain' }));

    await press('Lihat pratinjau');
    expect(await screen.findByText('Periksa 1 hal berikut')).toBeOnTheScreen();
    expect(screen.getByRole('link', { name: 'Isi panjang interval untuk Pemanas Air.' })).toBeOnTheScreen();
    expect(api.requests(PREVIEW)).toHaveLength(1);

    const minutes = screen.getByLabelText('Panjang interval untuk Pemanas Air (menit)');
    expect(minutes.props.keyboardType).toBe('number-pad');
    await fireEvent.changeText(minutes, '6a');
    expect(screen.getByText('Isi panjang interval dalam menit, dengan angka bulat.')).toBeOnTheScreen();

    await fireEvent.changeText(minutes, '60');
    expect(screen.queryByText('Isi panjang interval dalam menit, dengan angka bulat.')).toBeNull();
    await press('Lihat pratinjau');
    await screen.findByText('Langkah 3 dari 4 · Pratinjau');
    expect(mapping(api.requests(PREVIEW)[1]).interval_minutes).toEqual({ 'pemanas air': 60 });
  });

  it('requires the meaning of a power column and sends it', async () => {
    const api = mockImportApi('power');
    await openImport();
    await useExample('Daya rata-rata (power_w) dengan interval eksplisit');
    await press('Periksa berkas');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');
    await fireEvent.press(screen.getByRole('radio', { name: 'Ya, terpisah satu sama lain dan dari perangkat lain' }));

    await press('Lihat pratinjau');
    expect(await screen.findByRole('link', { name: 'Pilih arti kolom daya.' })).toBeOnTheScreen();

    await fireEvent.press(screen.getByRole('radio', { name: 'Daya rata-rata selama interval' }));
    await press('Lihat pratinjau');
    await screen.findByText('Langkah 3 dari 4 · Pratinjau');
    expect(mapping(api.requests(PREVIEW)[1]).power_meaning).toBe('average');
  });

  it('keeps the service question in the summary when it asks again', async () => {
    mockImportApi('power', { preview: (call) => respond(201, Object.keys(mapping(call)).length ? Recorded.instant : Recorded.power.first) });
    await openImport();
    await useExample('Daya rata-rata (power_w) dengan interval eksplisit');
    await press('Periksa berkas');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');
    await fireEvent.press(screen.getByRole('radio', { name: 'Daya sesaat (titik waktu)' }));
    await fireEvent.press(screen.getByRole('radio', { name: 'Ya, terpisah satu sama lain dan dari perangkat lain' }));

    await press('Lihat pratinjau');

    expect(await screen.findByRole('link', { name: Recorded.instant.questions[0].message })).toBeOnTheScreen();
    expect(screen.getByText('Langkah 2 dari 4 · Arti kolom dan pemetaan')).toBeOnTheScreen();
  });

  it('offers the three value kinds while the value column is open', async () => {
    mockImportApi('valid', { preview: () => respond(201, Recorded.value_kind) });
    await openImport();
    await pasteText('timestamp,perangkat,energi_wh,daya_w\n2026-10-20 06:00,Router,10,10\n');
    await press('Periksa berkas');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');

    expect(screen.getByText('tempelan.csv · 2 baris data · kolom waktu timestamp · kolom nilai belum dipilih')).toBeOnTheScreen();
    for (const label of ['Energi interval (Wh)', 'Daya rata-rata (W)', 'Penghitung kumulatif (Wh)']) {
      expect(screen.getByRole('radio', { name: label })).toBeOnTheScreen();
    }
  });

  it('shows service text verbatim: a counter reset and a quoted name', async () => {
    mockImportApi('counter');
    await openImport();
    await toPreview('Penghitung kumulatif dengan reset', Recorded.counter.first!);
    for (const assumption of Recorded.counter.answered!.assumptions) {
      expect(screen.getByText(assumption)).toBeOnTheScreen();
    }
    expect(screen.queryByText(/melanjutkan penghitung/)).toBeNull();
  });

  it('shows a name with a separator as written', async () => {
    mockImportApi('semi');
    await openImport();
    await useExample('Titik koma, koma desimal, nama berkutip');
    await press('Periksa berkas');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');

    expect(screen.getByText('Lampu; Gudang: interval 1 jam')).toBeOnTheScreen();
  });

  it('answers another source under the name the file writes, and the stored name', async () => {
    const sameName = Recorded.same_name as unknown as { first: ImportPreview; right: ImportPreview };
    const api = mockImportApi('valid', { preview: (call) => respond(201, mapping(call).asset_map ? sameName.right : sameName.first) });
    await openImport();
    await pasteText('timestamp,perangkat,energi_wh\n2026-10-20 06:00,kulkas,50\n');
    await press('Periksa berkas');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');

    expect(screen.getByText('Pemilihan sumber acuan belum tersedia di aplikasi ini.')).toBeOnTheScreen();
    await press('Lihat pratinjau');
    expect(await screen.findByRole('link', { name: 'Pilih cara mengimpor Kulkas.' })).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('radio', { name: 'Buat perangkat baru' }));
    await press('Lihat pratinjau');

    await screen.findByText('Langkah 3 dari 4 · Pratinjau');
    expect(mapping(api.requests(PREVIEW).at(-1)!).asset_map).toEqual({ kulkas: 'new', Kulkas: 'new' });
  });

  it('moves on with no request when nothing changed and nothing is asked', async () => {
    const api = mockImportApi('valid');
    await openImport();
    await toPreview('Valid: dua perangkat, interval 1 jam', Recorded.valid.first!);
    await press('Ubah pemetaan');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');

    await press('Lihat pratinjau');

    expect(await screen.findByText('Langkah 3 dari 4 · Pratinjau')).toBeOnTheScreen();
    expect(api.requests(PREVIEW)).toHaveLength(2);
  });
});

describe('result and landing', () => {
  beforeEach(() => storeWorkspace());

  /** Pastes text answered by a recorded entry, and confirms it. `before` counts summary reads before the commit. */
  async function importText(name: string, text: string) {
    const api = mockImportApi(name);
    await openImport();
    await pasteText(text);
    await press('Periksa berkas');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');
    const first = (Recorded[name] as Entry).first;
    if (first) {
      await answerQuestions(first);
    }
    await press('Lihat pratinjau');
    await screen.findByText('Langkah 3 dari 4 · Pratinjau');
    const before = api.requests(/\/summary$/).length;
    await toResult();
    return { ...api, before };
  }

  it('says how many rows straddle the clock, and still lands on the imported days', async () => {
    const { requests } = await importText('straddle', 'timestamp,perangkat,energi_wh\n2026-10-25 22:00,Router,10\n');

    expect(screen.getByText('2 dari 4 baris tersimpan berada setelah waktu ruang kerja ini, sehingga belum dihitung pada ringkasan.')).toBeOnTheScreen();
    await press('Lihat periode data');
    // The landing window ends after the workspace clock, so Beranda marks it as running.
    expect(await screen.findByText(/^Periode aktif: 25–26 Oktober 2026 · sampai 00\.00 \(berjalan\) · Asia\/Jakarta$/)).toBeOnTheScreen();
    expect(requests(/\/summary$/).at(-1)!.url.search).toBe('?start_date=2026-10-25&end_date=2026-10-26');
  });

  it('never claims rows after the clock are shown, and goes back to the same period', async () => {
    const { requests, before } = await importText('after_clock', 'timestamp,perangkat,energi_wh\n2026-11-01 06:00,Router,10\n');

    expect(
      screen.getByText('Semua 2 baris tersimpan, tetapi berada setelah waktu ruang kerja ini, sehingga belum tampil di Beranda atau Perangkat.'),
    ).toBeOnTheScreen();
    expect(screen.queryByRole('button', { name: 'Lihat periode data' })).toBeNull();
    expect(screen.queryByText(/berhasil ditampilkan|sudah tampil|terlihat di Beranda/)).toBeNull();
    // Every query refetches after a commit, though the period did not change (027 D23).
    await waitFor(() => expect(requests(/\/summary$/).length).toBe(before + 1));

    await press('Kembali ke Beranda');
    expect(await screen.findByText('Periode aktif: 19–25 Oktober 2026 · Asia/Jakarta')).toBeOnTheScreen();
  });

  it('lands on the last 366 days of a long file, and says so', async () => {
    const { requests } = await importText('long', 'timestamp,perangkat,energi_wh\n2025-01-01 06:00,Router,10\n');

    expect(screen.getByText('Rentang data lebih dari 366 hari, sehingga Beranda menampilkan 366 hari terakhirnya.')).toBeOnTheScreen();
    await press('Lihat periode data');
    await screen.findByRole('heading', { name: 'Beranda' });
    await waitFor(() => expect(requests(/\/summary$/).at(-1)!.url.search).toBe('?start_date=2025-10-20&end_date=2026-10-20'));
  });

  it('says no row is new on a reimport', async () => {
    mockImportApi('valid', {
      preview: (call) => respond(201, Object.keys(mapping(call)).length ? Recorded.reimport.answered : Recorded.valid.first),
      commit: () => respond(200, Recorded.reimport.commit),
    });
    await openImport();
    await toPreview('Valid: dua perangkat, interval 1 jam', Recorded.valid.first!);
    await toResult();

    expect(screen.getByText('Tidak ada baris baru. 12 baris sama dengan data tersimpan dan dihitung sekali.')).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Kembali ke Beranda' })).toBeOnTheScreen();
    expect(screen.queryByRole('button', { name: 'Lihat periode data' })).toBeNull();
  });

  it('says a scope answer holds only within the file', async () => {
    await importText('valid', EXAMPLE.valid.text);

    expect(
      screen.getByText(
        'Jawaban cakupan hanya berlaku antar perangkat dalam berkas ini. Bila ruang kerja sudah berisi perangkat lain, total gabungan menunggu konfirmasi cakupan; nilai per perangkat tetap tampil.',
      ),
    ).toBeOnTheScreen();
    expect(screen.queryByText(/Anda memilih “Belum tahu”/)).toBeNull();
  });
});

describe('entry points', () => {
  it('opens from empty and populated Perangkat inside the tab', async () => {
    const api = mockImportApi('valid');
    await storeWorkspace();
    await openImport('/perangkat');
    expect(screen.getByRole('tab', { name: 'Perangkat', selected: true })).toBeOnTheScreen();
    expect(screen.queryByText('Segera hadir')).toBeNull();

    api.markCommitted();
    await screen.unmount();
    await openImport('/perangkat');
    expect(screen.getByRole('tab', { name: 'Perangkat', selected: true })).toBeOnTheScreen();
  });

  it('opens from Saran with no data', async () => {
    mockImportApi('valid');
    await storeWorkspace();
    await openImport('/saran', 'Tentang impor data');

    expect(screen.getByRole('tab', { name: 'Saran', selected: true })).toBeOnTheScreen();
    expect(screen.queryByText('Segera hadir')).toBeNull();
  });

  it('lands on Beranda from the Perangkat tab, and Perangkat is its own list again', async () => {
    mockImportApi('valid');
    await storeWorkspace();
    await openImport('/perangkat');
    await toPreview('Valid: dua perangkat, interval 1 jam', Recorded.valid.first!);
    await toResult();

    await press('Lihat periode data');
    expect(await screen.findByRole('tab', { name: 'Beranda', selected: true })).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('tab', { name: 'Perangkat' }));

    expect(await screen.findByRole('heading', { name: 'Perangkat' })).toBeOnTheScreen();
    expect(screen.queryByText('Langkah 4 dari 4 · Hasil')).toBeNull();
  });

  it('needs a workspace, sends nothing without one, and keeps a typed paste through Mulai ruang kerja', async () => {
    const api = mockImportApi('valid');
    await openImport();

    expect(screen.getByText('Belum ada ruang kerja')).toBeOnTheScreen();
    expect(screen.getByText('Impor memerlukan ruang kerja. Mulai ruang kerja sementara untuk melanjutkan; isi yang sudah ditempel tetap ada.')).toBeOnTheScreen();
    await pasteText(EXAMPLE.valid.text);
    expect(api.requests(IMPORT_CALLS)).toEqual([]);

    await press('Mulai ruang kerja');
    await waitFor(() => expect(screen.queryByText('Belum ada ruang kerja')).toBeNull());
    expect(JSON.parse(String(api.requests(/\/demo\/sessions$/)[0].init.body))).toEqual({ scenario_id: 'empty' });
    expect(screen.getByLabelText('Atau tempel isi CSV').props.value).toBe(EXAMPLE.valid.text);
    expect(api.requests(IMPORT_CALLS)).toEqual([]);
  });
});

/** Labels of the elements focus was moved to, in order. Host refs in Jest carry their props. */
function focusedLabels(send: jest.SpyInstance): string[] {
  return send.mock.calls.map(([node]) => {
    const props = (node as { props?: Record<string, unknown> } | null)?.props ?? {};
    return String(props['aria-label'] ?? props.accessibilityLabel ?? (typeof props.children === 'string' ? props.children : props.role) ?? '');
  });
}

function spyFocus() {
  const send = jest.spyOn(AccessibilityInfo, 'sendAccessibilityEvent').mockImplementation(() => undefined);
  send.mockClear();
  return send;
}

function expectNoSecret() {
  expect(JSON.stringify(screen.toJSON())).not.toContain(FAKE_SECRET);
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

const PENDING = /^Menyimpan impor…$/;
const commitKey = (call: Call) => (call.init.headers as Record<string, string>)['Idempotency-Key'];

describe('row errors and acknowledgment', () => {
  beforeEach(() => storeWorkspace());

  it('lists the rows with their file lines, and the summary takes focus on arrival', async () => {
    const send = spyFocus();
    mockImportApi('two');
    await openImport();
    await toPreview('2 dari 10 baris tidak valid', Recorded.two.first!);

    const rows = ['Baris data 4, energi_wh: "dua" bukan angka. (baris berkas 5)', 'Baris data 7, energi_wh: gunakan angka 0 atau lebih. (baris berkas 8)'];
    for (const row of rows) {
      expect(screen.getByRole('link', { name: row })).toBeOnTheScreen();
      expect(screen.getAllByText(row)).toHaveLength(2);
    }
    expect(screen.getAllByText('Nomor baris data tidak menghitung header dan baris kosong. Baris berkas adalah nomor baris pada berkas, termasuk header.').length).toBe(2);
    expect(screen.getByLabelText('Baris bermasalah dalam berkas').props.role).toBe('alert');
    await waitFor(() => expect(focusedLabels(send)).toContain('Baris bermasalah dalam berkas'));

    await fireEvent.press(screen.getByRole('link', { name: rows[1] }));
    expect(focusedLabels(send).at(-1)).toBe('listitem');
  });

  it('asks for the acknowledgment before sending anything, then sends it', async () => {
    const send = spyFocus();
    const api = mockImportApi('two');
    await openImport();
    await toPreview('2 dari 10 baris tidak valid', Recorded.two.first!);

    await press('Konfirmasi impor');
    const ack = 'Centang konfirmasi bahwa 2 baris tidak valid tidak akan diimpor.';
    expect(await screen.findByLabelText('Periksa 1 hal berikut')).toBeOnTheScreen();
    expect(screen.getByLabelText('Periksa 1 hal berikut').props.role).toBe('alert');
    expect(screen.getAllByText(ack)).toHaveLength(2);
    await waitFor(() => expect(focusedLabels(send).at(-1)).toBe('Periksa 1 hal berikut'));
    await fireEvent.press(screen.getByRole('link', { name: ack }));
    expect(focusedLabels(send).at(-1)).toBe('Saya setuju 2 baris tidak valid dilewati dan tidak diimpor.');
    expect(api.requests(COMMIT)).toEqual([]);

    await fireEvent.press(screen.getByRole('checkbox', { name: 'Saya setuju 2 baris tidak valid dilewati dan tidak diimpor.' }));
    expect(screen.queryByText(ack)).toBeNull();
    await toResult();
    expect(api.requests(COMMIT)[0].init.body).toBe('{"acknowledge_skipped":true}');
  });

  it('shows the service refusal of a missing acknowledgment the same way, with its details', async () => {
    mockImportApi('two', { commit: () => replay(Recorded.two.ack_required!, 409) });
    await openImport();
    await toPreview('2 dari 10 baris tidak valid', Recorded.two.first!);
    await fireEvent.press(screen.getByRole('checkbox', { name: 'Saya setuju 2 baris tidak valid dilewati dan tidak diimpor.' }));

    await press('Konfirmasi impor');

    expect(await screen.findByRole('link', { name: 'Centang konfirmasi bahwa 2 baris tidak valid tidak akan diimpor.' })).toBeOnTheScreen();
    expect(screen.getByText('Impor belum disimpan')).toBeOnTheScreen();
    expect(screen.getByText(Recorded.two.ack_required!.error.message)).toBeOnTheScreen();
    expect(screen.getByText('2 baris tidak valid akan dilewati.')).toBeOnTheScreen();
    expect(screen.getByText(`ID referensi: ${Recorded.two.ack_required!.error.request_id}.`)).toBeOnTheScreen();
    expectNoSecret();
  });

  it('locks the acknowledgment while the commit is pending', async () => {
    const commit = deferred<Response>();
    mockImportApi('two', { commit: () => commit.promise });
    await openImport();
    await toPreview('2 dari 10 baris tidak valid', Recorded.two.first!);
    const box = () => screen.getByRole('checkbox', { name: 'Saya setuju 2 baris tidak valid dilewati dan tidak diimpor.' });
    await fireEvent.press(box());

    await press('Konfirmasi impor');
    expect(await screen.findByRole('button', { name: PENDING })).toBeOnTheScreen();
    await fireEvent.press(box());

    expect(box()).toBeDisabled();
    expect(box()).toBeChecked();
    await act(async () => commit.resolve(respond(200, Recorded.two.commit)));
    await screen.findByText('Langkah 4 dari 4 · Hasil');
  });
});

describe('blocked previews', () => {
  beforeEach(() => storeWorkspace());

  it('shows why a preview is blocked, and sends nothing', async () => {
    const api = mockImportApi('three');
    await openImport();
    await toPreview('3 dari 10 baris tidak valid (diblokir)', Recorded.three.first!);

    expect(screen.getByText('Impor diblokir')).toBeOnTheScreen();
    expect(screen.getByText('Impor diblokir: 3 dari 10 baris tidak valid.')).toBeOnTheScreen();
    expect(screen.getByText('Impor diblokir. Selesaikan alasan di atas lalu periksa lagi.')).toBeOnTheScreen();
    await press('Konfirmasi impor');
    expect(api.requests(COMMIT)).toEqual([]);
  });

  it('shows a conflict reason verbatim with both conflicting rows', async () => {
    mockImportApi('conflict');
    await openImport();
    await toPreview('Nilai berbeda pada interval yang sama', Recorded.conflict.first!);

    expect(screen.getByText(Recorded.conflict.answered!.block_reasons[0])).toBeOnTheScreen();
    expect(screen.getAllByText('Baris data 1, energi_wh: nilai berbeda untuk sumber dan interval yang sama. (baris berkas 2)').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Baris data 3, energi_wh: nilai berbeda untuk sumber dan interval yang sama. (baris berkas 4)').length).toBeGreaterThan(0);
  });

  it('shows the 100-asset reason verbatim', async () => {
    mockImportApi('valid', { preview: (call) => respond(201, Object.keys(mapping(call)).length ? Recorded.streams_101 : Recorded.valid.first) });
    await openImport();
    await toPreview('Valid: dua perangkat, interval 1 jam', Recorded.valid.first!);

    expect(screen.getByText(Recorded.streams_101.block_reasons[0])).toBeOnTheScreen();
  });

  it('reads the preview again when the service refuses a commit as blocked', async () => {
    const api = mockImportApi('valid', { commit: () => replay(Recorded.three.blocked_commit!, 409), get: () => respond(200, { ...Recorded.three.answered, id: Recorded.valid.answered!.id }) });
    await openImport();
    await toPreview('Valid: dua perangkat, interval 1 jam', Recorded.valid.first!);

    await press('Konfirmasi impor');

    expect(await screen.findByText('Impor diblokir: 3 dari 10 baris tidak valid.')).toBeOnTheScreen();
    expect(api.requests(GET_IMPORT)).toHaveLength(1);
    expect(screen.getByText(Recorded.three.blocked_commit!.error.message)).toBeOnTheScreen();
    expect(screen.getByText(`ID referensi: ${Recorded.three.blocked_commit!.error.request_id}.`)).toBeOnTheScreen();
    expectNoSecret();
  });
});

describe('unknown commit result', () => {
  beforeEach(() => storeWorkspace());

  async function toUnknown(overrides: Handlers = {}, commit: Handler = () => Promise.reject(new TypeError('Network request failed'))) {
    const api = mockImportApi('valid', { commit, ...overrides });
    await openImport();
    await toPreview('Valid: dua perangkat, interval 1 jam', Recorded.valid.first!);
    await press('Konfirmasi impor');
    expect(await screen.findByText('Status impor belum diketahui')).toBeOnTheScreen();
    return api;
  }

  it('offers only a status check, and never resends by itself', async () => {
    // Fake timers from the start, advancing with real time, so 70 s can pass without a mid-test switch.
    jest.useFakeTimers({ advanceTimers: true });
    const api = await toUnknown();

    expect(screen.getByText('Jawaban layanan tidak diterima. Periksa status sebelum mencoba lagi; impor tidak akan tersimpan dua kali.')).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Periksa status' })).toBeOnTheScreen();
    expect(screen.queryByRole('button', { name: 'Konfirmasi impor' })).toBeNull();
    await act(async () => {
      await jest.advanceTimersByTimeAsync(70_000);
    });
    expect(api.requests(COMMIT)).toHaveLength(1);
  });

  it('keeps the original commit intent when the user goes back before checking', async () => {
    const api = await toUnknown();

    await press('Kembali');
    expect(await screen.findByText('Ada impor yang belum selesai.')).toBeOnTheScreen();
    expect(screen.queryByRole('button', { name: 'Lihat pratinjau' })).toBeNull();
    await press('Buka pratinjau');
    await press('Periksa status');

    expect(await screen.findByLabelText('Berhasil: Impor sudah dikonfirmasi sebelumnya')).toBeOnTheScreen();
    expect(api.requests(PREVIEW)).toHaveLength(2);
    expect(api.requests(COMMIT)).toHaveLength(1);
  });

  it('finds a committed import by its status, without a second commit', async () => {
    const api = await toUnknown();

    await press('Periksa status');

    expect(await screen.findByLabelText('Berhasil: Impor sudah dikonfirmasi sebelumnya')).toBeOnTheScreen();
    expect(screen.getByText('Permintaan yang sama ditemukan; data tidak diimpor dua kali.')).toBeOnTheScreen();
    expect(api.requests(GET_IMPORT)).toHaveLength(1);
    expect(api.requests(COMMIT)).toHaveLength(1);
  });

  it('resends the same key and body when the import is not committed yet', async () => {
    let attempts = 0;
    const api = await toUnknown({ get: () => respond(200, Recorded.valid.answered) }, () => {
      attempts += 1;
      return attempts === 1 ? Promise.reject(new TypeError('Network request failed')) : respond(200, Recorded.valid.commit);
    });

    await press('Periksa status');
    expect(await screen.findByText('Impor belum tercatat')).toBeOnTheScreen();
    expect(screen.getByText('Saat diperiksa, impor ini belum tersimpan. Data tersimpan sebelumnya tidak berubah. Kirim lagi memakai permintaan yang sama.')).toBeOnTheScreen();
    await press('Kirim lagi');

    await screen.findByText('Langkah 4 dari 4 · Hasil');
    const [first, second] = api.requests(COMMIT);
    expect(commitKey(second)).toBe(commitKey(first));
    expect(second.init.body).toBe(first.init.body);
  });

  it.each([
    ['expired', () => respond(200, { ...Recorded.valid.answered, status: 'expired' })],
    ['gone', () => failure(404, 'NOT_FOUND')],
  ])('offers a new preview with the same source and answers when the import is %s', async (_name, get) => {
    const api = await toUnknown({ get });

    await press('Periksa status');
    expect(await screen.findByText('Pratinjau sudah tidak tersedia')).toBeOnTheScreen();
    await press('Buat pratinjau baru');

    await waitFor(() => expect(api.requests(PREVIEW)).toHaveLength(3));
    const [, answered, again] = api.requests(PREVIEW);
    expect((again.init.body as FormData).get('text')).toBe(EXAMPLE.valid.text);
    expect(mapping(again)).toEqual(mapping(answered));
  });

  it('stays unknown when the check fails, with its message and reference', async () => {
    await toUnknown({ get: () => failure(500, 'INTERNAL_ERROR') });

    await press('Periksa status');

    expect(await screen.findByText('Status impor belum dapat diperiksa')).toBeOnTheScreen();
    expect(screen.getByText('Status impor belum diketahui')).toBeOnTheScreen();
    expect(screen.getByText('Permintaan belum dapat diselesaikan. Coba lagi nanti.')).toBeOnTheScreen();
    expect(screen.getByText('ID referensi: ref_1.')).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Periksa status' })).toBeOnTheScreen();
    expectNoSecret();
  });

  it.each([
    ['a server failure', () => failure(500, 'INTERNAL_ERROR')],
    ['an unexpected body', () => respond(200, { secret: 'x' })],
  ])('treats %s as unknown', async (_name, commit) => {
    await toUnknown({}, commit);

    expect(screen.queryByRole('button', { name: 'Konfirmasi impor' })).toBeNull();
    expectNoSecret();
  });

  it('sends one request for two presses while pending', async () => {
    const commit = deferred<Response>();
    const api = mockImportApi('valid', { commit: () => commit.promise });
    await openImport();
    await toPreview('Valid: dua perangkat, interval 1 jam', Recorded.valid.first!);

    await press('Konfirmasi impor');
    await press(PENDING);
    expect(screen.getByText('Berkas besar dapat memerlukan waktu hingga satu menit.')).toBeOnTheScreen();

    expect(api.requests(COMMIT)).toHaveLength(1);
    await act(async () => commit.resolve(respond(200, Recorded.valid.commit)));
    await screen.findByText('Langkah 4 dari 4 · Hasil');
  });

  it('keeps a pending commit when the user leaves, and offers its result once it settles', async () => {
    const commit = deferred<Response>();
    mockImportApi('valid', { commit: () => commit.promise });
    await openImport();
    await toPreview('Valid: dua perangkat, interval 1 jam', Recorded.valid.first!);
    await press('Konfirmasi impor');

    await fireEvent.press(screen.getByRole('tab', { name: 'Perangkat' }));
    await fireEvent.press(await screen.findByRole('button', { name: 'Tambah data' }));
    expect(await screen.findByText('Ada impor yang belum selesai.')).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Buka pratinjau' })).toBeOnTheScreen();

    await act(async () => commit.resolve(respond(200, Recorded.valid.commit)));
    expect(await screen.findByText('Impor sebelumnya sudah tersimpan.')).toBeOnTheScreen();
    expect(screen.getByText('Langkah 1 dari 4 · Berkas')).toBeOnTheScreen();
    await press('Lihat hasil');
    expect(await screen.findByText('Langkah 4 dari 4 · Hasil')).toBeOnTheScreen();
    expect(screen.getByRole('tab', { name: 'Perangkat', selected: true })).toBeOnTheScreen();
  });
});

describe('refusals', () => {
  beforeEach(() => storeWorkspace());

  async function checkPaste(name: string, preview: Handler, text = EXAMPLE.valid.text) {
    const api = mockImportApi(name, { preview });
    await openImport();
    await pasteText(text);
    await press('Periksa berkas');
    return api;
  }

  function expectStatus(label: string, envelope: Envelope) {
    expect(screen.getByText(label)).toBeOnTheScreen();
    expect(screen.getByText(envelope.error.message)).toBeOnTheScreen();
    expect(screen.getByText(`ID referensi: ${envelope.error.request_id}.`)).toBeOnTheScreen();
    expectNoSecret();
  }

  it('lists every problem of an unreadable file, linked to the paste, with no retry', async () => {
    const send = spyFocus();
    const envelope = Recorded.invalid_header as unknown as Envelope;
    await checkPaste('valid', () => replay(envelope, 400), 'a,b,c\n1,2,3\n');

    expect(await screen.findByText('Berkas belum dapat diperiksa')).toBeOnTheScreen();
    expectStatus('Berkas belum dapat diperiksa', envelope);
    for (const detail of envelope.error.details!) {
      expect(screen.getByRole('link', { name: detail.msg })).toBeOnTheScreen();
    }
    expect(screen.queryByRole('button', { name: 'Coba lagi' })).toBeNull();
    await fireEvent.press(screen.getByRole('link', { name: envelope.error.details![0].msg }));
    expect(focusedLabels(send).at(-1)).toBe('Atau tempel isi CSV');
    expect(screen.getByLabelText('Atau tempel isi CSV').props.value).toBe('a,b,c\n1,2,3\n');
  });

  it('shows the row limit of a file that is too large', async () => {
    const envelope = Recorded.too_many_rows as unknown as Envelope;
    await checkPaste('valid', () => replay(envelope, 413));

    expect(await screen.findByRole('link', { name: '150001 baris data melebihi batas 150.000 baris.' })).toBeOnTheScreen();
    expectStatus('Berkas belum dapat diperiksa', envelope);
  });

  it('links a refused minutes answer to its field', async () => {
    const envelope = Recorded.bad_minutes as unknown as Envelope;
    const send = spyFocus();
    mockImportApi('one', { preview: (call) => (Object.keys(mapping(call)).length ? replay(envelope, 422) : respond(201, Recorded.one.first)) });
    await openImport();
    await useExample('Satu baris (interval wajib diisi)');
    await press('Periksa berkas');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');
    await answerQuestions(Recorded.one.first!);
    await press('Lihat pratinjau');

    await fireEvent.press(await screen.findByRole('link', { name: envelope.error.details![0].msg }));
    expect(focusedLabels(send).at(-1)).toBe('Panjang interval untuk Pemanas Air (menit)');
    expectStatus('Berkas belum dapat diperiksa', envelope);
  });

  it('clears a chosen asset that is gone and keeps every other answer', async () => {
    const envelope = Recorded.asset_gone as unknown as Envelope;
    const second = Recorded.same_name as unknown as { second: ImportPreview };
    const asking = { ...second.second, questions: [...Recorded.valid.first!.questions, ...second.second.questions] };
    mockImportApi('valid', { preview: (call) => (Object.keys(mapping(call)).length ? replay(envelope, 404) : respond(201, asking)) });
    await openImport();
    await pasteText('timestamp,perangkat,energi_wh\n2026-10-21 06:00,Kulkas,50\n');
    await press('Periksa berkas');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');
    await answerQuestions(Recorded.valid.first!);
    await fireEvent.press(screen.getByRole('radio', { name: 'Buat perangkat baru' }));

    await press('Lihat pratinjau');

    expect(await screen.findByText('Perangkat yang dipilih tidak ditemukan lagi. Pilih ulang perangkatnya.')).toBeOnTheScreen();
    expectStatus('Perangkat yang dipilih tidak ditemukan lagi. Pilih ulang perangkatnya.', envelope);
    expect(screen.getByRole('radio', { name: 'Buat perangkat baru', checked: false })).toBeOnTheScreen();
    expect(screen.getByRole('checkbox', { name: 'Waktu dalam berkas adalah waktu lokal Asia/Jakarta', checked: true })).toBeOnTheScreen();
    expect(screen.getByRole('radio', { name: 'Ya, terpisah satu sama lain dan dari perangkat lain', checked: true })).toBeOnTheScreen();
  });

  it('shows the message and reference of a request the client should never send', async () => {
    await checkPaste('valid', () => failure(400, 'BAD_REQUEST'));

    expect(await screen.findByText('Permintaan belum dapat diselesaikan. Coba lagi nanti.')).toBeOnTheScreen();
    expect(screen.getByText('ID referensi: ref_1.')).toBeOnTheScreen();
    expectNoSecret();
  });

  it('says a lost preview saved nothing, and Coba lagi sends it again', async () => {
    let attempts = 0;
    const api = await checkPaste('valid', () => {
      attempts += 1;
      return attempts === 1 ? Promise.reject(new TypeError('Network request failed')) : respond(201, Recorded.valid.first);
    });

    expect(await screen.findByText('Berkas belum selesai diperiksa')).toBeOnTheScreen();
    expect(screen.getByText('Data yang tersimpan tidak berubah.')).toBeOnTheScreen();
    await press('Coba lagi');

    expect(await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan')).toBeOnTheScreen();
    expect(api.requests(PREVIEW)).toHaveLength(2);
  });

  it('offers no retry after a server failure the service says not to retry', async () => {
    await checkPaste('valid', () => failure(500, 'INTERNAL_ERROR'));

    expect(await screen.findByText('Berkas belum selesai diperiksa')).toBeOnTheScreen();
    expect(screen.getByText('ID referensi: ref_1.')).toBeOnTheScreen();
    expect(screen.queryByRole('button', { name: 'Coba lagi' })).toBeNull();
    expectNoSecret();
  });

  it('ends the workspace on an expired session and hides its adopted paste', async () => {
    await checkPaste('valid', () => failure(401, 'SESSION_EXPIRED'));

    expect(await screen.findByText('Belum ada ruang kerja')).toBeOnTheScreen();
    expect(screen.getByText('Sesi demo sudah berakhir')).toBeOnTheScreen();
    expect(screen.getByLabelText('Atau tempel isi CSV').props.value).toBe('');
    expectNoSecret();
  });

  async function refuseCommit(commit: Handler) {
    const api = mockImportApi('valid', { commit });
    await openImport();
    await toPreview('Valid: dua perangkat, interval 1 jam', Recorded.valid.first!);
    await press('Konfirmasi impor');
    return api;
  }

  it('says a stale preview is no longer valid, and a new preview gets a new key', async () => {
    const envelope = Recorded.stale as unknown as Envelope;
    let attempts = 0;
    const api = await refuseCommit(() => {
      attempts += 1;
      return attempts === 1 ? replay(envelope, 409) : respond(200, Recorded.valid.commit);
    });

    expect(await screen.findByText('Pratinjau sudah tidak berlaku')).toBeOnTheScreen();
    expectStatus('Pratinjau sudah tidak berlaku', envelope);
    expect(screen.getByText('Data pada ruang kerja ini berubah setelah pratinjau dibuat.')).toBeOnTheScreen();
    await press('Buat pratinjau baru');
    await waitFor(() => expect(api.requests(PREVIEW)).toHaveLength(3));
    await toResult();

    const [first, second] = api.requests(COMMIT);
    expect(commitKey(second)).not.toBe(commitKey(first));
  });

  it('keeps the preview after a key conflict, and the next confirmation has a new key', async () => {
    const envelope = Recorded.key_conflict as unknown as Envelope;
    let attempts = 0;
    const api = await refuseCommit(() => {
      attempts += 1;
      return attempts === 1 ? replay(envelope, 409) : respond(200, Recorded.valid.commit);
    });

    expect(await screen.findByText('Impor belum disimpan')).toBeOnTheScreen();
    expectStatus('Impor belum disimpan', envelope);
    expect(screen.getByText('Langkah 3 dari 4 · Pratinjau')).toBeOnTheScreen();
    await toResult();
    const [first, second] = api.requests(COMMIT);
    expect(commitKey(second)).not.toBe(commitKey(first));
  });

  it('says a preview is gone and offers a new one', async () => {
    const envelope = Recorded.commit_not_found as unknown as Envelope;
    await refuseCommit(() => replay(envelope, 404));

    expect(await screen.findByText('Pratinjau sudah tidak tersedia')).toBeOnTheScreen();
    expectStatus('Pratinjau sudah tidak tersedia', envelope);
    expect(screen.getByRole('button', { name: 'Buat pratinjau baru' })).toBeOnTheScreen();
  });

  it('shows the details of a refused key, and drops it', async () => {
    const envelope = Recorded.bad_key as unknown as Envelope;
    let attempts = 0;
    const api = await refuseCommit(() => {
      attempts += 1;
      return attempts === 1 ? replay(envelope, 422) : respond(200, Recorded.valid.commit);
    });

    expect(await screen.findByText('Impor belum disimpan')).toBeOnTheScreen();
    expectStatus('Impor belum disimpan', envelope);
    expect(screen.getByText(envelope.error.details![0].msg)).toBeOnTheScreen();
    await toResult();
    const [first, second] = api.requests(COMMIT);
    expect(commitKey(second)).not.toBe(commitKey(first));
  });

  it('ends the workspace when a commit finds the session expired', async () => {
    await refuseCommit(() => failure(401, 'SESSION_EXPIRED'));

    expect(await screen.findByText('Belum ada ruang kerja')).toBeOnTheScreen();
    expect(screen.getByLabelText('Atau tempel isi CSV').props.value).toBe('');
    expectNoSecret();
  });
});

describe('back and replace', () => {
  beforeEach(() => storeWorkspace());

  it('keeps every answer and the text one step back at a time', async () => {
    mockImportApi('valid');
    await openImport();
    await toPreview('Valid: dua perangkat, interval 1 jam', Recorded.valid.first!);

    await press('Kembali');
    expect(await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan')).toBeOnTheScreen();
    expect(screen.getByRole('checkbox', { name: 'Waktu dalam berkas adalah waktu lokal Asia/Jakarta', checked: true })).toBeOnTheScreen();
    expect(screen.getByRole('radio', { name: 'Ya, terpisah satu sama lain dan dari perangkat lain', checked: true })).toBeOnTheScreen();

    await act(() => router.back());
    expect(await screen.findByText('Langkah 1 dari 4 · Berkas')).toBeOnTheScreen();
    expect(screen.getByLabelText('Atau tempel isi CSV').props.value).toBe(EXAMPLE.valid.text);
  });

  it('keeps the draft when the import is closed, and sends the same answers again', async () => {
    const api = mockImportApi('valid');
    await openImport();
    await toPreview('Valid: dua perangkat, interval 1 jam', Recorded.valid.first!);
    await press('Kembali');
    await press('Kembali');

    await press('Tutup impor (draf tetap tersimpan)');
    expect(await screen.findByRole('heading', { name: 'Beranda' })).toBeOnTheScreen();
    await press('Tambah data');
    expect(await screen.findByText('Langkah 1 dari 4 · Berkas')).toBeOnTheScreen();
    expect(screen.getByLabelText('Atau tempel isi CSV').props.value).toBe(EXAMPLE.valid.text);
    await press('Periksa berkas');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');

    expect(mapping(api.requests(PREVIEW).at(-1)!)).toEqual({ timezone_confirmed: true, scope: 'disjoint' });
  });

  it('posts again after an answer changes, and drops the acknowledgment', async () => {
    const api = mockImportApi('two');
    await openImport();
    await toPreview('2 dari 10 baris tidak valid', Recorded.two.first!);
    await fireEvent.press(screen.getByRole('checkbox', { name: 'Saya setuju 2 baris tidak valid dilewati dan tidak diimpor.' }));

    await press('Ubah pemetaan');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');
    await fireEvent.press(screen.getByRole('radio', { name: 'Belum tahu' }));
    await press('Lihat pratinjau');
    await screen.findByText('Langkah 3 dari 4 · Pratinjau');

    expect(api.requests(PREVIEW)).toHaveLength(3);
    expect(mapping(api.requests(PREVIEW)[2]).scope).toBe('unknown_overlap');
    expect(screen.getByRole('checkbox', { name: 'Saya setuju 2 baris tidak valid dilewati dan tidak diimpor.', checked: false })).toBeOnTheScreen();
  });

  it('goes back from the result to the tab, never to the committed preview', async () => {
    mockImportApi('valid');
    await openImport();
    await toPreview('Valid: dua perangkat, interval 1 jam', Recorded.valid.first!);
    await toResult();

    await press('Kembali');

    expect(await screen.findByRole('heading', { name: 'Beranda' })).toBeOnTheScreen();
    expect(screen.queryByText('Langkah 3 dari 4 · Pratinjau')).toBeNull();
  });
});

describe('after a reload', () => {
  let storage: Map<string, string>;

  /** A web page with a workspace and a draft already in sessionStorage, as a reload finds them. */
  async function reloadAt(url: string, draft: DraftSnapshot & { siteId: string; intent: CommitIntent | null }, legacy = false) {
    Platform.OS = 'web';
    storage = new Map();
    Object.defineProperty(globalThis, 'sessionStorage', {
      configurable: true,
      value: {
        getItem: (key: string) => storage.get(key) ?? null,
        setItem: (key: string, value: string) => storage.set(key, value),
        removeItem: (key: string) => storage.delete(key),
        clear: () => storage.clear(),
      },
    });
    Object.defineProperty(globalThis, 'document', { configurable: true, value: { documentElement: {} } });
    const workspace: Workspace = {
      token: 'token-recorded', siteId: 'site-recorded', scenarioId: 'empty',
      expiresAt: '2099-01-01T00:00:00Z',
      initialPeriod: { preset: 'last_7_days', start_date: '2026-10-19', end_date: '2026-10-25' },
    };
    if (legacy) {
      await saveWorkspace(workspace);
      storage.set('hematdaya.import-draft.v1', JSON.stringify({ ...draft, textDropped: false }));
    } else {
      const { epoch } = await seedConfirmedWorkspace(workspace);
      await AsyncStorage.setItem(ownerStorageKey(epoch, 'import-draft'), storeDraft(draft));
      if (draft.intent) writeRecovery(epoch, draft.intent);
    }
    await renderRouter('./src/app', { initialUrl: url });
  }

  afterEach(() => {
    Reflect.deleteProperty(globalThis, 'document');
  });

  const base = { siteId: 'site-recorded', answers: {}, intervalText: {}, importId: null, intent: null };
  const fileDraft = { ...base, source: { kind: 'file' as const, name: 'contoh-valid.csv' } };
  const reselect = 'Berkas contoh-valid.csv perlu dipilih ulang karena halaman dimuat ulang. Isi berkas tidak dapat dipulihkan dari peramban.';

  it('asks for a stored file again, and never claims it was recovered', async () => {
    mockImportApi('valid');
    await reloadAt('/impor/berkas', fileDraft);

    expect(await screen.findByText(reselect)).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Pilih berkas lagi' })).toBeOnTheScreen();
    expect(screen.queryByText('Berkas: contoh-valid.csv')).toBeNull();
  });

  it('reads a stored preview again, and commits it without the file', async () => {
    const api = mockImportApi('valid');
    await reloadAt('/impor/pratinjau', { ...fileDraft, answers: { timezone_confirmed: true, scope: 'disjoint' }, importId: Recorded.valid.answered!.id });

    expect(await screen.findByText('12 baris akan disimpan.')).toBeOnTheScreen();
    expect(api.requests(GET_IMPORT)).toHaveLength(1);
    await toResult();
    expect(api.requests(COMMIT)).toHaveLength(1);
    expect(api.requests(PREVIEW)).toEqual([]);
  });

  it('asks for the file before a new preview, and keeps the answers after the pick', async () => {
    const api = mockImportApi('valid', { get: () => respond(200, Recorded.valid.first) });
    const file = new File([EXAMPLE.valid.text], 'contoh-valid.csv', { type: 'text/csv' });
    pick.mockResolvedValue({ canceled: false, assets: [{ uri: 'blob:x', name: 'contoh-valid.csv', size: file.size, mimeType: 'text/csv', lastModified: 0, file }] });
    await reloadAt('/impor/pemetaan', { ...fileDraft, answers: { timezone_confirmed: true }, importId: Recorded.valid.first!.id });
    await screen.findByText('tempelan.csv · 12 baris data · kolom waktu timestamp · kolom nilai energi_wh (Wh)');
    await fireEvent.press(screen.getByRole('radio', { name: 'Ya, terpisah satu sama lain dan dari perangkat lain' }));

    await press('Lihat pratinjau');
    expect(await screen.findByRole('link', { name: reselect })).toBeOnTheScreen();
    expect(api.requests(PREVIEW)).toEqual([]);

    await press('Pilih berkas lagi');
    await press('Lihat pratinjau');
    await screen.findByText('Langkah 3 dari 4 · Pratinjau');
    expect(mapping(api.requests(PREVIEW)[0])).toEqual({ timezone_confirmed: true, scope: 'disjoint' });
    expect((api.requests(PREVIEW)[0].init.body as FormData).get('file')).toBeTruthy();
  });

  it('rejects a different file during reselection and previews the selected bytes again', async () => {
    const api = mockImportApi('valid');
    const original = new File([EXAMPLE.valid.text], 'contoh-valid.csv', { type: 'text/csv' });
    const other = new File([EXAMPLE.semi.text], 'berkas-lain.csv', { type: 'text/csv' });
    for (const file of [other, original]) {
      pick.mockResolvedValueOnce({
        canceled: false,
        assets: [{ uri: 'blob:x', name: file.name, size: file.size, mimeType: 'text/csv', lastModified: 0, file }],
      });
    }
    await reloadAt('/impor/pemetaan', {
      ...fileDraft,
      answers: { timezone_confirmed: true, scope: 'disjoint' },
      importId: Recorded.valid.answered!.id,
    });

    await fireEvent.press(await screen.findByRole('button', { name: 'Pilih berkas lagi' }));
    expect(await screen.findByText(/Pilih kembali contoh-valid.csv/)).toBeOnTheScreen();
    expect(screen.getByText(reselect)).toBeOnTheScreen();
    expect(api.requests(PREVIEW)).toEqual([]);

    await press('Pilih berkas lagi');
    await press('Lihat pratinjau');
    await screen.findByText('Langkah 3 dari 4 · Pratinjau');
    expect(api.requests(PREVIEW)).toHaveLength(1);
    const uploaded = (api.requests(PREVIEW)[0].init.body as FormData).get('file') as File;
    expect(uploaded.name).toBe(original.name);
    expect(await uploaded.text()).toBe(EXAMPLE.valid.text);
  });

  it('checks a stored commit before anything else', async () => {
    const api = mockImportApi('valid');
    await reloadAt('/impor/pratinjau', {
      ...fileDraft,
      importId: Recorded.valid.answered!.id,
      intent: { importId: Recorded.valid.answered!.id, key: 'k'.repeat(22), acknowledge: false },
    });

    expect(await screen.findByText('Status impor belum diketahui')).toBeOnTheScreen();
    expect(screen.queryByRole('button', { name: 'Konfirmasi impor' })).toBeNull();
    await press('Periksa status');
    expect(await screen.findByLabelText('Berhasil: Impor sudah dikonfirmasi sebelumnya')).toBeOnTheScreen();
    expect(api.requests(COMMIT)).toEqual([]);
  });

  it('checks and recovers a purged import after reloading an uncertain commit', async () => {
    const api = mockImportApi('valid', { get: () => failure(404, 'NOT_FOUND') });
    const importId = Recorded.valid.answered!.id;
    await reloadAt('/impor/pratinjau', { ...fileDraft, importId, intent: { importId, key: 'k'.repeat(22), acknowledge: false } });

    await fireEvent.press(await screen.findByRole('button', { name: 'Periksa status' }));
    expect(await screen.findByText('Pratinjau sudah tidak tersedia')).toBeOnTheScreen();
    expect(screen.getByText('ID referensi: ref_1.')).toBeOnTheScreen();
    expect(screen.queryByText(FAKE_SECRET)).toBeNull();
    await press('Buat pratinjau baru');
    expect(await screen.findByText(reselect)).toBeOnTheScreen();
    expect(api.requests(GET_IMPORT)).toHaveLength(1);
    expect(api.requests(COMMIT)).toEqual([]);
  });

  it('verifies an old import explicitly before moving its original attempt to the confirmed owner', async () => {
    let lookups = 0;
    const api = mockImportApi('valid', {
      get: () => ++lookups === 1
        ? failure(503, 'DATABASE_UNAVAILABLE')
        : respond(200, Recorded.valid.answered),
    });
    const importId = Recorded.valid.answered!.id;
    const key = 'l'.repeat(22);
    await reloadAt('/impor/pratinjau', { ...fileDraft, importId, intent: { importId, key, acknowledge: false } }, true);
    expect(await screen.findByText('Status impor belum diketahui')).toBeOnTheScreen();
    expect(api.requests(GET_IMPORT)).toHaveLength(0);
    expect(api.requests(COMMIT)).toHaveLength(0);
    await press('Periksa status');
    expect(await screen.findByText('Status impor belum dapat diperiksa')).toBeOnTheScreen();
    expect(storage.has('hematdaya.import-draft.v1')).toBe(true);
    expect(api.requests(COMMIT)).toHaveLength(0);

    await press('Periksa status');
    expect(await screen.findByText('Impor belum tercatat')).toBeOnTheScreen();
    expect(storage.has('hematdaya.import-draft.v1')).toBe(false);
    await press('Kirim lagi');
    await screen.findByText('Langkah 4 dari 4 · Hasil');
    const requests = api.requests(COMMIT);
    expect(requests).toHaveLength(1);
    expect(commitKey(requests[0])).toBe(key);
  });

  it('brings a stored paste back, and says when it was too large to keep', async () => {
    mockImportApi('valid');
    await reloadAt('/impor/berkas', { ...base, source: { kind: 'paste', text: EXAMPLE.valid.text } });
    expect(await screen.findByDisplayValue(EXAMPLE.valid.text)).toBeOnTheScreen();
    await screen.unmount();

    await reloadAt('/impor/berkas', { ...base, source: null, textDropped: true });
    expect(await screen.findByText('Isi tempelan terlalu besar untuk disimpan di peramban. Tempel ulang isinya.')).toBeOnTheScreen();
  });
});

describe('long error lists', () => {
  beforeEach(() => storeWorkspace());

  async function toPages(errors?: Handler) {
    const send = spyFocus();
    const api = mockImportApi('valid', { preview: () => respond(201, Recorded.pages.preview), ...(errors ? { errors } : {}) });
    await openImport();
    await pasteText('timestamp,perangkat,energi_wh\n');
    await press('Periksa berkas');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');
    await press('Lihat pratinjau');
    await screen.findByText('Langkah 3 dari 4 · Pratinjau');
    return { api, send };
  }

  const listItems = () => screen.getAllByText(/^Baris data \d+, energi_wh: .* \(baris berkas \d+\)$/).filter((node) => node.parent?.props.role === 'listitem');

  it('shows 50 rows, a short summary and a link to the list', async () => {
    const { send } = await toPages();

    expect(listItems()).toHaveLength(50);
    const summary = screen.getByLabelText('Baris bermasalah dalam berkas');
    expect(within(summary).getAllByRole('link')).toHaveLength(6);
    await fireEvent.press(within(summary).getByRole('link', { name: 'Lihat semua baris bermasalah' }));
    expect(focusedLabels(send).at(-1)).toBe('Baris bermasalah');
  });

  it('loads the next 50 rows by cursor', async () => {
    const { api } = await toPages();

    await press('Muat 50 baris berikutnya');

    await waitFor(() => expect(listItems()).toHaveLength(60));
    const [page] = api.requests(/\/errors$/);
    expect(page.url.searchParams.get('limit')).toBe('50');
    expect(page.url.searchParams.get('cursor')).toBe(Recorded.pages.preview.next_error_cursor);
    expect(screen.queryByRole('button', { name: 'Muat 50 baris berikutnya' })).toBeNull();
  });

  it('keeps the loaded rows when a page fails', async () => {
    await toPages(() => failure(500, 'INTERNAL_ERROR'));

    await press('Muat 50 baris berikutnya');

    expect(await screen.findByText('Baris berikutnya belum dapat dimuat')).toBeOnTheScreen();
    expect(screen.getByText(/ID referensi: ref_1\./)).toBeOnTheScreen();
    expect(listItems()).toHaveLength(50);
    expectNoSecret();
  });
});

describe('import accessibility', () => {
  beforeEach(() => storeWorkspace());

  type Host = { type: unknown; props: Record<string, unknown>; children: (Host | string)[]; parent: Host | null };

  function hosts(predicate: (node: Host) => boolean): Host[] {
    const found: Host[] = [];
    const walk = (node: Host | string) => {
      if (typeof node === 'string') {
        return;
      }
      if (predicate(node)) {
        found.push(node);
      }
      node.children.forEach(walk);
    };
    walk(screen.root as unknown as Host);
    return found;
  }

  function contains(ancestor: Host, node: Host) {
    for (let current: Host | null = node; current; current = current.parent) {
      if (current === ancestor) {
        return true;
      }
    }
    return false;
  }

  function checkStep(subtitle: string, primary: string) {
    for (const role of ['button', 'link', 'checkbox', 'radio'] as const) {
      for (const control of screen.queryAllByRole(role)) {
        const label = control.props['aria-label'] ?? control.props.accessibilityLabel ?? within(control).queryAllByText(/\S/).length;
        expect(label).toBeTruthy();
        expect((StyleSheet.flatten(control.props.style as object) as { minHeight?: number })?.minHeight).toBeGreaterThanOrEqual(tokens.size.targetMinimum);
      }
    }
    const scroll = hosts((node) => node.type === 'RCTScrollView').find((node) => within(node as never).queryByText(subtitle));
    expect(scroll).toBeDefined();
    const button = screen.getByRole('button', { name: primary });
    expect(contains(scroll!, button as unknown as Host)).toBe(false);
    expect(screen.getByTestId('import-keyboard-avoiding')).toBeOnTheScreen();
  }

  it('meets target, label, footer and keyboard rules on every step', async () => {
    mockImportApi('two');
    await openImport();
    checkStep('Langkah 1 dari 4 · Berkas', 'Periksa berkas');

    await useExample('2 dari 10 baris tidak valid');
    await press('Periksa berkas');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');
    checkStep('Langkah 2 dari 4 · Arti kolom dan pemetaan', 'Lihat pratinjau');

    await answerQuestions(Recorded.two.first!);
    await press('Lihat pratinjau');
    await screen.findByText('Langkah 3 dari 4 · Pratinjau');
    checkStep('Langkah 3 dari 4 · Pratinjau', 'Konfirmasi impor');
    expect(hosts((node) => node.props.role === 'status').length).toBeGreaterThan(0);

    await fireEvent.press(screen.getByRole('checkbox'));
    await toResult();
    checkStep('Langkah 4 dari 4 · Hasil', 'Lihat periode data');
    expect(hosts((node) => node.props.role === 'status' && node.props.accessibilityLiveRegion === 'polite').length).toBeGreaterThan(0);
  });
});

describe('hostile text', () => {
  const FORMULA = '=HYPERLINK("http://x","y")';
  const SCRIPT = '<script>alert(1)</script>';

  function expectPlain(name: string) {
    expect(screen.queryByRole('link', { name })).toBeNull();
  }

  it('renders formula and markup names as plain text on every screen they reach', async () => {
    await storeWorkspace();
    const hostile = Recorded.hostile;
    mockImportApi('hostile');
    await openImport();
    await pasteText(Recorded.hostile_text);
    await press('Periksa berkas');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');

    expect(screen.getByText(`${FORMULA}: interval 1 jam`)).toBeOnTheScreen();
    expect(screen.getByText(`${SCRIPT}: interval 1 jam`)).toBeOnTheScreen();
    [FORMULA, SCRIPT].forEach(expectPlain);

    await answerQuestions(hostile.first!);
    await press('Lihat pratinjau');
    await screen.findByText('Langkah 3 dari 4 · Pratinjau');
    await press('Lihat pemetaan kolom');
    expect(screen.getByText(`${FORMULA}: interval 1 jam (disimpulkan)`)).toBeOnTheScreen();
    expect(screen.getByText(`${SCRIPT}: interval 1 jam (disimpulkan)`)).toBeOnTheScreen();
    [FORMULA, SCRIPT].forEach(expectPlain);

    await toResult();
    const created = hostile.commit!.assets_created!.map((asset) => asset.name).join(', ');
    expect(created).toContain(FORMULA);
    expect(screen.getByLabelText(`Perangkat baru: ${created}`)).toBeOnTheScreen();
    expect(screen.getByText(created)).toBeOnTheScreen();
    [FORMULA, SCRIPT].forEach(expectPlain);

    await press('Lihat periode data');
    await screen.findByRole('heading', { name: 'Beranda' });
    expect((await screen.findAllByText(FORMULA)).length).toBeGreaterThan(0);
    expect(screen.getAllByText(SCRIPT).length).toBeGreaterThan(0);
    [FORMULA, SCRIPT].forEach(expectPlain);

    await fireEvent.press(screen.getByRole('tab', { name: 'Perangkat' }));
    const list = await screen.findByLabelText('Daftar perangkat, urut energi tercatat');
    expect(within(list).getAllByText(FORMULA).length).toBeGreaterThan(0);
    expect(within(list).getAllByText(SCRIPT).length).toBeGreaterThan(0);
    [FORMULA, SCRIPT].forEach(expectPlain);
  });

  it('shows the file name the service stored for a hostile upload name', async () => {
    await storeWorkspace();
    mockImportApi('hostile', { preview: () => respond(201, Recorded.hostile.file_first) });
    pick.mockResolvedValue(nativeAsset({ name: '../<script>alert(1)</script>.csv' }));
    await openImport();
    await press('Pilih berkas CSV');
    await press('Periksa berkas');
    await screen.findByText('Langkah 2 dari 4 · Arti kolom dan pemetaan');

    expect(screen.getByText(/^script>\.csv · 4 baris data · /)).toBeOnTheScreen();
    expectPlain('script>.csv');
  });
});

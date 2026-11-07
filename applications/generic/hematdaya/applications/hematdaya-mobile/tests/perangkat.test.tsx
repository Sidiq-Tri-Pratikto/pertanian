// Recorded on 2026-11-07 from the merged hematdaya-api at 6563a2f (Alembic head 0009), by real demo sessions.
import { focusManager } from '@tanstack/react-query';
import { act, fireEvent, renderRouter, screen, waitFor, within } from 'expo-router/testing-library';
import { seedConfirmedWorkspace } from './fixtures/workspaces';

import recorded from './fixtures/assets.json';
import { hourlyHistory, mondayWindow, weeklyHistory, weekWindow } from './fixtures/history';

type Row = { asset_id: string; name: string };
type Detail = { asset: { id: string; name: string; bindings: unknown[]; sources: unknown[] }; summary: Record<string, unknown> & { assets: Row[]; coverage: object; origins: string[] } };
type Scenario = {
  initial_period: { preset: string; start_date: string; end_date: string };
  summary: Record<string, unknown> & { window: unknown; assets: Row[]; coverage: object; scope: { excluded: unknown[] } };
  assets: { items: { id: string; name: string }[]; next_cursor: null };
  notices: { kind: string; asset_id: string | null; title: string; body: string }[];
  details: Record<string, Detail>;
  today?: unknown;
  today_asset?: Detail['summary'];
};
const Recorded = recorded as unknown as Record<string, Scenario>;

const LIST = 'Daftar perangkat, urut energi tercatat';
const FAKE_SECRET = 'fake-secret-123';
const KEPT = /Angka yang tampil adalah data terakhir yang terkonfirmasi\./;

function respond(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status });
}

function failure(status: number, code: string, recovery: object = { retryable: false }, requestId = 'ref_1') {
  return respond(status, {
    error: {
      code,
      message: 'Permintaan belum dapat diselesaikan. Coba lagi nanti.',
      request_id: requestId,
      recovery,
      debug_info: FAKE_SECRET,
    },
  });
}

const SERVER_FAILED = () => failure(500, 'INTERNAL_ERROR');
const SESSION_ENDED = () => failure(401, 'SESSION_EXPIRED');
const NOT_FOUND = () => failure(404, 'NOT_FOUND', { retryable: false }, 'ref_404');
// TanStack first asks about a retry with a count of 0, so `max_attempts: 1` still spends one retry. No wait for it here.
const RETRYABLE = () => failure(503, 'DATABASE_UNAVAILABLE', { retryable: true, retry_after_seconds: 0, max_attempts: 1 });
const NEVER = () => new Promise<Response>(() => undefined);

function scenarioOf(url: URL): Scenario {
  const siteId = /\/sites\/([^/]+)\//.exec(url.pathname)?.[1] ?? '';
  return Recorded[siteId.replace(/^site-/, '')];
}

function detailOf(url: URL): { entry: Detail; scenario: Scenario } {
  const id = decodeURIComponent(/\/assets\/([^/]+)/.exec(url.pathname)?.[1] ?? '');
  for (const scenario of Object.values(Recorded)) {
    for (const entry of Object.values(scenario.details)) {
      if (entry.asset.id === id) {
        return { entry, scenario };
      }
    }
  }
  throw new Error(`No recorded asset ${id}`);
}

function isToday(url: URL) {
  return url.searchParams.get('preset') === 'today';
}

type Handler = (url: URL, init: RequestInit) => Response | Promise<Response>;
type Api = { summary?: Handler; assets?: Handler; insights?: Handler; asset?: Handler; assetSummary?: Handler; history?: Handler; create?: Handler };

const defaults: Required<Api> = {
  create: (_url, init) => {
    const scenario = JSON.parse(String(init.body)).scenario_id as string;
    return respond(201, {
      token: `hdd_v1_${scenario}`,
      site_id: `site-${scenario}`,
      scenario_id: scenario,
      expires_at: '2099-01-01T00:00:00Z',
      initial_period: Recorded[scenario].initial_period,
    });
  },
  summary: (url) => {
    const scenario = scenarioOf(url);
    return respond(200, isToday(url) && scenario.today ? scenario.today : scenario.summary);
  },
  assets: (url) => respond(200, scenarioOf(url).assets),
  insights: (url) => {
    const scenario = scenarioOf(url);
    return respond(200, { window: scenario.summary.window, observations: [], notices: scenario.notices, learning_count: 0, comparable_count: 0 });
  },
  assetSummary: (url) => {
    const { entry, scenario } = detailOf(url);
    return respond(200, isToday(url) && scenario.today_asset ? scenario.today_asset : entry.summary);
  },
  asset: (url) => respond(200, detailOf(url).entry.asset),
  history: () => respond(200, weeklyHistory()),
};

function mockApi(api: Api = {}) {
  const handlers = { ...defaults, ...api };
  return jest.spyOn(globalThis, 'fetch').mockImplementation(async (input, init = {}) => {
    const url = new URL(String(input));
    const path = url.pathname;
    if (/^\/api\/v1\/demo\/sessions$/.test(path)) {
      return handlers.create(url, init);
    }
    if (/^\/api\/v1\/sites\/[^/]+\/summary$/.test(path)) {
      return handlers.summary(url, init);
    }
    if (/^\/api\/v1\/sites\/[^/]+\/assets$/.test(path)) {
      return handlers.assets(url, init);
    }
    if (/^\/api\/v1\/sites\/[^/]+\/insights$/.test(path)) {
      return handlers.insights(url, init);
    }
    if (/^\/api\/v1\/assets\/[^/]+\/summary$/.test(path)) {
      return handlers.assetSummary(url, init);
    }
    if (/^\/api\/v1\/assets\/[^/]+\/measurements$/.test(path)) {
      return handlers.history(url, init);
    }
    if (/^\/api\/v1\/assets\/[^/]+$/.test(path)) {
      return handlers.asset(url, init);
    }
    return respond(404, {});
  });
}

function requests(fetchMock: jest.SpyInstance, pattern: RegExp): URL[] {
  return fetchMock.mock.calls.map(([input]) => new URL(String(input))).filter((url) => pattern.test(url.pathname));
}

async function storeWorkspace(scenario: string, scenarioId = scenario) {
  await seedConfirmedWorkspace({
      token: `hdd_v1_${scenario}`,
      siteId: `site-${scenario}`,
      scenarioId,
      expiresAt: '2099-01-01T00:00:00Z',
      initialPeriod: Recorded[scenario].initial_period,
    });
}

async function openPerangkat(scenario: string, scenarioId = scenario) {
  await storeWorkspace(scenario, scenarioId);
  await renderRouter('./src/app', { initialUrl: '/perangkat' });
  return findList();
}

// A plain View with a role is not an accessibility element, so React Native Testing Library finds it by label.
async function findList() {
  const list = await screen.findByLabelText(LIST);
  expect(list.props.role).toBe('list');
  return list;
}

/** The status region a text sits in. Fails when the text is outside any. */
function statusRegionOf(text: string | RegExp) {
  let node: ReturnType<typeof screen.getByText> | null = screen.getByText(text);
  while (node && node.props.role !== 'status') {
    node = node.parent as typeof node;
  }
  expect(node).not.toBeNull();
  return node!;
}

function rowNamed(list: Parameters<typeof within>[0], name: string) {
  return within(list).getByRole('link', { name: new RegExp(`^${name},`) });
}

function rowNames(list: Parameters<typeof within>[0]) {
  return within(list)
    .getAllByRole('link')
    .map((row) => String(row.props['aria-label'] ?? row.props.accessibilityLabel).split(',')[0]);
}

const patchedSummary = (scenario: string, patch: (summary: Scenario['summary']) => object): Handler => () =>
  respond(200, patch(Recorded[scenario].summary));

afterEach(() => jest.restoreAllMocks());

describe('Perangkat list', () => {
  it('lists every measured asset in the order the service gave', async () => {
    mockApi();

    const list = await openPerangkat('h-base');

    expect(rowNames(list)).toEqual(['Kulkas', 'TV', 'Pompa Air', 'Router']);
    expect(within(rowNamed(list, 'Kulkas')).getByText('8,400 kWh')).toBeOnTheScreen();
    expect(within(rowNamed(list, 'TV')).getByText('2,520 kWh')).toBeOnTheScreen();
    expect(within(rowNamed(list, 'Pompa Air')).getByText('2,100 kWh')).toBeOnTheScreen();
    expect(within(rowNamed(list, 'Router')).getByText('1,680 kWh')).toBeOnTheScreen();
    expect(await within(rowNamed(list, 'Kulkas')).findByText('Perangkat · Dapur · Pendingin makanan')).toBeOnTheScreen();
    expect(within(rowNamed(list, 'Pompa Air')).getByText('Perangkat · Halaman belakang · Pompa')).toBeOnTheScreen();
    expect(screen.getByText('Periode aktif: 19–25 Oktober 2026 · Asia/Jakarta')).toBeOnTheScreen();
    expect(screen.getByText('Cakupan pengukuran: 4 perangkat')).toBeOnTheScreen();
    expect(screen.getByText('Demo · Data simulasi')).toBeOnTheScreen();
    expect(screen.getByText('Urutan berdasarkan energi tercatat pada periode ini. Urutan bukan penilaian boros atau hemat.')).toBeOnTheScreen();
    expect(screen.queryByText(/14,700 kWh/)).toBeNull();
  });

  it('keeps individual values and explains a scope conflict, with no combined total', async () => {
    mockApi();

    const list = await openPerangkat('h-scope');

    expect(rowNames(list)).toEqual(['Meter utama', 'TV', 'Pompa Air', 'Router', 'Kulkas']);
    expect(await within(rowNamed(list, 'Meter utama')).findByText('Meter lokasi · Teras · Meter rumah')).toBeOnTheScreen();
    expect(within(rowNamed(list, 'Meter utama')).getByText('10,000 kWh')).toBeOnTheScreen();
    const kulkas = rowNamed(list, 'Kulkas');
    expect(within(kulkas).getByText('— kWh')).toBeOnTheScreen();
    expect(within(kulkas).getByText('Colokan simulasi Kulkas (sumber kedua): 1,000 kWh')).toBeOnTheScreen();
    expect(within(kulkas).getByText('Sumber demo (simulasi): 1,000 kWh')).toBeOnTheScreen();
    expect(screen.getByText('Total gabungan belum dapat dihitung')).toBeOnTheScreen();
    const issues = (Recorded['h-scope'].summary.scope as unknown as { issues: { message: string }[] }).issues;
    const notice = issues.map((issue) => issue.message).join(' ');
    expect(screen.getByText(`${notice} Nilai masing-masing tetap ditampilkan.`)).toBeOnTheScreen();
    expect(screen.queryByText(/Pilih cakupan/)).toBeNull();
  });

  it('offers no control and no judgement on any row', async () => {
    mockApi();

    const list = await openPerangkat('h-scope');

    expect(within(list).queryByRole('switch')).toBeNull();
    expect(within(list).queryByRole('button')).toBeNull();
    expect(within(list).queryByText(/paling boros/i)).toBeNull();
    expect(within(list).queryByText(/nyalakan|matikan/i)).toBeNull();
  });

  it('lists the industrial demo', async () => {
    mockApi();

    const list = await openPerangkat('i-base');

    expect(rowNames(list)[0]).toBe('Oven');
    expect(within(rowNamed(list, 'Oven')).getByText('72,000 kWh')).toBeOnTheScreen();
    expect(await within(rowNamed(list, 'Oven')).findByText('Perangkat · Area produksi · Pemanas/memasak')).toBeOnTheScreen();
  });
});

describe('Perangkat failures', () => {
  it('says a first read is pending, with no number', async () => {
    mockApi({ summary: NEVER });
    await storeWorkspace('h-base');

    await renderRouter('./src/app', { initialUrl: '/perangkat' });

    await screen.findByText('Memuat data perangkat…');
    statusRegionOf('Memuat data perangkat…');
    expect(screen.queryByText(/kWh/)).toBeNull();
  });

  it('shows the message and reference of a first read that failed, with no retry when it is not allowed', async () => {
    mockApi({ summary: SERVER_FAILED });
    await storeWorkspace('h-base');

    await renderRouter('./src/app', { initialUrl: '/perangkat' });

    expect(await screen.findByText('Data perangkat belum dapat dimuat')).toBeOnTheScreen();
    const status = statusRegionOf('Data perangkat belum dapat dimuat');
    expect(within(status).getByText(/Permintaan belum dapat diselesaikan\. Coba lagi nanti\./)).toBeOnTheScreen();
    expect(within(status).getByText(/ID referensi: ref_1/)).toBeOnTheScreen();
    expect(screen.queryByRole('button', { name: 'Coba lagi' })).toBeNull();
    expect(screen.queryByText(/kWh/)).toBeNull();
    expect(screen.queryByText(new RegExp(FAKE_SECRET))).toBeNull();
  });

  it('offers a retry when the service allows one, and the retry shows the rows', async () => {
    let healthy = false;
    mockApi({
      summary: (url) => (healthy ? defaults.summary(url, {}) : RETRYABLE()),
    });
    await storeWorkspace('h-base');

    await renderRouter('./src/app', { initialUrl: '/perangkat' });
    const retry = await screen.findByRole('button', { name: 'Coba lagi' });
    healthy = true;
    await fireEvent.press(retry);

    const list = await findList();
    expect(rowNames(list)).toHaveLength(4);
    expect(screen.queryByText('Data perangkat belum dapat dimuat')).toBeNull();
  });

  it('keeps the rows while another period is pending', async () => {
    mockApi({ summary: (url) => (isToday(url) ? NEVER() : defaults.summary(url, {})) });

    const list = await openPerangkat('h-base');
    await fireEvent.press(screen.getByRole('button', { name: 'Hari ini' }));

    expect(rowNames(list)).toHaveLength(4);
    expect(screen.getByText('8,400 kWh')).toBeOnTheScreen();
    expect(screen.getByText('Periode aktif: 19–25 Oktober 2026 · Asia/Jakarta')).toBeOnTheScreen();
    expect(screen.queryByText('0,000 kWh')).toBeNull();
  });

  it('keeps rows, values and selector when another period fails, and recovers on the next choice', async () => {
    mockApi({ summary: (url) => (isToday(url) ? SERVER_FAILED() : defaults.summary(url, {})) });

    const list = await openPerangkat('h-base');
    await fireEvent.press(screen.getByRole('button', { name: 'Hari ini' }));

    expect(await screen.findByText('Data perangkat belum dapat diperbarui')).toBeOnTheScreen();
    expect(screen.getByText(KEPT)).toBeOnTheScreen();
    expect(rowNames(list)).toEqual(['Kulkas', 'TV', 'Pompa Air', 'Router']);
    expect(screen.getByText('8,400 kWh')).toBeOnTheScreen();
    expect(screen.getByText('1,680 kWh')).toBeOnTheScreen();
    expect(screen.getByLabelText('Periode')).toBeOnTheScreen();
    expect(screen.getByText('Periode aktif: 19–25 Oktober 2026 · Asia/Jakarta')).toBeOnTheScreen();
    expect(screen.queryByText('0,000 kWh')).toBeNull();

    await fireEvent.press(screen.getByRole('button', { name: '7 hari lengkap terakhir' }));

    await waitFor(() => expect(screen.queryByText('Data perangkat belum dapat diperbarui')).toBeNull());
    expect(screen.getByText('8,400 kWh')).toBeOnTheScreen();
  });

  it('keeps the rows when a refresh from Beranda fails', async () => {
    let healthy = true;
    mockApi({ summary: (url) => (healthy ? defaults.summary(url, {}) : SERVER_FAILED()) });
    await openPerangkat('h-base');

    await fireEvent.press(screen.getByRole('tab', { name: 'Beranda' }));
    healthy = false;
    await fireEvent.press(await screen.findByRole('button', { name: 'Perbarui' }));
    await screen.findByText('Data belum dapat diperbarui');
    await fireEvent.press(screen.getByRole('tab', { name: 'Perangkat' }));

    expect(await screen.findByText('Data perangkat belum dapat diperbarui')).toBeOnTheScreen();
    expect(rowNames(screen.getByLabelText(LIST))).toHaveLength(4);
    expect(screen.getByText('8,400 kWh')).toBeOnTheScreen();
  });

  it('removes only location and category when their read fails, and says so', async () => {
    mockApi({ assets: SERVER_FAILED });

    const list = await openPerangkat('h-base');

    expect(await screen.findByText('Lokasi dan kategori belum dapat dimuat.')).toBeOnTheScreen();
    expect(within(rowNamed(list, 'Kulkas')).getByText('8,400 kWh')).toBeOnTheScreen();
    expect(within(rowNamed(list, 'Kulkas')).getByText('Kelengkapan data: 100% periode')).toBeOnTheScreen();
    expect(within(rowNamed(list, 'Kulkas')).getByText('Perangkat')).toBeOnTheScreen();
    expect(screen.queryByText(/Dapur/)).toBeNull();
  });

  it('keeps rows and leaves freshness unknown for a legacy summary', async () => {
    mockApi({ insights: SERVER_FAILED });

    const list = await openPerangkat('h-base');

    expect(await screen.findByText('Kesegaran sumber belum diketahui.')).toBeOnTheScreen();
    expect(within(rowNamed(list, 'Router')).getByText('1,680 kWh')).toBeOnTheScreen();
    expect(screen.queryByText('Data belum diperbarui')).toBeNull();
  });
});

describe('Perangkat empty', () => {
  it('makes no request with no workspace', async () => {
    const fetchMock = mockApi();

    await renderRouter('./src/app', { initialUrl: '/perangkat' });

    expect(await screen.findByText('Belum ada perangkat')).toBeOnTheScreen();
    expect(requests(fetchMock, /\/(summary|assets)$/)).toEqual([]);
  });

  it('shows no number and no date with no assets', async () => {
    mockApi();
    await storeWorkspace('empty');

    await renderRouter('./src/app', { initialUrl: '/perangkat' });

    expect(await screen.findByText('Belum ada perangkat')).toBeOnTheScreen();
    expect(screen.queryByText(/kWh/)).toBeNull();
    expect(screen.queryByText(/Periode aktif/)).toBeNull();
    expect(screen.queryByText('Lihat rencana fitur ini')).toBeNull();
  });

  it('keeps its entry points, inside the tab', async () => {
    mockApi();
    await storeWorkspace('empty');
    await renderRouter('./src/app', { initialUrl: '/perangkat' });
    await screen.findByText('Belum ada perangkat');

    await fireEvent.press(screen.getByRole('button', { name: 'Tambah sumber' }));
    expect(await screen.findByRole('heading', { name: 'Sumber dan meter' })).toBeOnTheScreen();
    expect(screen.getByText('Segera hadir')).toBeOnTheScreen();
    expect(screen.getByRole('tab', { name: 'Perangkat', selected: true })).toBeOnTheScreen();

    await fireEvent.press(screen.getByRole('button', { name: 'Kembali' }));
    expect(await screen.findByRole('heading', { name: 'Perangkat' })).toBeOnTheScreen();

    await fireEvent.press(screen.getByRole('button', { name: 'Impor data' }));
    expect(await screen.findByRole('heading', { name: 'Impor data CSV' })).toBeOnTheScreen();

    await fireEvent.press(screen.getByRole('button', { name: 'Kembali' }));
    await fireEvent.press(await screen.findByRole('button', { name: 'Coba demo' }));
    expect(await screen.findByRole('heading', { name: 'Pilih data demo' })).toBeOnTheScreen();
  });

  it('explains an ended session, and a new demo shows only its own assets', async () => {
    let ended = true;
    mockApi({ summary: (url) => (ended ? SESSION_ENDED() : defaults.summary(url, {})) });
    await storeWorkspace('h-base');

    await renderRouter('./src/app', { initialUrl: '/perangkat' });

    expect(await screen.findByText('Sesi demo sudah berakhir')).toBeOnTheScreen();
    expect(screen.getByText('Belum ada perangkat')).toBeOnTheScreen();

    ended = false;
    await fireEvent.press(screen.getByRole('button', { name: 'Coba demo' }));
    await fireEvent.press(await screen.findByRole('radio', { name: 'Industri' }));
    await fireEvent.press(screen.getByRole('button', { name: 'Buka demo' }));

    const list = await findList();
    expect(rowNames(list)[0]).toBe('Oven');
    expect(screen.queryByText(/Kulkas/)).toBeNull();
  });
});

describe('Perangkat quality', () => {
  it('shows partial coverage per row', async () => {
    mockApi();

    const list = await openPerangkat('h-learning-partial');

    expect(within(rowNamed(list, 'Pompa Air')).getByText('Kelengkapan data: 71,4% periode')).toBeOnTheScreen();
    expect(within(rowNamed(list, 'Kulkas')).getByText('Kelengkapan data: 98,8% periode')).toBeOnTheScreen();
  });

  it('shows a measured zero as a zero with complete data', async () => {
    mockApi();

    const list = await openPerangkat('h-zero');

    for (const row of within(list).getAllByRole('link')) {
      expect(within(row).getByText('0,000 kWh')).toBeOnTheScreen();
      expect(within(row).getByText('Nol terukur dengan data lengkap')).toBeOnTheScreen();
    }
  });

  it('shows a period with no data as no value, never a zero', async () => {
    mockApi();

    const list = await openPerangkat('h-base');
    await fireEvent.press(screen.getByRole('button', { name: 'Hari ini' }));
    await screen.findByText('Periode aktif: 26 Oktober 2026 · Asia/Jakarta');

    for (const row of within(list).getAllByRole('link')) {
      expect(within(row).getByText('— kWh')).toBeOnTheScreen();
      expect(within(row).getByText('Belum ada data pada periode ini')).toBeOnTheScreen();
    }
    expect(screen.queryByText('0,000 kWh')).toBeNull();
  });

  it('says a stale source has no new data, beside its coverage, and never that it is off', async () => {
    mockApi();

    const list = await openPerangkat('h-stale-offline');

    const router = rowNamed(list, 'Router');
    expect(await within(router).findByText('Data belum diperbarui')).toBeOnTheScreen();
    expect(within(router).getByText('Kelengkapan data: 96,4% periode')).toBeOnTheScreen();
    expect(within(rowNamed(list, 'Kulkas')).queryByText('Data belum diperbarui')).toBeNull();
    expect(screen.queryByText(/\bmati\b/i)).toBeNull();
  });

  it('notes an allocated estimate', async () => {
    mockApi({ summary: patchedSummary('h-base', (summary) => ({ ...summary, coverage: { ...summary.coverage, allocated_estimate: true } })) });

    await openPerangkat('h-base');

    expect(screen.getByText('Sebagian interval melewati batas periode dan dibagi rata dalam intervalnya (estimasi).')).toBeOnTheScreen();
  });

  it('names what the scope leaves out', async () => {
    mockApi({
      summary: patchedSummary('h-base', (summary) => ({
        ...summary,
        scope: { ...summary.scope, excluded: [{ asset_id: 'lama', name: 'Lampu Lama', reason: 'archived' }] },
      })),
    });

    await openPerangkat('h-base');

    expect(screen.getByText(/Tidak termasuk: Lampu Lama\./)).toBeOnTheScreen();
  });

  it('keeps imported data apart from simulated data', async () => {
    mockApi();

    const list = await openPerangkat('imported', 'empty');

    expect(rowNames(list)).toEqual(['Kulkas', 'Router']);
    for (const row of within(list).getAllByRole('link')) {
      expect(within(row).getByText('Perangkat')).toBeOnTheScreen();
      expect(within(row).getByText('Kelengkapan data: 1,1% periode')).toBeOnTheScreen();
    }
    expect(screen.getByText('Data historis · Impor CSV')).toBeOnTheScreen();
    expect(screen.queryByText('Demo · Data simulasi')).toBeNull();
  });

  it('moves every tab when the period changes here', async () => {
    const fetchMock = mockApi();

    await openPerangkat('h-base');
    await fireEvent.press(screen.getByRole('button', { name: 'Hari ini' }));
    await screen.findByText('Periode aktif: 26 Oktober 2026 · Asia/Jakarta');

    expect(requests(fetchMock, /\/sites\/[^/]+\/summary$/).some(isToday)).toBe(true);
    await fireEvent.press(screen.getByRole('tab', { name: 'Beranda' }));
    expect(await screen.findByText('Periode aktif: 26 Oktober 2026 · Asia/Jakarta')).toBeOnTheScreen();
  });
});

function assetIdOf(scenario: string, name: string) {
  return Recorded[scenario].details[name].asset.id;
}

/** Opens detail by pressing its row, so the list stays underneath. */
async function pressRow(scenario: string, name: string, scenarioId = scenario) {
  const list = await openPerangkat(scenario, scenarioId);
  await fireEvent.press(rowNamed(list, name));
  await screen.findByRole('heading', { name });
}

/** Opens detail by address, with nothing underneath. */
async function openAddress(scenario: string, name: string, scenarioId = scenario) {
  await storeWorkspace(scenario, scenarioId);
  await renderRouter('./src/app', { initialUrl: `/asset/${assetIdOf(scenario, name)}` });
}

describe('asset detail', () => {
  it('opens from its row with the same period, values and provenance, and no share', async () => {
    const fetchMock = mockApi();

    await pressRow('h-base', 'Kulkas');

    expect(screen.getByText('Perangkat · Dapur · Pendingin makanan')).toBeOnTheScreen();
    expect(screen.getByText('Periode aktif: 19–25 Oktober 2026 · Asia/Jakarta')).toBeOnTheScreen();
    expect(screen.getByText(/Cakupan pengukuran: 1 perangkat \(hanya beban yang diukur sumber ini\)/)).toBeOnTheScreen();
    expect(screen.getByText('8,400 kWh')).toBeOnTheScreen();
    expect(screen.getByText('Kelengkapan data: 100% periode')).toBeOnTheScreen();
    expect(screen.getByText('Demo · Data simulasi')).toBeOnTheScreen();
    expect(screen.getByRole('tab', { name: 'Perangkat', selected: true })).toBeOnTheScreen();

    expect(await screen.findByText('Sumber data')).toBeOnTheScreen();
    const sources = await screen.findByLabelText('Sumber data');
    expect(within(sources).getByText('Sumber demo (simulasi)')).toBeOnTheScreen();
    expect(within(sources).getByText('Simulasi')).toBeOnTheScreen();
    expect(within(sources).getByText('1 jam · resolusi 0,001 kWh')).toBeOnTheScreen();
    expect(within(sources).getByText('mulai 28 September 2026 00.00')).toBeOnTheScreen();
    expect(within(sources).getByText('Sumber acuan')).toBeOnTheScreen();

    const quality = screen.getByLabelText('Kualitas data');
    expect(within(quality).getByText('Pengukuran terakhir')).toBeOnTheScreen();
    expect(within(quality).getByText('26 Oktober 2026 00.00 (data simulasi)')).toBeOnTheScreen();
    expect(within(quality).getByText('Asal data')).toBeOnTheScreen();

    const id = assetIdOf('h-base', 'Kulkas');
    const assetCalls = requests(fetchMock, /^\/api\/v1\/assets\//).map((url) => `${url.pathname}${url.search}`);
    expect(assetCalls).toEqual(expect.arrayContaining([`/api/v1/assets/${id}/summary?preset=last_7_days`, `/api/v1/assets/${id}`]));
    expect(assetCalls.some((call) => call.includes('/measurements'))).toBe(false);
    expect(screen.queryByText(/100,00%/)).toBeNull();
    expect(screen.getByRole('button', { name: 'Ubah detail' })).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Arsipkan' })).toBeOnTheScreen();
    expect(screen.queryByRole('button', { name: 'Pilih sumber acuan' })).toBeNull();
  });

  it('opens by address', async () => {
    mockApi();

    await openAddress('h-base', 'Kulkas');

    expect(await screen.findByRole('heading', { name: 'Kulkas' })).toBeOnTheScreen();
    expect(await screen.findByText('8,400 kWh')).toBeOnTheScreen();
    expect(await screen.findByText('Perangkat · Dapur · Pendingin makanan')).toBeOnTheScreen();
    expect(screen.getByText('Periode aktif: 19–25 Oktober 2026 · Asia/Jakarta')).toBeOnTheScreen();
  });
});

describe('asset detail states', () => {
  it('shows partial coverage with every gap', async () => {
    mockApi();

    await openAddress('h-learning-partial', 'Pompa Air');

    expect(await screen.findByText('Sebagian data belum tersedia · Kelengkapan data: 71,4% periode')).toBeOnTheScreen();
    expect(screen.getByText('Data 24–25 Oktober 2026 belum tersedia.')).toBeOnTheScreen();
  });

  it('shows a short gap', async () => {
    mockApi();

    await openAddress('h-learning-partial', 'Kulkas');

    expect(await screen.findByText('Data 22 Oktober 2026 14.00–16.00 belum tersedia.')).toBeOnTheScreen();
  });

  it('shows a measured zero', async () => {
    mockApi();

    await openAddress('h-zero', 'Kulkas');

    expect(await screen.findByText('0,000 kWh')).toBeOnTheScreen();
    expect(screen.getByText('Nol terukur dengan data lengkap · Kelengkapan data: 100% periode')).toBeOnTheScreen();
  });

  it('offers the data period on an empty one, and shows no zero', async () => {
    mockApi();

    await openAddress('h-base', 'Kulkas');
    await screen.findByText('8,400 kWh');
    await fireEvent.press(screen.getByRole('button', { name: 'Hari ini' }));

    expect(await screen.findByText('Belum ada energi pada periode ini')).toBeOnTheScreen();
    expect(screen.getByText(/Tidak ditampilkan sebagai 0 kWh/)).toBeOnTheScreen();
    expect(screen.queryByText('0,000 kWh')).toBeNull();
    expect(screen.getByText('Demo · Data simulasi')).toBeOnTheScreen();

    await fireEvent.press(screen.getByRole('button', { name: 'Lihat periode data' }));

    expect(await screen.findByText('8,400 kWh')).toBeOnTheScreen();
  });

  it('offers no way to the period already shown', async () => {
    mockApi({ assetSummary: () => respond(200, Recorded['h-base'].today_asset) });

    await openAddress('h-base', 'Kulkas');

    expect(await screen.findByText('Belum ada energi pada periode ini')).toBeOnTheScreen();
    expect(screen.queryByRole('button', { name: 'Lihat periode data' })).toBeNull();
  });

  it('shows each source of a conflicted asset, and no sum', async () => {
    mockApi();

    await openAddress('h-scope', 'Kulkas');

    expect(await screen.findByText('Lebih dari satu sumber untuk beban yang sama')).toBeOnTheScreen();
    expect(screen.getByText('Colokan simulasi Kulkas (sumber kedua): 1,000 kWh')).toBeOnTheScreen();
    expect(screen.getByText('Sumber demo (simulasi): 1,000 kWh')).toBeOnTheScreen();
    expect(screen.getByText(/Kulkas memiliki lebih dari satu sumber untuk beban yang sama\./)).toBeOnTheScreen();
    expect(screen.queryByText(/2,000 kWh/)).toBeNull();
    expect(screen.queryByText('Total gabungan belum dapat dihitung')).toBeNull();
    expect(screen.queryByText(/Kelengkapan data/)).toBeNull();
    expect(screen.getByText('Demo · Data simulasi')).toBeOnTheScreen();
    expect(await screen.findAllByText('Belum dipilih sebagai sumber acuan')).toHaveLength(2);
  });

  it('labels a meter by its kind', async () => {
    mockApi();

    await openAddress('h-scope', 'Meter utama');

    expect(await screen.findByText('10,000 kWh')).toBeOnTheScreen();
    expect(screen.getByText(/Cakupan pengukuran: 1 meter lokasi/)).toBeOnTheScreen();
  });

  it('says a stale source has no new data, beside its partial value', async () => {
    mockApi();

    await openAddress('h-stale-offline', 'Router');

    expect(await screen.findByText('Data belum diperbarui · Router')).toBeOnTheScreen();
    expect(screen.getByText(/Pembacaan sumber terakhir: 25 Oktober 2026 18.00/)).toBeOnTheScreen();
    expect(screen.getByText('1,620 kWh')).toBeOnTheScreen();
    expect(screen.getByText('Sebagian data belum tersedia · Kelengkapan data: 96,4% periode')).toBeOnTheScreen();
    expect(screen.getByText('Interval 1 jam. Status perangkat tidak diketahui.')).toBeOnTheScreen();
    expect(screen.queryByText(/\bmati\b/)).toBeNull();
  });

  it('notes an allocated estimate', async () => {
    const { summary } = Recorded['h-base'].details.Kulkas;
    mockApi({ assetSummary: () => respond(200, { ...summary, coverage: { ...summary.coverage, allocated_estimate: true } }) });

    await openAddress('h-base', 'Kulkas');

    expect(await screen.findByText('Sebagian interval melewati batas periode dan dibagi rata dalam intervalnya (estimasi).')).toBeOnTheScreen();
  });

  it('says so when no source exists, and keeps the provenance', async () => {
    mockApi({ asset: (url) => respond(200, { ...detailOf(url).entry.asset, bindings: [], sources: [] }) });

    await openAddress('h-base', 'Kulkas');

    expect(await screen.findByText('Belum ada sumber untuk perangkat ini.')).toBeOnTheScreen();
    expect(await screen.findByText('Demo · Data simulasi')).toBeOnTheScreen();
  });

  it('keeps imported data apart from simulated data', async () => {
    mockApi();

    await openAddress('imported', 'Kulkas', 'empty');

    expect(await screen.findByText('Data historis · Impor CSV')).toBeOnTheScreen();
    expect(screen.queryByText('Demo · Data simulasi')).toBeNull();
    expect(await screen.findByText('Impor CSV · Data historis')).toBeOnTheScreen();
    expect(screen.getByText('interval tidak diketahui · resolusi tidak diketahui')).toBeOnTheScreen();
  });
});

describe('return from detail', () => {
  it('keeps the list mounted, with its typed input, and reads nothing again', async () => {
    const fetchMock = mockApi();

    const list = await openPerangkat('h-base');
    await fireEvent.changeText(screen.getByLabelText('Tanggal mulai'), '2026-10-12');
    const before = requests(fetchMock, /\/sites\/[^/]+\/summary$/).length;
    await fireEvent.press(rowNamed(list, 'Kulkas'));
    await screen.findByRole('heading', { name: 'Kulkas' });
    await fireEvent.press(screen.getByRole('button', { name: 'Kembali' }));

    expect(await screen.findByRole('heading', { name: 'Perangkat' })).toBeOnTheScreen();
    expect(screen.getByRole('tab', { name: 'Perangkat', selected: true })).toBeOnTheScreen();
    expect(screen.getByLabelText('Tanggal mulai').props.value).toBe('2026-10-12');
    expect(requests(fetchMock, /\/sites\/[^/]+\/summary$/)).toHaveLength(before);
  });

  it('reads detail for the period chosen on the list', async () => {
    const fetchMock = mockApi();

    const list = await openPerangkat('h-base');
    await fireEvent.press(screen.getByRole('button', { name: 'Hari ini' }));
    await screen.findByText('Periode aktif: 26 Oktober 2026 · Asia/Jakarta');
    await fireEvent.press(rowNamed(list, 'Kulkas'));

    expect(await screen.findByRole('heading', { name: 'Kulkas' })).toBeOnTheScreen();
    expect(await screen.findByText('Belum ada energi pada periode ini')).toBeOnTheScreen();
    expect(screen.getByText('Periode aktif: 26 Oktober 2026 · Asia/Jakarta')).toBeOnTheScreen();
    expect(requests(fetchMock, /^\/api\/v1\/assets\/[^/]+\/summary$/).every(isToday)).toBe(true);
  });

  it('takes a period chosen on detail back to the list', async () => {
    mockApi();

    await pressRow('h-base', 'Kulkas');
    await fireEvent.press(screen.getByRole('button', { name: 'Hari ini' }));
    await screen.findByText('Belum ada energi pada periode ini');
    await fireEvent.press(screen.getByRole('button', { name: 'Kembali' }));

    expect(await screen.findByRole('heading', { name: 'Perangkat' })).toBeOnTheScreen();
    expect(await screen.findByText('Periode aktif: 26 Oktober 2026 · Asia/Jakarta')).toBeOnTheScreen();
    const list = screen.getByLabelText(LIST);
    for (const row of within(list).getAllByRole('link')) {
      expect(within(row).getByText('— kWh')).toBeOnTheScreen();
    }
  });
});

describe('Beranda to detail', () => {
  async function openBeranda(scenario: string) {
    await storeWorkspace(scenario);
    await renderRouter('./src/app', { initialUrl: '/beranda' });
    await screen.findAllByText(/Cakupan pengukuran/);
  }

  it('opens the largest asset in one press, inside the tab, and returns', async () => {
    mockApi();
    await openBeranda('h-base');
    expect(screen.getByText('8,400 kWh · 57,14%')).toBeOnTheScreen();

    await fireEvent.press(screen.getByRole('button', { name: 'Lihat perangkat terbesar' }));

    expect(await screen.findByRole('heading', { name: 'Kulkas' })).toBeOnTheScreen();
    expect(screen.getByText('Periode aktif: 19–25 Oktober 2026 · Asia/Jakarta')).toBeOnTheScreen();
    expect(screen.getByRole('tab', { name: 'Beranda', selected: true })).toBeOnTheScreen();

    await fireEvent.press(screen.getByRole('button', { name: 'Kembali' }));

    expect(await screen.findByRole('heading', { name: 'Beranda' })).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Lihat data' })).toBeOnTheScreen();
  });

  it('opens a ranking row', async () => {
    mockApi();
    await openBeranda('h-base');

    await fireEvent.press(screen.getByRole('link', { name: /^Pompa Air, / }));

    expect(await screen.findByRole('heading', { name: 'Pompa Air' })).toBeOnTheScreen();
    expect(await screen.findByText('2,100 kWh')).toBeOnTheScreen();
  });

  it.each(['h-zero', 'h-scope'])('names no largest asset in %s', async (scenario) => {
    mockApi();

    await openBeranda(scenario);

    expect(screen.queryByRole('button', { name: 'Lihat perangkat terbesar' })).toBeNull();
  });

  it.each(['h-base', 'h-learning-partial'])('gives one value and one coverage on all three screens in %s', async (scenario) => {
    mockApi();
    await openBeranda(scenario);
    await fireEvent.press(screen.getByRole('button', { name: 'Lihat data' }));
    const table = screen.getByLabelText('Energi per perangkat, 19–25 Oktober 2026, Asia/Jakarta');
    const beranda = new Map<string, { kwh: string; coverage: string }>();
    for (const name of Object.keys(Recorded[scenario].details)) {
      let row = within(table).getByText(name) as ReturnType<typeof screen.getByText> | null;
      while (row && row.props.role !== 'row') {
        row = row.parent as typeof row;
      }
      const cell = within(row!).getByText('Kelengkapan data').parent!;
      beranda.set(name, {
        kwh: String(within(row!).getByText(/kWh$/).props.children),
        coverage: String(within(cell as typeof row & object).getByText(/%$/).props.children),
      });
    }

    await fireEvent.press(screen.getByRole('tab', { name: 'Perangkat' }));
    const list = await findList();
    for (const [name, { kwh, coverage }] of beranda) {
      expect(within(rowNamed(list, name)).getByText(kwh)).toBeOnTheScreen();
      expect(within(rowNamed(list, name)).getByText(`Kelengkapan data: ${coverage} periode`)).toBeOnTheScreen();

      await fireEvent.press(rowNamed(list, name));
      await screen.findByRole('heading', { name });
      expect(await screen.findByText(kwh)).toBeOnTheScreen();
      expect(screen.getByText(`${coverage} periode`)).toBeOnTheScreen();
      await fireEvent.press(screen.getByRole('button', { name: 'Kembali' }));
      await screen.findByRole('heading', { name: 'Perangkat' });
    }
  });
});

describe('asset detail failures', () => {
  it.each([
    ['the asset summary', { assetSummary: NOT_FOUND }],
    ['the asset', { asset: NOT_FOUND }],
  ])('treats NOT_FOUND on %s as not available', async (_name, api) => {
    mockApi(api);

    await openAddress('h-base', 'Kulkas');

    expect(await screen.findByRole('heading', { name: 'Perangkat tidak ditemukan' })).toBeOnTheScreen();
    expect(screen.getByText('Perangkat ini tidak ada di ruang kerja aktif.')).toBeOnTheScreen();
    expect(screen.getByText(/ID referensi: ref_404/)).toBeOnTheScreen();
    expect(screen.queryByRole('button', { name: 'Coba lagi' })).toBeNull();
    expect(screen.getByRole('button', { name: 'Kembali' })).toBeOnTheScreen();
    expect(screen.queryByText(new RegExp(FAKE_SECRET))).toBeNull();
  });

  it('asks for nothing with no workspace, and says the asset is not here', async () => {
    const fetchMock = mockApi();

    await renderRouter('./src/app', { initialUrl: '/asset/x' });

    expect(await screen.findByRole('heading', { name: 'Perangkat tidak ditemukan' })).toBeOnTheScreen();
    expect(requests(fetchMock, /^\/api\/v1\/assets/)).toEqual([]);
  });

  it('never loads forever after a session ends', async () => {
    mockApi({ assetSummary: SESSION_ENDED });

    await openAddress('h-base', 'Kulkas');

    expect(await screen.findByRole('heading', { name: 'Perangkat tidak ditemukan' })).toBeOnTheScreen();
    expect(screen.getByText('Sesi demo sudah berakhir')).toBeOnTheScreen();
    expect(screen.queryByText('Memuat perangkat…')).toBeNull();
  });

  it('says a first read is pending', async () => {
    mockApi({ assetSummary: NEVER, asset: NEVER });

    await openAddress('h-base', 'Kulkas');

    await screen.findByText('Memuat perangkat…');
    statusRegionOf('Memuat perangkat…');
    expect(screen.getByRole('heading', { name: 'Perangkat' })).toBeOnTheScreen();
  });

  it('shows its title and sources when only the summary is pending', async () => {
    mockApi({ assetSummary: NEVER });

    await openAddress('h-base', 'Kulkas');

    expect(await screen.findByRole('heading', { name: 'Kulkas' })).toBeOnTheScreen();
    expect(screen.getByText('Memuat perangkat…')).toBeOnTheScreen();
    expect(within(screen.getByLabelText('Sumber data')).getByText('Sumber demo (simulasi)')).toBeOnTheScreen();
    expect(screen.queryByText(/^\d+,\d+ kWh$/)).toBeNull();
  });

  it('offers a retry on a first read that failed, when allowed, and recovers', async () => {
    let healthy = false;
    mockApi({ assetSummary: (url) => (healthy ? defaults.assetSummary(url, {}) : RETRYABLE()) });

    await openAddress('h-base', 'Kulkas');

    expect(await screen.findByText('Perangkat belum dapat dimuat')).toBeOnTheScreen();
    healthy = true;
    await fireEvent.press(screen.getByRole('button', { name: 'Coba lagi' }));

    expect(await screen.findByText('8,400 kWh')).toBeOnTheScreen();
    expect(screen.queryByText('Perangkat belum dapat dimuat')).toBeNull();
  });

  it('shows message and reference on a first read that may not be retried', async () => {
    mockApi({ assetSummary: SERVER_FAILED });

    await openAddress('h-base', 'Kulkas');

    expect(await screen.findByText('Perangkat belum dapat dimuat')).toBeOnTheScreen();
    expect(screen.getByText(/Permintaan belum dapat diselesaikan\. Coba lagi nanti\./)).toBeOnTheScreen();
    expect(screen.getByText(/ID referensi: ref_1/)).toBeOnTheScreen();
    expect(screen.queryByRole('button', { name: 'Coba lagi' })).toBeNull();
    expect(screen.queryByText(new RegExp(FAKE_SECRET))).toBeNull();
  });

  it('keeps numbers and selector when another period fails', async () => {
    mockApi({ assetSummary: (url) => (isToday(url) ? SERVER_FAILED() : defaults.assetSummary(url, {})) });

    await openAddress('h-base', 'Kulkas');
    await screen.findByText('8,400 kWh');
    await fireEvent.press(screen.getByRole('button', { name: 'Hari ini' }));

    expect(await screen.findByText('Data perangkat belum dapat diperbarui')).toBeOnTheScreen();
    expect(screen.getByText(KEPT)).toBeOnTheScreen();
    expect(screen.getByText('8,400 kWh')).toBeOnTheScreen();
    expect(screen.getByLabelText('Periode')).toBeOnTheScreen();
  });

  it('keeps the energy when only the sources fail, and keeps the provenance', async () => {
    mockApi({ asset: SERVER_FAILED });

    await openAddress('h-base', 'Kulkas');

    expect(await screen.findByText('Sumber data belum dapat dimuat')).toBeOnTheScreen();
    expect(screen.getByText('8,400 kWh')).toBeOnTheScreen();
    expect(screen.getByText('Demo · Data simulasi')).toBeOnTheScreen();
  });

  it('keeps the energy and reports freshness as unknown for a legacy summary', async () => {
    mockApi({ insights: SERVER_FAILED });

    await openAddress('h-base', 'Kulkas');

    expect(await screen.findByText('Belum diketahui')).toBeOnTheScreen();
    expect(screen.getByText('8,400 kWh')).toBeOnTheScreen();
  });
});


const HISTORY_PATH = /\/assets\/[^/]+\/measurements$/;
const WEEK_HIGHEST = 'Energi tercatat tertinggi: 19 Oktober 2026, 1,200 kWh.';
const WEEK_TABLE = 'Riwayat Kulkas, 19–25 Oktober 2026 · Asia/Jakarta';

function deferReply() {
  let finish!: (value: Response) => void;
  const reply = new Promise<Response>((resolve) => { finish = resolve; });
  return { reply, finish };
}

async function showHistory() {
  await fireEvent.press(await screen.findByRole('button', { name: 'Lihat riwayat' }));
}

async function showHistoryData() {
  await fireEvent.press(await screen.findByRole('button', { name: 'Lihat data' }));
}

describe('asset history disclosure', () => {
  it.each(['Beranda', 'Perangkat'])('reads lazily from %s, shows parity and goes back within that tab', async (tab) => {
    const response = deferReply();
    const fetchMock = mockApi({ history: () => response.reply });
    if (tab === 'Beranda') {
      await storeWorkspace('h-base');
      await renderRouter('./src/app', { initialUrl: '/beranda' });
      await fireEvent.press(await screen.findByRole('button', { name: 'Lihat perangkat terbesar' }));
      await screen.findByRole('heading', { name: 'Kulkas' });
    } else {
      await pressRow('h-base', 'Kulkas');
    }
    expect(requests(fetchMock, HISTORY_PATH)).toHaveLength(0);
    expect(screen.getByRole('tab', { name: tab, selected: true })).toBeOnTheScreen();

    await showHistory();
    expect(screen.getByRole('button', { name: 'Lihat riwayat', expanded: true })).toBeOnTheScreen();
    expect(statusRegionOf('Memuat riwayat…')).toBeOnTheScreen();
    expect(screen.queryByRole('img', { name: /Riwayat energi/ })).toBeNull();

    await act(async () => response.finish(respond(200, weeklyHistory())));
    expect(await screen.findByText(WEEK_HIGHEST)).toBeOnTheScreen();
    expect(screen.getByRole('img', { name: /Riwayat energi.*1,200 kWh/ })).toBeOnTheScreen();
    await showHistoryData();
    const table = screen.getByLabelText(WEEK_TABLE);
    expect(within(table).getAllByText('1,200 kWh')).toHaveLength(7);
    expect(within(table).getAllByText('100%')).toHaveLength(7);
    expect(within(table).getByText('19 Oktober 2026')).toBeOnTheScreen();
    expect(requests(fetchMock, HISTORY_PATH).map((url) => Object.fromEntries(url.searchParams))).toEqual([
      { start_date: '2026-10-19', end_date: '2026-10-25', bucket: 'day' },
    ]);

    await fireEvent.press(screen.getByRole('button', { name: 'Kembali' }));
    expect(await screen.findByRole('heading', { name: tab })).toBeOnTheScreen();
    expect(screen.getByRole('tab', { name: tab, selected: true })).toBeOnTheScreen();
  });

  it('waits for the newly selected summary and ignores a late history result from the former period', async () => {
    const newSummary = deferReply();
    const previousSummary = deferReply();
    const previousHistory = deferReply();
    const fetchMock = mockApi({
      assetSummary: (url, init) => {
        if (url.searchParams.get('preset') === 'this_week') return previousSummary.reply;
        return isToday(url) ? newSummary.reply : defaults.assetSummary(url, init);
      },
      history: (url) => url.searchParams.get('bucket') === 'day' ? previousHistory.reply : respond(200, hourlyHistory()),
    });
    await openAddress('h-base', 'Kulkas');
    await showHistory();
    await waitFor(() => expect(requests(fetchMock, HISTORY_PATH)).toHaveLength(1));

    await fireEvent.press(screen.getByRole('button', { name: 'Minggu ini' }));
    await waitFor(() => expect(requests(fetchMock, /\/assets\/[^/]+\/summary$/)
      .some((url) => url.searchParams.get('preset') === 'this_week')).toBe(true));
    await fireEvent.press(screen.getByRole('button', { name: 'Hari ini' }));
    await act(async () => previousSummary.finish(respond(200, {
      ...Recorded['h-base'].details.Kulkas.summary, window: mondayWindow,
    })));
    expect(statusRegionOf('Menunggu periode terpilih…')).toBeOnTheScreen();
    expect(requests(fetchMock, HISTORY_PATH)).toHaveLength(1);

    await act(async () => newSummary.finish(respond(200, {
      ...Recorded['h-base'].details.Kulkas.summary, window: mondayWindow,
    })));
    expect(await screen.findByText(/Energi tercatat tertinggi: 19 Oktober 2026 00.00/)).toBeOnTheScreen();

    await act(async () => previousHistory.finish(respond(200, weeklyHistory())));
    await waitFor(() => expect(requests(fetchMock, HISTORY_PATH).map((url) => url.searchParams.get('bucket'))).toEqual(['day', 'hour']));
    expect(screen.queryByText(WEEK_HIGHEST)).toBeNull();
    await showHistoryData();
    const table = screen.getByLabelText('Riwayat Kulkas, 19 Oktober 2026 · Asia/Jakarta');
    expect(within(table).getAllByText('1,200 kWh')).toHaveLength(24);
    expect(within(table).getByText(/19 Oktober 2026 01.00.*19 Oktober 2026 02.00/)).toBeOnTheScreen();
  });

  it('keeps confirmed History when an explicit summary echoes a different date range', async () => {
    const fetchMock = mockApi();
    await openAddress('h-base', 'Kulkas');
    await showHistory();
    expect(await screen.findByText(WEEK_HIGHEST)).toBeOnTheScreen();

    await fireEvent.changeText(screen.getByLabelText('Tanggal mulai'), '2026-10-22');
    await fireEvent.changeText(screen.getByLabelText('Tanggal selesai'), '2026-10-22');
    await fireEvent.press(screen.getByRole('button', { name: 'Terapkan' }));

    expect(await screen.findByText('Riwayat belum dapat dimuat')).toBeOnTheScreen();
    expect(screen.getByText(/pembacaan terakhir yang terkonfirmasi/)).toBeOnTheScreen();
    expect(screen.getByText(WEEK_HIGHEST)).toBeOnTheScreen();
    expect(requests(fetchMock, HISTORY_PATH)).toHaveLength(1);
  });

  it('keeps confirmed context when a background refresh of the same History fails', async () => {
    const old = weeklyHistory();
    old.window = { ...weekWindow, is_current: true, effective_end: '2026-10-25T10:00:00Z' };
    old.highest_bucket = { start: old.buckets.at(-1)!.start };
    let historyCalls = 0;
    const fetchMock = mockApi({
      history: () => historyCalls++ === 0 ? respond(200, old) : SERVER_FAILED(),
    });
    await openAddress('h-base', 'Kulkas');
    await showHistory();
    await showHistoryData();
    const context = '19–25 Oktober 2026 · Asia/Jakarta · hingga 25 Oktober 2026 17.00 (UTC+07:00)';
    const clock = jest.spyOn(Date, 'now').mockReturnValue(Date.now() + 31_000);
    try {
      await act(async () => {
        focusManager.setFocused(false);
        focusManager.setFocused(true);
      });
      await screen.findByText('Riwayat belum dapat dimuat');
      expect(screen.getByText(/pembacaan terakhir yang terkonfirmasi/)).toBeOnTheScreen();
      expect(screen.getByLabelText(`Riwayat Kulkas, ${context}`)).toBeOnTheScreen();
      expect(requests(fetchMock, HISTORY_PATH)).toHaveLength(2);
    } finally {
      focusManager.setFocused(undefined);
      clock.mockRestore();
    }
  });

  it('keeps the prior period, timezone and cutoff during a retry wait and terminal failure', async () => {
    const old = weeklyHistory();
    old.window = { ...weekWindow, is_current: true, effective_end: '2026-10-25T10:00:00Z' };
    old.highest_bucket = { start: old.buckets.at(-1)!.start };
    const nextSummary = deferReply();
    let hourCalls = 0;
    const fetchMock = mockApi({
      assetSummary: (url, init) => isToday(url) ? nextSummary.reply : defaults.assetSummary(url, init),
      history: (url) => {
        if (url.searchParams.get('bucket') === 'day') return respond(200, old);
        hourCalls += 1;
        return failure(503, 'DATABASE_UNAVAILABLE', { retryable: true, retry_after_seconds: 1, max_attempts: 2 }, 'ref-history');
      },
    });
    await openAddress('h-base', 'Kulkas');
    await showHistory();
    const context = '19–25 Oktober 2026 · Asia/Jakarta · hingga 25 Oktober 2026 17.00 (UTC+07:00)';
    const highest = 'Energi tercatat tertinggi: 25 Oktober 2026, 1,200 kWh hingga 25 Oktober 2026 17.00 (UTC+07:00).';
    expect(await screen.findByText(highest)).toBeOnTheScreen();
    await showHistoryData();
    expect(screen.getByLabelText(`Riwayat Kulkas, ${context}`)).toBeOnTheScreen();

    await fireEvent.press(screen.getByRole('button', { name: 'Hari ini' }));
    expect(statusRegionOf('Menunggu periode terpilih…')).toBeOnTheScreen();
    expect(screen.getByText(highest)).toBeOnTheScreen();

    await act(async () => nextSummary.finish(respond(200, {
      ...Recorded['h-base'].details.Kulkas.summary, window: mondayWindow,
    })));
    const waiting = await screen.findByText('Menunggu percobaan otomatis riwayat…');
    expect(statusRegionOf(String(waiting.props.children))).toBeOnTheScreen();
    expect(screen.getByText(/dalam 1 detik/)).toBeOnTheScreen();
    expect(screen.queryByRole('button', { name: 'Coba lagi' })).toBeNull();
    expect(hourCalls).toBe(1);

    const stopped = await screen.findByText('Riwayat belum dapat dimuat', {}, { timeout: 3000 });
    expect(statusRegionOf(String(stopped.props.children))).toBeOnTheScreen();
    expect(screen.getByText(/Percobaan riwayat telah dihentikan/)).toBeOnTheScreen();
    expect(screen.getByText(/ID referensi: ref-history/)).toBeOnTheScreen();
    expect(screen.queryByText(new RegExp(FAKE_SECRET))).toBeNull();
    expect(screen.queryByRole('button', { name: 'Coba lagi' })).toBeNull();
    expect(screen.getByText(highest)).toBeOnTheScreen();
    expect(screen.getByLabelText(`Riwayat Kulkas, ${context}`)).toBeOnTheScreen();

    await showHistory();
    await showHistory();
    expect(await screen.findByText('Riwayat belum dapat dimuat')).toBeOnTheScreen();
    expect(requests(fetchMock, HISTORY_PATH)).toHaveLength(3);
  });
});

describe('history bucket states', () => {
  it('keeps measured, partial, missing, future and unavailable distinct and ignores comparison data', async () => {
    const history = hourlyHistory();
    history.window = { ...history.window, is_current: true, effective_end: '2026-10-19T02:30:00Z' };
    history.buckets = history.buckets.map((bucket, index) => {
      if (index >= 10) return { ...bucket, state: 'future', energy_kwh: null, coverage: null };
      return {
        ...bucket,
        ...([
          { energy_kwh: '1.200', comparison_kwh: '0.200' },
          { energy_kwh: '0.000' },
          { state: 'partial', energy_kwh: '1.300', coverage: '0.916' },
          { state: 'partial', energy_kwh: '0.001', coverage: '0.010' },
          { state: 'partial', energy_kwh: '0.000', coverage: '0.000' },
          { state: 'missing', energy_kwh: null, coverage: '0.000' },
          { state: 'unavailable', energy_kwh: null, coverage: null, unavailable_reason: 'source_conflict' },
          { state: 'unavailable', energy_kwh: null, coverage: null, unavailable_reason: 'insufficient_resolution' },
          { state: 'unavailable', energy_kwh: null, coverage: null, unavailable_reason: FAKE_SECRET },
          { energy_kwh: '1.200' },
        ][index]),
      };
    });
    history.highest_bucket = { start: history.buckets[9].start };
    mockApi({
      assetSummary: () => respond(200, { ...Recorded['h-base'].details.Kulkas.summary, window: mondayWindow }),
      history: () => respond(200, history),
    });
    await openAddress('h-base', 'Kulkas');
    await showHistory();

    const cutoff = 'hingga 19 Oktober 2026 09.30 (UTC+07:00)';
    expect(await screen.findByText(`Energi tercatat tertinggi: 19 Oktober 2026 09.00 (UTC+07:00), 1,200 kWh ${cutoff}.`)).toBeOnTheScreen();
    expect(screen.getByText(/^Tidak ada data: 19 Oktober 2026 05.00/)).toBeOnTheScreen();
    await showHistoryData();
    const table = screen.getByLabelText(`Riwayat Kulkas, 19 Oktober 2026 · Asia/Jakarta · ${cutoff}`);
    function rowAt(hour: string) {
      let row = within(table).getByText(new RegExp(`^19 Oktober 2026 ${hour}\\.00.* – `));
      while (row.props.role !== 'row') row = row.parent as typeof row;
      return within(row);
    }

    expect(rowAt('00').getByText('1,200 kWh')).toBeOnTheScreen();
    expect(rowAt('00').getByText('Terukur')).toBeOnTheScreen();
    expect(rowAt('01').getByText('0,000 kWh')).toBeOnTheScreen();
    expect(rowAt('01').getByText('Terukur')).toBeOnTheScreen();
    expect(rowAt('02').getByText('1,300 kWh')).toBeOnTheScreen();
    expect(rowAt('02').getByText('91,6%')).toBeOnTheScreen();
    expect(rowAt('03').getByText('0,001 kWh')).toBeOnTheScreen();
    expect(rowAt('03').getByText('1%')).toBeOnTheScreen();
    expect(rowAt('04').getByText('0,000 kWh')).toBeOnTheScreen();
    expect(rowAt('04').getByText('0%')).toBeOnTheScreen();
    expect(rowAt('04').getByText(/^Data sebagian\./)).toBeOnTheScreen();
    expect(rowAt('05').getByText('Tidak ada data')).toBeOnTheScreen();
    expect(rowAt('06').getByText(/^Sumber data bertentangan/)).toBeOnTheScreen();
    expect(rowAt('07').getByText(/^Resolusi pengukuran belum memadai/)).toBeOnTheScreen();
    expect(rowAt('08').getByText('Data tidak tersedia untuk interval ini.')).toBeOnTheScreen();
    expect(rowAt('09').getByText(`100% ${cutoff}`)).toBeOnTheScreen();
    expect(rowAt('10').getByText('Belum terjadi')).toBeOnTheScreen();
    expect(within(table).queryByText('0,200 kWh')).toBeNull();
    expect(screen.queryByText(new RegExp(FAKE_SECRET))).toBeNull();
  });

  it.each([
    ['missing', 'Tidak ada data'],
    ['future', 'Belum terjadi'],
    ['unavailable', 'Resolusi pengukuran belum memadai untuk interval ini.'],
  ])('replaces retained numeric history with a confirmed all-%s series', async (state, quality) => {
    const later = hourlyHistory();
    later.highest_bucket = null;
    if (state === 'future') later.window = { ...later.window, effective_end: later.window.start, is_current: true };
    later.buckets = later.buckets.map((bucket) => ({
      ...bucket, state, energy_kwh: null, coverage: state === 'missing' ? '0.000' : null,
      unavailable_reason: state === 'unavailable' ? 'insufficient_resolution' : null,
    }));
    const response = deferReply();
    mockApi({
      assetSummary: (url, init) => isToday(url)
        ? respond(200, { ...Recorded['h-base'].details.Kulkas.summary, window: mondayWindow })
        : defaults.assetSummary(url, init),
      history: (url) => url.searchParams.get('bucket') === 'hour' ? response.reply : respond(200, weeklyHistory()),
    });
    await openAddress('h-base', 'Kulkas');
    await showHistory();
    expect(await screen.findByText(WEEK_HIGHEST)).toBeOnTheScreen();
    await showHistoryData();

    await fireEvent.press(screen.getByRole('button', { name: 'Hari ini' }));
    expect(screen.getByText(WEEK_HIGHEST)).toBeOnTheScreen();
    await act(async () => response.finish(respond(200, later)));
    expect(await screen.findByText('Belum ada interval terukur lengkap untuk menentukan energi tertinggi.')).toBeOnTheScreen();
    expect(screen.queryByText(WEEK_HIGHEST)).toBeNull();
    expect(screen.queryByText(/pembacaan terakhir yang terkonfirmasi/)).toBeNull();
    const table = screen.getByLabelText(/^Riwayat Kulkas, 19 Oktober 2026 · Asia\/Jakarta/);
    expect(within(table).getAllByText(quality)).toHaveLength(24);
    expect(within(table).queryByText(/kWh/)).toBeNull();
  });

  it('shows an explicit state when the service confirms an empty series', async () => {
    mockApi({ history: () => respond(200, { ...weeklyHistory(), highest_bucket: null, buckets: [] }) });
    await openAddress('h-base', 'Kulkas');
    await showHistory();

    expect(await screen.findByText('Riwayat belum memiliki interval untuk periode ini.')).toBeOnTheScreen();
    expect(screen.queryByRole('img', { name: /Riwayat energi/ })).toBeNull();
  });
});

describe('asset edit and archive', () => {
  it('keeps the S04 name and detail confirmed until a PATCH acknowledgment', async () => {
    let name = 'Kulkas';
    let finish!: () => void;
    const fetchMock = mockApi({
      asset: (url, init) => {
        const original = detailOf(url).entry.asset;
        if (init.method === 'PATCH') {
          return new Promise<Response>((resolve) => {
            finish = () => {
              name = JSON.parse(String(init.body)).name;
              resolve(respond(200, { ...original, name }));
            };
          });
        }
        return respond(200, { ...original, name });
      },
      assets: (url) => {
        const page = scenarioOf(url).assets;
        return respond(200, { ...page, items: page.items.map((item) => item.name === 'Kulkas' ? { ...item, name } : item) });
      },
    });
    const list = await openPerangkat('h-base');
    await fireEvent.press(rowNamed(list, 'Kulkas'));
    await fireEvent.press(await screen.findByRole('button', { name: 'Ubah detail' }));
    await fireEvent.changeText(screen.getByLabelText('Nama perangkat'), ' Kulkas baru ');
    await fireEvent.press(screen.getByRole('button', { name: 'Simpan' }));
    expect(screen.getByRole('heading', { name: 'Kulkas', includeHiddenElements: true })).toBeOnTheScreen();
    await act(() => finish());
    expect(await screen.findByRole('heading', { name: 'Kulkas baru' })).toBeOnTheScreen();
    expect(screen.getByText('Sumber data')).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('button', { name: 'Kembali' }));
    expect(await within(await findList()).findByRole('link', { name: /^Kulkas baru,/ })).toBeOnTheScreen();
    expect(fetchMock.mock.calls.filter(([, init]) => init?.method === 'PATCH')).toHaveLength(1);
  });

  it('retains an explicitly rejected draft on sheet dismissal and reopen', async () => {
    mockApi({
      asset: (url, init) => init.method === 'PATCH'
        ? failure(422, 'VALIDATION_FAILED', { retryable: false }, 'ref-rename') : defaults.asset(url, init),
    });
    await fireEvent.press(rowNamed(await openPerangkat('h-base'), 'Kulkas'));
    await fireEvent.press(await screen.findByRole('button', { name: 'Ubah detail' }));
    await fireEvent.changeText(screen.getByLabelText('Nama perangkat'), 'Draf disimpan di lembar');
    await fireEvent.press(screen.getByRole('button', { name: 'Simpan' }));
    expect(await screen.findByText(/ref-rename/)).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('button', { name: 'Batal' }));
    expect(await screen.findByRole('heading', { name: 'Kulkas' })).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('button', { name: 'Ubah detail' }));
    expect(screen.getByLabelText('Nama perangkat').props.value).toBe('Draf disimpan di lembar');
    await fireEvent.press(screen.getByRole('button', { name: 'Buang draf' }));
    await fireEvent.press(screen.getByRole('button', { name: 'Ubah detail' }));
    expect(screen.getByLabelText('Nama perangkat').props.value).toBe('Kulkas');
  });

  it('keeps archived access when the active summary fails', async () => {
    const entry = Recorded['h-base'].details.Kulkas;
    mockApi({
      summary: SERVER_FAILED,
      assets: (url) => respond(200, {
        items: url.searchParams.get('include_archived') === 'true' ? [{ ...entry.asset, archived: true }] : [],
        next_cursor: null,
      }),
      asset: () => respond(200, { ...entry.asset, archived: true }),
    });
    await storeWorkspace('h-base');
    await renderRouter('./src/app', { initialUrl: '/perangkat' });
    await fireEvent.press(await screen.findByRole('button', { name: 'Diarsipkan' }));
    await fireEvent.press(await screen.findByRole('link', { name: /^Kulkas,/ }));
    expect(await screen.findByRole('button', { name: 'Pulihkan' })).toBeOnTheScreen();
    expect(await screen.findByRole('button', { name: 'Lihat riwayat' })).toBeOnTheScreen();
  });

  it('takes S07 learning through the device chooser and returns through the Saran tab', async () => {
    mockApi({
      insights: (url) => respond(200, {
        window: scenarioOf(url).summary.window, observations: [], notices: [], learning_count: 4, comparable_count: 0,
      }),
    });
    await storeWorkspace('h-base');
    await renderRouter('./src/app', { initialUrl: '/saran' });
    await fireEvent.press(await screen.findByRole('button', { name: 'Tentang riwayat perangkat' }));
    expect(await screen.findByRole('heading', { name: 'Riwayat perangkat' })).toBeOnTheScreen();
    await fireEvent.press(rowNamed(await findList(), 'Kulkas'));
    await fireEvent.press(await screen.findByRole('button', { name: 'Lihat riwayat' }));
    await fireEvent.press(await screen.findByRole('button', { name: 'Lihat data' }));
    expect(await screen.findByLabelText(/Riwayat Kulkas, 19–25 Oktober 2026/)).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('button', { name: 'Kembali' }));
    expect(await screen.findByRole('heading', { name: 'Riwayat perangkat' })).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('button', { name: 'Kembali' }));
    expect(await screen.findByRole('heading', { name: 'Saran' })).toBeOnTheScreen();
    expect(screen.getByText('19–25 Oktober 2026 · Asia/Jakarta')).toBeOnTheScreen();
  });
});

it('changes active/archive membership on acknowledgment while preserving previous service scope', async () => {
  let archived = false;
  let currentSummary = Recorded['h-base'].summary;
  let refreshHeld = false;
  let finishRefresh!: (response: Response) => void;
  const id = assetIdOf('h-base', 'Kulkas');
  const fetchMock = mockApi({
    summary: () => refreshHeld ? new Promise<Response>((resolve) => { finishRefresh = resolve; }) : respond(200, currentSummary),
    assets: (url) => {
      const page = Recorded['h-base'].assets;
      const items = page.items.map((asset) => asset.id === id ? { ...asset, archived } : asset);
      return respond(200, { ...page, items: url.searchParams.has('include_archived') ? items : items.filter((asset) => asset.id !== id || !archived) });
    },
    asset: (url, init) => {
      if (init.method === 'PATCH') {
        archived = JSON.parse(String(init.body)).archived;
        refreshHeld = true;
      }
      return respond(200, { ...detailOf(url).entry.asset, archived });
    },
  });
  await fireEvent.press(rowNamed(await openPerangkat('h-base'), 'Kulkas'));
  await fireEvent.press(await screen.findByRole('button', { name: 'Arsipkan' }));
  const dialog = screen.getByLabelText('Arsipkan Kulkas?');
  await fireEvent.press(within(dialog).getByRole('button', { name: 'Batal' }));
  expect(fetchMock.mock.calls.filter(([, init]) => init?.method === 'PATCH')).toHaveLength(0);

  await fireEvent.press(screen.getByRole('button', { name: 'Arsipkan' }));
  await fireEvent.press(within(screen.getByLabelText('Arsipkan Kulkas?')).getByRole('button', { name: 'Arsipkan' }));
  expect(await screen.findByRole('button', { name: 'Pulihkan' })).toBeOnTheScreen();
  await fireEvent.press(screen.getByRole('button', { name: 'Kembali' }));
  expect(within(await findList()).queryByRole('link', { name: /^Kulkas,/ })).toBeNull();
  expect(await screen.findByText('Ringkasan masih memakai cakupan sebelumnya')).toBeOnTheScreen();
  expect(screen.getByText('Cakupan pengukuran: 4 perangkat')).toBeOnTheScreen();
  currentSummary = { ...currentSummary, assets: currentSummary.assets.filter((row) => row.asset_id !== id) };
  refreshHeld = false;
  await act(() => finishRefresh(respond(200, currentSummary)));
  await waitFor(() => expect(screen.queryByText('Ringkasan masih memakai cakupan sebelumnya')).toBeNull());
  await fireEvent.press(screen.getByRole('button', { name: 'Diarsipkan' }));
  await fireEvent.press(await within(await screen.findByLabelText('Perangkat diarsipkan')).findByRole('link', { name: /^Kulkas,/ }));

  await fireEvent.press(await screen.findByRole('button', { name: 'Pulihkan' }));
  await fireEvent.press(within(screen.getByLabelText('Pulihkan Kulkas?')).getByRole('button', { name: 'Pulihkan' }));
  expect(await screen.findByRole('button', { name: 'Arsipkan' })).toBeOnTheScreen();
  await fireEvent.press(screen.getByRole('button', { name: 'Kembali' }));
  const unranked = await screen.findByLabelText('Perangkat aktif tanpa ringkasan');
  const restored = within(unranked).getByRole('link', { name: /^Kulkas,/ });
  expect(within(restored).getByText('— kWh')).toBeOnTheScreen();
  expect(screen.queryByLabelText('Perangkat diarsipkan')).toBeNull();
  expect(fetchMock.mock.calls.filter(([, init]) => init?.method === 'PATCH').map(([, init]) => init?.body))
    .toEqual([JSON.stringify({ archived: true }), JSON.stringify({ archived: false })]);
});

it('keeps acknowledged detail and history from S03 when the summary refresh fails', async () => {
  let changed = false;
  mockApi({
    asset: (url, init) => {
      if (init.method === 'PATCH') {
        changed = true;
        return respond(200, { ...detailOf(url).entry.asset, name: 'Kulkas S03' });
      }
      return defaults.asset(url, init);
    },
    assetSummary: (url, init) => changed ? SERVER_FAILED() : defaults.assetSummary(url, init),
  });
  await storeWorkspace('h-base');
  await renderRouter('./src/app', { initialUrl: '/beranda' });
  await fireEvent.press(await screen.findByRole('button', { name: 'Lihat perangkat terbesar' }));
  await fireEvent.press(await screen.findByRole('button', { name: 'Lihat riwayat' }));
  await screen.findByRole('button', { name: 'Lihat data' });
  await fireEvent.press(await screen.findByRole('button', { name: 'Ubah detail' }));
  await fireEvent.changeText(screen.getByLabelText('Nama perangkat'), 'Kulkas S03');
  await fireEvent.press(screen.getByRole('button', { name: 'Simpan' }));
  expect(await screen.findByRole('heading', { name: 'Kulkas S03' })).toBeOnTheScreen();
  expect(await screen.findByText('Data perangkat belum dapat diperbarui')).toBeOnTheScreen();
  expect(screen.getByRole('button', { name: 'Lihat data' })).toBeOnTheScreen();
  expect(screen.getByText('Sumber demo (simulasi)')).toBeOnTheScreen();
  expect(screen.getByText('8,400 kWh')).toBeOnTheScreen();
});

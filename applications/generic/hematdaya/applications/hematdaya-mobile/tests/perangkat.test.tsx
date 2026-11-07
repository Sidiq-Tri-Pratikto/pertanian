// Recorded on 2026-11-07 from the merged hematdaya-api at 6563a2f (Alembic head 0009), by real demo sessions.
import { act, fireEvent, renderRouter, screen, waitFor, within } from 'expo-router/testing-library';
import * as SecureStore from 'expo-secure-store';

import recorded from './fixtures/assets.json';

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
type Api = { summary?: Handler; assets?: Handler; insights?: Handler; asset?: Handler; assetSummary?: Handler; create?: Handler };

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
  await SecureStore.setItemAsync(
    'hematdaya.workspace.v1',
    JSON.stringify({
      token: `hdd_v1_${scenario}`,
      siteId: `site-${scenario}`,
      scenarioId,
      expiresAt: '2099-01-01T00:00:00Z',
      initialPeriod: Recorded[scenario].initial_period,
    }),
  );
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

  it('keeps the rows when the freshness check fails, and says so', async () => {
    mockApi({ insights: SERVER_FAILED });

    const list = await openPerangkat('h-stale-offline');

    expect(await screen.findByText('Status pembaruan sumber belum dapat diperiksa.')).toBeOnTheScreen();
    expect(within(rowNamed(list, 'Router')).getByText('1,620 kWh')).toBeOnTheScreen();
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
    for (const absent of ['Lihat riwayat', 'Ubah detail', 'Arsipkan', 'Pilih sumber acuan']) {
      expect(screen.queryByRole('button', { name: absent })).toBeNull();
    }
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

    const { body, title } = Recorded['h-stale-offline'].notices[0];
    expect(await screen.findByText(title)).toBeOnTheScreen();
    expect(title).toBe('Data belum diperbarui · Router');
    expect(screen.getByText(body)).toBeOnTheScreen();
    expect(screen.getByText('1,620 kWh')).toBeOnTheScreen();
    expect(screen.getByText('Sebagian data belum tersedia · Kelengkapan data: 96,4% periode')).toBeOnTheScreen();
    expect(screen.getAllByText(/\bmati\b/)).toHaveLength(1);
    expect(screen.getByText(/Ini bukan tanda perangkat mati\./)).toBeOnTheScreen();
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
    expect(screen.getByText('Demo · Data simulasi')).toBeOnTheScreen();
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

  it('keeps everything when only the freshness check fails', async () => {
    mockApi({ insights: SERVER_FAILED });

    await openAddress('h-base', 'Kulkas');

    expect(await screen.findByText('Status pembaruan sumber belum dapat diperiksa.')).toBeOnTheScreen();
    expect(screen.getByText('8,400 kWh')).toBeOnTheScreen();
  });
});

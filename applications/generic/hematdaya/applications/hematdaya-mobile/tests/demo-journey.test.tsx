import AsyncStorage from '@react-native-async-storage/async-storage';
import { act, fireEvent, renderRouter, screen, waitFor, within } from 'expo-router/testing-library';
import * as SecureStore from 'expo-secure-store';
import { setLocale } from '@/features/localization/locale';
import { seedConfirmedWorkspace } from './fixtures/workspaces';

import householdGolden from '../../../contracts/golden/summary-h-week.json';
import scopeGolden from '../../../contracts/golden/summary-scope.json';

const householdWeek = { ...householdGolden, revision: 1 };
const scopeDay = { ...scopeGolden, revision: 1 };

const manifest = {
  schema_version: 1,
  source_release: '0.1.0',
  composition: { id: 'core-plus-optional', version: 1 },
  capabilities: [{ id: 'core', optional: false, status: 'available' }],
  adapters: [{ id: 'demo', status: 'simulated' }],
  policies: [{ id: 'baseline', version: 1 }],
};
const LAST_WEEK = { preset: 'last_7_days', start_date: '2026-10-19', end_date: '2026-10-25' };

function respond(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status });
}

function session(scenario: string) {
  return {
    token: `hdd_v1_${scenario}`,
    site_id: `site-${scenario}`,
    scenario_id: scenario,
    expires_at: '2099-01-01T00:00:00Z',
    initial_period: LAST_WEEK,
  };
}

const emptySummary = {
  ...householdWeek,
  source_freshness: [],
  energy_kwh: null,
  energy_unavailable_reason: 'no_data',
  assets: [],
  scope: { valid: true, issues: [], included: [], excluded: [] },
  coverage: { minimum: null, concurrent: null, allocated_estimate: false },
  latest_measurement_at: null,
  origins: [],
};

const todayOnMonday = {
  ...householdWeek,
  window: { ...householdWeek.window, start: '2026-10-25T17:00:00Z', end: '2026-10-26T17:00:00Z', effective_end: '2026-10-25T17:00:00Z', start_date: '2026-10-26', end_date: '2026-10-26', is_current: true },
  energy_kwh: null,
  energy_unavailable_reason: 'no_data',
  coverage: { minimum: null, concurrent: null, allocated_estimate: false },
  assets: householdWeek.assets.map((asset) => ({ ...asset, energy_kwh: null, energy_unavailable_reason: 'no_data', share_percent: null, coverage: null })),
};

const currentDay = {
  ...householdWeek,
  window: { ...householdWeek.window, start: '2026-10-20T17:00:00Z', end: '2026-10-21T17:00:00Z', effective_end: '2026-10-21T05:00:00Z', start_date: '2026-10-21', end_date: '2026-10-21', is_current: true },
  energy_kwh: '0.870',
};

const partialWeek = {
  ...householdWeek,
  coverage: { minimum: '0.714', concurrent: '0.702', allocated_estimate: false },
  assets: householdWeek.assets.map((asset) =>
    asset.name === 'Pompa Air'
      ? { ...asset, coverage: '0.714', gaps: [{ start: '2026-10-23T17:00:00Z', end: '2026-10-25T17:00:00Z' }] }
      : asset,
  ),
};

const zeroWeek = {
  ...householdWeek,
  energy_kwh: '0.000',
  assets: householdWeek.assets.map((asset) => ({ ...asset, energy_kwh: '0.000', share_percent: null })),
};

type Handlers = {
  create?: (init: RequestInit) => Response | Promise<Response>;
  summary?: (url: URL) => Response | Promise<Response>;
};

function mockApi({ create, summary }: Handlers) {
  return jest.spyOn(globalThis, 'fetch').mockImplementation(async (input, init = {}) => {
    const url = new URL(String(input));
    if (url.pathname === '/api/v1/demo/sessions') {
      return create ? create(init) : respond(201, session(JSON.parse(String(init.body)).scenario_id));
    }
    if (url.pathname.endsWith('/summary')) {
      return summary ? summary(url) : respond(200, householdWeek);
    }
    if (url.pathname.endsWith('/insights')) {
      return respond(200, { window: householdWeek.window, observations: [], notices: [], learning_count: 0, comparable_count: 0 });
    }
    return respond(200, manifest);
  });
}

function createCalls(fetchMock: jest.SpyInstance) {
  return fetchMock.mock.calls
    .filter(([input]) => String(input).includes('/demo/sessions'))
    .map(([, init]) => ({ headers: (init as RequestInit).headers as Record<string, string>, body: JSON.parse(String((init as RequestInit).body)) }));
}

async function storeWorkspace(token = 'hdd_v1_stored') {
  await seedConfirmedWorkspace({ token, siteId: 'site-stored', scenarioId: 'h-base', expiresAt: '2099-01-01T00:00:00Z', initialPeriod: LAST_WEEK });
}

async function openDemo() {
  await renderRouter('./src/app', { initialUrl: '/' });
  await fireEvent.press(await screen.findByRole('button', { name: 'Coba demo' }));
  expect(await screen.findByRole('heading', { name: 'Pilih data demo' })).toBeOnTheScreen();
}

describe('demo onboarding', () => {
  afterEach(() => jest.restoreAllMocks());

  it('opens a populated household demo in two taps with no text entry', async () => {
    const fetchMock = mockApi({});

    await openDemo();
    expect(screen.getByRole('radio', { name: 'Rumah tangga', checked: true })).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('button', { name: 'Buka demo' }));

    expect(await screen.findByText('14,700 kWh')).toBeOnTheScreen();
    expect(screen.getByText('Demo · Data simulasi')).toBeOnTheScreen();
    expect(screen.getAllByText('Kelengkapan data: 100% periode').length).toBeGreaterThan(0);
    expect(screen.getByText('Periode aktif: 19–25 Oktober 2026 · Asia/Jakarta')).toBeOnTheScreen();
    expect(screen.getByText(/19–25 Oktober 2026 · Cakupan pengukuran: 4 perangkat/)).toBeOnTheScreen();
    expect(screen.getByText('8,400 kWh · 57,14%')).toBeOnTheScreen();
    expect(createCalls(fetchMock)).toHaveLength(1);
    const [call] = createCalls(fetchMock);
    expect(call.body).toEqual({ scenario_id: 'h-base' });
    expect(call.headers['Idempotency-Key'].length).toBeGreaterThanOrEqual(22);
    expect(call.headers['X-Demo-Replay-Proof'].length).toBeGreaterThanOrEqual(43);
    const summaryCall = fetchMock.mock.calls.find(([input]) => String(input).includes('/summary'))!;
    expect(String(summaryCall[0])).toContain('/api/v1/sites/site-h-base/summary?preset=last_7_days');
    expect(((summaryCall[1] as RequestInit).headers as Record<string, string>).Authorization).toBe('Bearer hdd_v1_h-base');
  });

  it('keeps Insights reads and workspace identity stable when the locale changes', async () => {
    await storeWorkspace();
    const fetchMock = mockApi({});
    await renderRouter('./src/app', { initialUrl: '/beranda' });
    await screen.findByText('14,700 kWh');
    const listReads = () => fetchMock.mock.calls.filter(([input]) => String(input).includes('/insights')).length;
    await waitFor(() => expect(listReads()).toBeGreaterThan(0));
    const before = listReads();
    try {
      await act(() => setLocale('en'));
      expect(listReads()).toBe(before);
      expect(createCalls(fetchMock)).toHaveLength(0);
      expect(screen.getByText('14.700 kWh')).toBeOnTheScreen();
    } finally {
      await act(() => setLocale('id'));
    }
  });

  it('opens the industrial demo after selecting Industri', async () => {
    const fetchMock = mockApi({ summary: () => respond(200, householdWeek) });
    await openDemo();
    await fireEvent.press(screen.getByRole('radio', { name: 'Industri' }));
    expect(screen.getByRole('radio', { name: 'Industri', checked: true })).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('button', { name: 'Buka demo' }));

    await screen.findByText('14,700 kWh');
    expect(createCalls(fetchMock).map((call) => call.body)).toEqual([{ scenario_id: 'i-base' }]);
  });

  it('cancelling creates nothing', async () => {
    const fetchMock = mockApi({});

    await openDemo();
    await fireEvent.press(screen.getByRole('button', { name: 'Batal' }));

    await waitFor(() => expect(screen.queryByRole('heading', { name: 'Pilih data demo' })).toBeNull());
    expect(createCalls(fetchMock)).toHaveLength(0);
    expect(screen.getByRole('heading', { name: 'Selamat datang' })).toBeOnTheScreen();
  });

  it('keeps the sheet open on failure and retries the same request', async () => {
    let attempts = 0;
    const fetchMock = mockApi({
      create: (init) => {
        attempts += 1;
        if (attempts === 1) {
          throw new TypeError('Network request failed');
        }
        return respond(201, session(JSON.parse(String(init.body)).scenario_id));
      },
    });

    await openDemo();
    await fireEvent.press(screen.getByRole('button', { name: 'Buka demo' }));
    expect(await screen.findByText('Layanan belum dapat dihubungi. Periksa koneksi Anda lalu coba lagi.')).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('button', { name: 'Coba lagi' }));

    expect(await screen.findByText('14,700 kWh')).toBeOnTheScreen();
    const [first, second] = createCalls(fetchMock);
    expect(second.headers['Idempotency-Key']).toBe(first.headers['Idempotency-Key']);
    expect(second.headers['X-Demo-Replay-Proof']).toBe(first.headers['X-Demo-Replay-Proof']);
    expect(second.body).toEqual(first.body);
  });

  it('never starts silently after a refused replay', async () => {
    let attempts = 0;
    const fetchMock = mockApi({
      create: (init) => {
        attempts += 1;
        return attempts === 1
          ? respond(409, {
              error: {
                code: 'CONFLICT',
                message: 'Permintaan demo ini sudah dipakai untuk sesi lain atau sudah kedaluwarsa. Mulai sesi demo baru.',
                request_id: 'ref_conflict',
                recovery: { retryable: false },
              },
            })
          : respond(201, session(JSON.parse(String(init.body)).scenario_id));
      },
    });

    await openDemo();
    await fireEvent.press(screen.getByRole('button', { name: 'Buka demo' }));
    expect(await screen.findByText('Hasil permintaan sebelumnya belum diketahui')).toBeOnTheScreen();
    expect(screen.queryByRole('button', { name: 'Coba lagi' })).toBeNull();
    await fireEvent.press(screen.getByRole('button', { name: 'Mulai demo baru' }));

    await screen.findByText('14,700 kWh');
    const [first, second] = createCalls(fetchMock);
    expect(second.headers['Idempotency-Key']).not.toBe(first.headers['Idempotency-Key']);
  });

  it('continues to empty Home without creating a workspace', async () => {
    const fetchMock = mockApi({});
    await renderRouter('./src/app', { initialUrl: '/' });
    await fireEvent.press(await screen.findByRole('button', { name: 'Lanjut tanpa data' }));
    expect(await screen.findByText('Belum ada data energi')).toBeOnTheScreen();
    expect(createCalls(fetchMock)).toHaveLength(0);
    expect(await AsyncStorage.getItem('hematdaya.welcome.explored.v1')).toBe('true');
  });

  it('restores empty Home after returning without a workspace', async () => {
    await AsyncStorage.setItem('hematdaya.welcome.explored.v1', 'true');
    const fetchMock = mockApi({});
    await renderRouter('./src/app', { initialUrl: '/' });
    expect(await screen.findByText('Belum ada data energi')).toBeOnTheScreen();
    expect(createCalls(fetchMock)).toHaveLength(0);
  });

  it('resumes a stored workspace on restart', async () => {
    await storeWorkspace();
    mockApi({});

    await renderRouter('./src/app', { initialUrl: '/' });

    expect(await screen.findByText('14,700 kWh')).toBeOnTheScreen();
    expect(screen.queryByRole('heading', { name: 'Selamat datang' })).toBeNull();
  });

  it('ends an expired workspace honestly and offers to start again', async () => {
    await storeWorkspace();
    mockApi({
      summary: () =>
        respond(401, {
          error: {
            code: 'SESSION_EXPIRED',
            message: 'Sesi demo sudah berakhir. Mulai sesi demo baru untuk melanjutkan.',
            request_id: 'ref_expired',
            recovery: { retryable: false },
          },
        }),
    });

    await renderRouter('./src/app', { initialUrl: '/beranda' });

    expect(await screen.findByText('Sesi demo sudah berakhir')).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Coba demo' })).toBeOnTheScreen();
    expect(screen.queryByText('SESSION_EXPIRED')).toBeNull();
    expect(await SecureStore.getItemAsync('hematdaya.workspace.v1')).toBeNull();
  });
});

describe('populated Beranda', () => {
  afterEach(() => jest.restoreAllMocks());

  async function openWith(summary: (url: URL) => Response) {
    await storeWorkspace();
    const fetchMock = mockApi({ summary });
    await renderRouter('./src/app', { initialUrl: '/beranda' });
    return fetchMock;
  }

  it('shows no number on an empty today and offers the data period', async () => {
    const fetchMock = await openWith((url) => respond(200, url.searchParams.get('preset') === 'today' ? todayOnMonday : householdWeek));
    await screen.findByText('14,700 kWh');

    await fireEvent.press(screen.getByRole('button', { name: 'Hari ini' }));

    expect(await screen.findByText('Belum ada energi pada periode ini')).toBeOnTheScreen();
    expect(screen.getByText(/Tidak ditampilkan sebagai 0 kWh/)).toBeOnTheScreen();
    expect(screen.queryByText('14,700 kWh')).toBeNull();
    await fireEvent.press(screen.getByRole('button', { name: 'Lihat periode data' }));
    expect(await screen.findByText('14,700 kWh')).toBeOnTheScreen();
    expect(fetchMock.mock.calls.some(([input]) => String(input).includes('preset=today'))).toBe(true);
  });

  it('marks a running period', async () => {
    await openWith(() => respond(200, currentDay));

    expect(await screen.findByText('0,870 kWh')).toBeOnTheScreen();
    expect(screen.getByText('Periode aktif: 21 Oktober 2026 · sampai 12.00 (berjalan) · Asia/Jakarta')).toBeOnTheScreen();
  });

  it('shows partial coverage and the first gaps without expanding anything', async () => {
    await openWith(() => respond(200, partialWeek));

    expect(await screen.findAllByText('Sebagian data belum tersedia · Kelengkapan data: 71,4% periode')).not.toHaveLength(0);
    expect(screen.getAllByText('Data Pompa Air: 24–25 Oktober 2026 belum tersedia.').length).toBeGreaterThan(0);
  });

  it('shows a measured zero with no percentages', async () => {
    await openWith(() => respond(200, zeroWeek));

    expect((await screen.findAllByText('0,000 kWh')).length).toBeGreaterThan(0);
    expect(screen.getAllByText('Nol terukur dengan data lengkap · Kelengkapan data: 100% periode').length).toBeGreaterThan(0);
    expect(screen.queryByText(/%\s*$/)).toBeNull();
    expect(screen.getByText('Total energi nol, sehingga tidak ada persentase kontribusi.')).toBeOnTheScreen();
  });

  it('refuses a double-counting total and explains why', async () => {
    await openWith(() => respond(200, scopeDay));

    expect(await screen.findByText('Total gabungan belum dapat dihitung')).toBeOnTheScreen();
    expect(screen.getByText('Meter utama sudah mencakup Kulkas. Keduanya tidak dapat dijumlahkan.')).toBeOnTheScreen();
    expect(screen.queryByText('Belum ada data energi')).toBeNull();
    expect(screen.queryByText('Kontributor terbesar')).toBeNull();
  });

  it('offers the ranking as a table with the same values', async () => {
    await openWith(() => respond(200, householdWeek));
    await screen.findByText('14,700 kWh');

    await fireEvent.press(screen.getByRole('button', { name: 'Lihat data' }));

    const table = screen.getByLabelText('Energi per perangkat, 19–25 Oktober 2026, Asia/Jakarta');
    expect(within(table).getByText('8,400 kWh')).toBeOnTheScreen();
    expect(within(table).getByText('57,14%')).toBeOnTheScreen();
    expect(screen.getByText(/Kulkas mencatat energi terbesar: 8,400 kWh dari 14,700 kWh/)).toBeOnTheScreen();
  });

  it('keeps confirmed numbers when a refresh fails', async () => {
    let calls = 0;
    await openWith(() => {
      calls += 1;
      return calls === 1
        ? respond(200, householdWeek)
        : respond(500, { error: { code: 'INTERNAL_ERROR', message: 'Permintaan belum dapat diselesaikan.', request_id: 'ref_2', recovery: { retryable: false } } });
    });
    await screen.findByText('14,700 kWh');

    await fireEvent.press(screen.getByRole('button', { name: 'Perbarui' }));

    expect(await screen.findByText('Data belum dapat diperbarui')).toBeOnTheScreen();
    expect(screen.getByText('14,700 kWh')).toBeOnTheScreen();
  });

  it('applies an explicit range and refuses an invalid one', async () => {
    const fetchMock = await openWith(() => respond(200, householdWeek));
    await screen.findByText('14,700 kWh');

    await fireEvent.changeText(screen.getByLabelText('Tanggal mulai'), '19-10-2026');
    await fireEvent.press(screen.getByRole('button', { name: 'Terapkan' }));
    expect(screen.getByText(/Tanggal belum valid/)).toBeOnTheScreen();

    await fireEvent.changeText(screen.getByLabelText('Tanggal mulai'), '2026-10-12');
    await fireEvent.changeText(screen.getByLabelText('Tanggal selesai'), '2026-10-18');
    await fireEvent.press(screen.getByRole('button', { name: 'Terapkan' }));

    await waitFor(() =>
      expect(fetchMock.mock.calls.some(([input]) => String(input).includes('start_date=2026-10-12&end_date=2026-10-18'))).toBe(true),
    );
  });
});

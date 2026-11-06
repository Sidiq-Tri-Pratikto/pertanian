import { act, fireEvent, renderRouter, screen } from 'expo-router/testing-library';

import householdWeek from '../../../contracts/golden/summary-h-week.json';

const manifest = {
  schema_version: 1,
  source_release: '0.1.0',
  composition: { id: 'core-plus-optional', version: 1 },
  capabilities: [{ id: 'core', optional: false, status: 'planned' }],
  adapters: [{ id: 'csv', status: 'planned' }],
  policies: [{ id: 'baseline', version: 1 }],
};

function respond(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status });
}

const emptySession = {
  token: 'hdd_v1_empty',
  site_id: 'site-empty',
  scenario_id: 'empty',
  expires_at: '2099-01-01T00:00:00Z',
  initial_period: { preset: 'last_7_days', start_date: '2026-10-19', end_date: '2026-10-25' },
};
const emptySummary = {
  ...householdWeek,
  energy_kwh: null,
  energy_unavailable_reason: 'no_data',
  assets: [],
  scope: { valid: true, issues: [], included: [], excluded: [] },
  coverage: { minimum: null, concurrent: null, allocated_estimate: false },
  latest_measurement_at: null,
  origins: [],
};

/** Mulai and Lewati open an empty workspace through the service; everything else reads the manifest. */
async function serviceWithEmptyWorkspace(input: RequestInfo | URL) {
  const path = new URL(String(input)).pathname;
  if (path === '/api/v1/demo/sessions') {
    return respond(201, emptySession);
  }
  if (path.endsWith('/insights')) {
    return respond(200, { window: householdWeek.window, observations: [], notices: [], learning_count: 0, comparable_count: 0 });
  }
  return path.endsWith('/summary') ? respond(200, emptySummary) : respond(200, manifest);
}

async function startAtBeranda() {
  await renderRouter('./src/app', { initialUrl: '/beranda' });
  await screen.findByText('Layanan tersedia');
}

describe('navigation', () => {
  beforeEach(() => {
    jest.spyOn(globalThis, 'fetch').mockImplementation(serviceWithEmptyWorkspace);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('starts at the welcome screen and needs nothing to continue', async () => {
    await renderRouter('./src/app', { initialUrl: '/' });

    expect(screen.getByRole('heading', { name: 'Selamat datang' })).toBeOnTheScreen();
    expect(screen.getByRole('radio', { name: 'Belum memilih', checked: true })).toBeOnTheScreen();

    await fireEvent.press(screen.getByRole('button', { name: 'Mulai' }));

    expect(await screen.findByRole('heading', { name: 'Beranda' })).toBeOnTheScreen();
  });

  it('uses the chosen context for examples only', async () => {
    await renderRouter('./src/app', { initialUrl: '/' });

    await fireEvent.press(screen.getByRole('radio', { name: 'Industri' }));
    await fireEvent.press(screen.getByRole('button', { name: 'Mulai' }));

    expect(await screen.findByText('Misalnya oven, kompresor, atau mesin press.')).toBeOnTheScreen();
  });

  it('skipping keeps neutral examples', async () => {
    await renderRouter('./src/app', { initialUrl: '/' });

    await fireEvent.press(screen.getByRole('radio', { name: 'Industri' }));
    await fireEvent.press(screen.getByRole('button', { name: 'Lewati' }));

    expect(await screen.findByText('Misalnya perangkat, sirkuit, atau meter lokasi.')).toBeOnTheScreen();
  });

  it('shows exactly three labelled destinations with the current one selected', async () => {
    await startAtBeranda();

    expect(screen.getAllByRole('tab')).toHaveLength(3);
    expect(screen.getByRole('tab', { name: 'Beranda', selected: true })).toBeOnTheScreen();
    expect(screen.getByRole('tab', { name: 'Perangkat', selected: false })).toBeOnTheScreen();
    expect(screen.getByRole('tab', { name: 'Saran', selected: false })).toBeOnTheScreen();
  });

  it('moves between tabs', async () => {
    await startAtBeranda();

    await fireEvent.press(screen.getByRole('tab', { name: 'Saran' }));
    expect(await screen.findByRole('heading', { name: 'Saran' })).toBeOnTheScreen();
    expect(screen.getByText('Belum ada saran')).toBeOnTheScreen();

    await fireEvent.press(screen.getByRole('tab', { name: 'Perangkat' }));
    expect(await screen.findByRole('heading', { name: 'Perangkat' })).toBeOnTheScreen();
  });

  it('shows no data figures before data exists', async () => {
    await startAtBeranda();

    expect(screen.getByText('Belum ada data energi')).toBeOnTheScreen();
    expect(screen.queryByText(/kWh/)).toBeNull();
    expect(screen.queryByText(/Rp\d/)).toBeNull();
  });

  it('opens a planned feature inside the tab and returns to it', async () => {
    await startAtBeranda();

    await fireEvent.press(screen.getByRole('button', { name: 'Impor data' }));

    expect(await screen.findByRole('heading', { name: 'Impor data CSV' })).toBeOnTheScreen();
    expect(screen.getByText('Segera hadir')).toBeOnTheScreen();
    expect(screen.getByRole('tab', { name: 'Beranda', selected: true })).toBeOnTheScreen();

    await fireEvent.press(screen.getByRole('button', { name: 'Kembali' }));

    expect(await screen.findByRole('heading', { name: 'Beranda' })).toBeOnTheScreen();
  });

  it('lists every planned feature in settings', async () => {
    await startAtBeranda();

    await fireEvent.press(screen.getByRole('button', { name: 'Pengaturan' }));
    await screen.findByRole('heading', { name: 'Pengaturan' });

    await fireEvent.press(screen.getByRole('link', { name: 'Jadwal pemakaian, segera hadir' }));

    expect(await screen.findByRole('heading', { name: 'Jadwal pemakaian' })).toBeOnTheScreen();
  });

  it('handles an unknown feature address honestly', async () => {
    await renderRouter('./src/app', { initialUrl: '/segera-hadir/tidak-ada' });

    expect(await screen.findByRole('heading', { name: 'Fitur tidak ditemukan' })).toBeOnTheScreen();
  });
});

describe('service status', () => {
  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  it('keeps the app usable when the service is unreachable, and the retry recovers', async () => {
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('Network request failed'));

    await renderRouter('./src/app', { initialUrl: '/beranda' });

    expect(await screen.findByText('Layanan belum tersedia')).toBeOnTheScreen();
    expect(screen.getByRole('tab', { name: 'Beranda' })).toBeOnTheScreen();

    fetchMock.mockResolvedValue(respond(200, manifest));
    await fireEvent.press(screen.getByRole('button', { name: 'Coba lagi' }));

    expect(await screen.findByText('Layanan tersedia')).toBeOnTheScreen();
  });

  it('counts the first network request toward the retry limit', async () => {
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('Network request failed'));

    await renderRouter('./src/app', { initialUrl: '/beranda' });

    await fireEvent.press(await screen.findByRole('button', { name: 'Coba lagi' }));
    await fireEvent.press(await screen.findByRole('button', { name: 'Coba lagi' }));

    expect(await screen.findByText('Layanan belum tersedia')).toBeOnTheScreen();
    expect(screen.queryByRole('button', { name: 'Coba lagi' })).toBeNull();
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it('honors the server wait and attempt limit while keeping the reference visible', async () => {
    jest.useFakeTimers();
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockImplementation(async () =>
      respond(503, {
        error: {
          code: 'DATABASE_UNAVAILABLE',
          message: 'Layanan data sedang tidak tersedia. Coba lagi beberapa menit lagi.',
          request_id: 'ref_retry',
          recovery: { retryable: true, retry_after_seconds: 2, max_attempts: 2 },
        },
      }),
    );

    await renderRouter('./src/app', { initialUrl: '/beranda' });

    const retry = await screen.findByRole('button', { name: 'Coba lagi' });
    expect(retry).toBeDisabled();
    await fireEvent.press(retry);
    expect(fetchMock).toHaveBeenCalledTimes(1);

    await act(async () => {
      await jest.advanceTimersByTimeAsync(2000);
    });
    expect(screen.getByRole('button', { name: 'Coba lagi' })).toBeEnabled();
    await fireEvent.press(screen.getByRole('button', { name: 'Coba lagi' }));

    expect(await screen.findByText('ID referensi: ref_retry')).toBeOnTheScreen();
    expect(screen.queryByRole('button', { name: 'Coba lagi' })).toBeNull();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('shows the service message and reference, with no retry when not retryable', async () => {
    jest.spyOn(globalThis, 'fetch').mockResolvedValue(
      respond(500, {
        error: { code: 'INTERNAL_ERROR', message: 'Permintaan belum dapat diselesaikan.', request_id: 'ref_1', recovery: { retryable: false } },
      }),
    );

    await renderRouter('./src/app', { initialUrl: '/beranda' });

    expect(await screen.findByText('Permintaan belum dapat diselesaikan.')).toBeOnTheScreen();
    expect(screen.getByText('ID referensi: ref_1')).toBeOnTheScreen();
    expect(screen.queryByRole('button', { name: 'Coba lagi' })).toBeNull();
  });
});

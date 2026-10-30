import { fireEvent, renderRouter, screen } from 'expo-router/testing-library';

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

async function startAtBeranda() {
  await renderRouter('./src/app', { initialUrl: '/beranda' });
  await screen.findByText('Layanan tersedia');
}

describe('navigation', () => {
  beforeEach(() => {
    jest.spyOn(globalThis, 'fetch').mockImplementation(async () => respond(200, manifest));
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

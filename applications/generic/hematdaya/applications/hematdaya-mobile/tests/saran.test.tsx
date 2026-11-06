import { fireEvent, renderRouter, screen, within } from 'expo-router/testing-library';
import * as SecureStore from 'expo-secure-store';

import householdWeek from '../../../contracts/golden/summary-h-week.json';
import recorded from './fixtures/insights.json';

// Recorded from the 021 service on 2026-11-07: h-change, h-base and h-learning-partial for 19–25 Oktober 2026.
const change = recorded['h-change'];
const detail = recorded['h-change-detail'];
const LAST_WEEK = { preset: 'last_7_days', start_date: '2026-10-19', end_date: '2026-10-25' };

function respond(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status });
}

type Api = { insights?: () => Response; insight?: (url: URL) => Response };

function mockApi({ insights = () => respond(200, change), insight = () => respond(200, detail) }: Api = {}) {
  return jest.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
    const url = new URL(String(input));
    if (url.pathname.endsWith('/summary')) {
      return respond(200, householdWeek);
    }
    if (url.pathname.endsWith('/insights')) {
      return insights();
    }
    if (url.pathname.startsWith('/api/v1/insights/')) {
      return insight(url);
    }
    return respond(404, {});
  });
}

async function storeWorkspace() {
  await SecureStore.setItemAsync(
    'hematdaya.workspace.v1',
    JSON.stringify({ token: 'hdd_v1_change', siteId: 'site-change', scenarioId: 'h-change', expiresAt: '2099-01-01T00:00:00Z', initialPeriod: LAST_WEEK }),
  );
}

function detailCalls(fetchMock: jest.SpyInstance) {
  return fetchMock.mock.calls.map(([input]) => new URL(String(input))).filter((url) => url.pathname.startsWith('/api/v1/insights/'));
}

describe('Saran and evidence', () => {
  beforeEach(storeWorkspace);
  afterEach(() => jest.restoreAllMocks());

  it('reaches the exact evidence revision in one tap from Beranda and reads it in order', async () => {
    const fetchMock = mockApi();
    await renderRouter('./src/app', { initialUrl: '/beranda' });

    expect(await screen.findByText('TV naik 1,400 kWh (+55,56%)')).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('button', { name: 'Lihat dasar saran' }));

    expect(await screen.findByRole('heading', { name: 'TV naik 1,400 kWh (+55,56%)' })).toBeOnTheScreen();
    const [url] = detailCalls(fetchMock);
    expect(url.pathname).toBe(`/api/v1/insights/${detail.id}`);
    expect(url.searchParams.get('revision')).toBe('1');

    const steps = within(screen.getByLabelText('Dasar saran')).getAllByRole('heading').map((node) => node.props.children);
    expect(steps).toEqual(['1. Yang tercatat', '2. Pembanding', '3. Kualitas dan cakupan data', '4. Yang belum diketahui', '5. Saran umum']);
    expect(screen.getByText(detail.text.observed)).toBeOnTheScreen();
    expect(screen.getByText(detail.text.unknown)).toBeOnTheScreen();
    expect(screen.getByText('Langkah pemeriksaan umum, bukan hasil analisis khusus lokasi ini.')).toBeOnTheScreen();
    expect(screen.getByText(/Kelengkapan data periode ini: 100%/)).toBeOnTheScreen();
    expect(screen.getByText('Demo · Data simulasi')).toBeOnTheScreen();
    expect(screen.queryByText(/Terapkan|Matikan|Kerusakan|Boros|Hemat Rp/)).toBeNull();

    await fireEvent.press(screen.getByRole('button', { name: 'Detail perhitungan' }));
    expect(screen.getByText('C − B = 3,920 kWh − 2,520 kWh = 1,400 kWh')).toBeOnTheScreen();
    expect(screen.getByText('0,168 kWh')).toBeOnTheScreen();
    expect(screen.getByText('0,840 kWh')).toBeOnTheScreen();
    expect(screen.getByText('change versi 1')).toBeOnTheScreen();
    expect(screen.getByText(detail.evidence.rule)).toBeOnTheScreen();

    await fireEvent.press(screen.getByRole('button', { name: 'Lihat data pembanding' }));
    expect(screen.getByRole('img', { name: /TV: periode ini dan pembanding\. TV mencatat 3,920 kWh/ })).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('button', { name: 'Lihat data' }));
    const table = screen.getByLabelText('Energi harian TV, 19–25 Oktober 2026, Asia/Jakarta');
    expect(within(table).getAllByText('0,560 kWh')).toHaveLength(7);
    expect(within(table).getAllByText('0,360 kWh')).toHaveLength(7);
    expect(within(table).getByText('19 Oktober 2026')).toBeOnTheScreen();
  });

  it('keeps the revision the card showed after the data is corrected, marked as superseded', async () => {
    const fetchMock = mockApi({ insight: () => respond(200, { ...detail, superseded: true, current_revision: 2 }) });
    await renderRouter('./src/app', { initialUrl: '/saran' });

    await fireEvent.press(await screen.findByRole('button', { name: 'Lihat dasar saran' }));
    expect(await screen.findByText('Bukti ini sudah diperbarui')).toBeOnTheScreen();
    expect(screen.getByText(/Anda melihat versi 1 seperti saat saran ditampilkan/)).toBeOnTheScreen();
    expect(screen.getByText(detail.text.observed)).toBeOnTheScreen();

    await fireEvent.press(screen.getByRole('button', { name: 'Lihat bukti terbaru' }));
    await screen.findAllByText('Bukti ini sudah diperbarui');
    expect(detailCalls(fetchMock).map((url) => url.searchParams.get('revision'))).toEqual(['1', '2']);
  });

  it('lists observations and returns to the same list on back', async () => {
    mockApi();
    await renderRouter('./src/app', { initialUrl: '/saran' });

    expect(await screen.findByText('19–25 Oktober 2026 · Asia/Jakarta')).toBeOnTheScreen();
    expect(screen.getByText(/Memenuhi kriteria perubahan\. Penyebab belum diketahui\./)).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('button', { name: 'Lihat dasar saran' }));
    await screen.findByRole('heading', { name: 'TV naik 1,400 kWh (+55,56%)' });
    await fireEvent.press(screen.getByRole('button', { name: 'Kembali' }));
    expect(await screen.findByRole('heading', { name: 'Saran' })).toBeOnTheScreen();
    expect(screen.getByText('TV naik 1,400 kWh (+55,56%)')).toBeOnTheScreen();
  });

  it('says plainly when nothing met the criteria, without a verdict', async () => {
    mockApi({ insights: () => respond(200, recorded['h-base']) });
    await renderRouter('./src/app', { initialUrl: '/saran' });

    expect(await screen.findByText('Belum ada perubahan yang memenuhi kriteria pada periode ini')).toBeOnTheScreen();
    expect(screen.getByText(/bukan penilaian efisiensi atau keamanan/)).toBeOnTheScreen();
    expect(screen.queryByText('Catatan data')).toBeNull();
  });

  it('separates learning and data notices from observations', async () => {
    mockApi({ insights: () => respond(200, recorded['h-learning-partial']) });
    await renderRouter('./src/app', { initialUrl: '/saran' });

    expect(await screen.findByText('Belum cukup periode pembanding')).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Tentang riwayat perangkat' })).toBeOnTheScreen();
    expect(screen.getByText('Catatan data')).toBeOnTheScreen();
    expect(screen.getByText('Sebagian data belum tersedia · Pompa Air')).toBeOnTheScreen();
    expect(screen.queryByText('Belum ada perubahan yang memenuhi kriteria pada periode ini')).toBeNull();
  });

  it('shows a failure with retry, and Beranda keeps its numbers', async () => {
    let fail = true;
    mockApi({
      insights: () =>
        fail
          ? respond(503, { error: { code: 'SERVICE_UNAVAILABLE', message: 'Layanan belum tersedia. Coba lagi nanti.', request_id: 'req_1', recovery: { retryable: false } } })
          : respond(200, change),
    });
    await renderRouter('./src/app', { initialUrl: '/saran' });

    expect(await screen.findByText('Saran belum dapat dimuat')).toBeOnTheScreen();
    fail = false;
    await fireEvent.press(screen.getByRole('button', { name: 'Coba lagi' }));
    expect(await screen.findByText('TV naik 1,400 kWh (+55,56%)')).toBeOnTheScreen();
  });

  it('refuses an evidence link without a revision', async () => {
    mockApi();
    await renderRouter('./src/app', { initialUrl: `/saran/${detail.id}` });
    expect(await screen.findByText('Bukti tidak ditemukan')).toBeOnTheScreen();
  });
});

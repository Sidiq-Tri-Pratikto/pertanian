import AsyncStorage from '@react-native-async-storage/async-storage';
import { act, fireEvent, renderRouter, screen, waitFor } from 'expo-router/testing-library';

import { setLocale } from '@/features/localization/locale';
import { plannedMeter } from './fixtures/meter-pilot';

const CODE = 'hdpilot_test_access_code';
const SITE = 'pilot-site';
const ENROLLMENT = 'test-enrollment';
const expiry = '2099-01-01T00:00:00Z';
const captured = '2026-11-09T01:00:00Z';

function response(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status });
}

function mockPilot(available = true) {
  const writeRequests: { path: string; key: string | null; body: unknown; authorization: string | null }[] = [];
  let meterState = 'waiting';
  let failedSignIn = false;
  let failedConfirmation = false;
  let revoked = false;
  const fetcher = jest.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    const path = new URL(String(input)).pathname;
    const headers = new Headers(init?.headers);
    const authorization = headers.get('Authorization');
    if (init?.method === 'POST') {
      writeRequests.push({
        path, key: headers.get('Idempotency-Key'), body: JSON.parse(String(init.body)), authorization,
      });
    }
    if (path === '/api/v1/device-catalog') {
      return response(200, { devices: [{ ...plannedMeter, status: available ? 'available' : 'planned' }] });
    }
    if (path === '/api/v1/pilot/session') {
      if (failedSignIn) {
        return response(401, { error: { code: 'UNAUTHORIZED', message: 'Kode akses tidak berlaku. Minta kode baru.',
          request_id: 'ref_signin', recovery: { retryable: false } } });
      }
      return response(200, { site_id: SITE, expires_at: expiry });
    }
    if (path === `/api/v1/sites/${SITE}`) {
      return response(200, { id: SITE, kind: 'standard', timezone: 'Asia/Jakarta', now: captured });
    }
    if (path === `/api/v1/enrollments/${ENROLLMENT}/confirm`) {
      if (failedConfirmation) {
        failedConfirmation = false;
        return response(503, { error: { code: 'DATABASE_UNAVAILABLE', message: 'Sambungan belum dapat disimpan. Coba lagi.',
          request_id: 'ref_confirm', recovery: { retryable: true, retry_after_seconds: 0, max_attempts: 2 } } });
      }
      meterState = 'connected';
    }
    if (revoked && path === `/api/v1/enrollments/${ENROLLMENT}`) {
      return response(401, { error: { code: 'SESSION_EXPIRED', message: 'Kode akses sudah berakhir. Minta kode baru.',
        request_id: 'ref_expired', recovery: { retryable: false } } });
    }
    if (path.endsWith('/enrollments') || path.includes(`/enrollments/${ENROLLMENT}`)) {
      return response(200, {
        id: ENROLLMENT, expires_at: expiry, status: meterState,
        first_measured_at: meterState === 'waiting' ? null : captured,
        asset_id: meterState === 'connected' ? 'asset-from-meter' : null,
      });
    }
    return response(404, { error: { code: 'NOT_FOUND', message: 'Data belum ditemukan. Periksa kembali.',
      request_id: 'ref_fixture', recovery: { retryable: false } } });
  });
  return {
    fetcher, writeRequests,
    reading: () => { meterState = 'ready'; },
    rejectSignIn: () => { failedSignIn = true; },
    retryConfirm: () => { failedConfirmation = true; },
    revoke: () => { revoked = true; },
  };
}

afterEach(async () => {
  jest.restoreAllMocks();
  await act(() => setLocale('id'));
});

it('opens the English catalog from Welcome, with CSV optional and no enrollment for a planned model', async () => {
  const service = mockPilot(false);
  await renderRouter('./src/app', { initialUrl: '/' });
  await fireEvent.press(await screen.findByRole('radio', { name: 'English' }));
  const actions = screen.getAllByRole('button');
  expect(actions[0]).toBe(screen.getByRole('button', { name: 'Connect a meter' }));
  await fireEvent.press(actions[0]);

  expect(await screen.findByRole('heading', { name: 'Connect a meter' })).toBeOnTheScreen();
  expect(await screen.findByText('Shelly Plug PM Gen3')).toBeOnTheScreen();
  expect(screen.getByText('Planned')).toBeOnTheScreen();
  expect(screen.getByRole('button', { name: 'Import CSV history' })).toBeOnTheScreen();
  expect(screen.queryByRole('button', { name: 'Sign in to the pilot' })).toBeNull();
  expect(service.writeRequests).toHaveLength(0);
  expect(await AsyncStorage.getItem('hematdaya.welcome.explored.v1')).toBe('true');
});

it('keeps the pilot access code out of storage and connects only after a valid reading is confirmed', async () => {
  const service = mockPilot();
  await renderRouter('./src/app', { initialUrl: '/(tabs)/(beranda)/sumber' });
  await fireEvent.changeText(await screen.findByLabelText('Kode akses uji coba'), CODE);
  await fireEvent.press(screen.getByRole('button', { name: 'Masuk ke uji coba' }));

  expect(service.writeRequests).toHaveLength(0);
  expect(await AsyncStorage.getItem('hematdaya.workspace.v1')).toBeNull();
  await fireEvent.press(await screen.findByRole('button', { name: 'Mulai penyambungan' }));
  expect(await screen.findByText('Menunggu pembacaan pertama')).toBeOnTheScreen();
  expect(screen.queryByText('Alat ukur terhubung')).toBeNull();

  service.reading();
  await fireEvent.press(screen.getByRole('button', { name: 'Periksa status' }));
  expect(await screen.findByText('Pembacaan pertama diterima')).toBeOnTheScreen();
  expect(screen.queryByText('Alat ukur terhubung')).toBeNull();
  await fireEvent.changeText(screen.getByLabelText('Nama peralatan'), 'Kulkas');
  service.retryConfirm();
  await fireEvent.press(screen.getByRole('button', { name: 'Konfirmasi sambungan' }));

  expect(await screen.findByText('Alat ukur terhubung')).toBeOnTheScreen();
  expect(screen.getByRole('button', { name: 'Lihat riwayat peralatan' })).toBeOnTheScreen();
  const [start, confirm, retry] = service.writeRequests;
  expect(start).toEqual({
    path: `/api/v1/sites/${SITE}/enrollments`, key: expect.any(String),
    body: { model_id: plannedMeter.id }, authorization: `Bearer ${CODE}`,
  });
  expect(confirm).toEqual({
    path: `/api/v1/enrollments/${ENROLLMENT}/confirm`, key: expect.any(String),
    body: { asset_name: 'Kulkas' }, authorization: `Bearer ${CODE}`,
  });
  expect(retry).toEqual(confirm);
  await waitFor(() => expect(service.fetcher.mock.calls.some(([url]) =>
    String(url).includes(`/api/v1/sites/${SITE}/summary`))).toBe(true));

  await fireEvent.press(screen.getByRole('button', { name: 'Keluar dari uji coba' }));
  expect(await screen.findByRole('button', { name: 'Masuk ke uji coba' })).toBeOnTheScreen();
  expect(screen.queryByText('Alat ukur terhubung')).toBeNull();
});

it('shows the server reference for rejected access and makes no enrollment request', async () => {
  const service = mockPilot();
  service.rejectSignIn();
  await renderRouter('./src/app', { initialUrl: '/(tabs)/(perangkat)/sumber' });
  await fireEvent.changeText(await screen.findByLabelText('Kode akses uji coba'), CODE);
  await fireEvent.press(screen.getByRole('button', { name: 'Masuk ke uji coba' }));
  expect(await screen.findByText(/ID referensi: ref_signin/)).toBeOnTheScreen();
  expect(screen.queryByText(CODE)).toBeNull();
  expect(service.writeRequests).toHaveLength(0);
});


it('drops the previous enrollment view when the service revokes the pilot session', async () => {
  const service = mockPilot();
  await renderRouter('./src/app', { initialUrl: '/(tabs)/(beranda)/sumber' });
  await fireEvent.changeText(await screen.findByLabelText('Kode akses uji coba'), CODE);
  await fireEvent.press(screen.getByRole('button', { name: 'Masuk ke uji coba' }));
  await fireEvent.press(await screen.findByRole('button', { name: 'Mulai penyambungan' }));
  expect(await screen.findByText('Menunggu pembacaan pertama')).toBeOnTheScreen();

  service.revoke();
  await fireEvent.press(screen.getByRole('button', { name: 'Periksa status' }));

  expect(await screen.findByText('Akses uji coba berakhir')).toBeOnTheScreen();
  expect(screen.getByText(/ID referensi: ref_expired/)).toBeOnTheScreen();
  expect(await screen.findByRole('button', { name: 'Masuk ke uji coba' })).toBeOnTheScreen();
  expect(screen.queryByText('Menunggu pembacaan pertama')).toBeNull();
  expect(screen.queryByRole('button', { name: 'Periksa status' })).toBeNull();
});

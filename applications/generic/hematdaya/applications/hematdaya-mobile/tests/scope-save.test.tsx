import AsyncStorage from '@react-native-async-storage/async-storage';
import { Slot } from 'expo-router';
import { onlineManager } from '@tanstack/react-query';
import { act, fireEvent, renderRouter, screen, waitFor } from 'expo-router/testing-library';

import { NavigationContextProvider } from '@/features/navigation-context/NavigationContextProvider';
import { ScopeScreen } from '@/features/scope/ScopeScreen';
import { WorkspaceProvider } from '@/features/workspace/WorkspaceProvider';
import { ownerStorageKey } from '@/features/offline/owner-storage';

import { answer, baseSelection, meter, previewResult, rejection, scopeService, scopeWorkspace } from './fixtures/scope';
import { seedConfirmedWorkspace } from './fixtures/workspaces';

jest.setTimeout(30_000);

const routes = {
  _layout: () => <WorkspaceProvider><NavigationContextProvider><Slot /></NavigationContextProvider></WorkspaceProvider>,
  cakupan: ScopeScreen,
};

afterEach(() => {
  onlineManager.setOnline(true);
  jest.restoreAllMocks();
});

async function review() {
  await fireEvent.press(await screen.findByRole('radio', { name: 'Meter utama · 10,000 kWh' }));
  await fireEvent.press(screen.getByRole('button', { name: 'Pratinjau cakupan' }));
  await screen.findByText('Periode yang ditinjau');
}

async function start() {
  await renderRouter(routes, { initialUrl: '/cakupan' });
  await review();
}

it.each([
  ['SCOPE_CONFLICT', 'Perubahan ditolak layanan'],
  ['SCOPE_STALE', 'Pratinjau perlu diperbarui'],
] as const)('retains the draft, shows a reference and requires a fresh review after %s', async (code, title) => {
  await seedConfirmedWorkspace(scopeWorkspace);
  const fetchMock = scopeService({ put: () => rejection(code) });
  await start();
  await fireEvent.press(screen.getByRole('button', { name: 'Konfirmasi cakupan' }));
  expect(await screen.findByText(title)).toBeOnTheScreen();
  expect(screen.getByText('ID referensi: ref-scope-test.')).toBeOnTheScreen();
  expect(screen.queryByText(/fake-secret/)).toBeNull();
  expect(screen.getByRole('radio', { name: 'Meter utama · 10,000 kWh', checked: true })).toBeOnTheScreen();
  expect(screen.getByRole('button', { name: 'Konfirmasi cakupan', disabled: true })).toBeOnTheScreen();
  expect(fetchMock.mock.calls.filter(([, init]) => init?.method === 'PUT')).toHaveLength(1);
});

it('keeps same-pair lost-acknowledgment evidence through a read check, reconnect and another definitive refusal', async () => {
  const owner = await seedConfirmedWorkspace(scopeWorkspace);
  const key = ownerStorageKey(owner.epoch, 'scope-attempt');
  const mock = jest.fn()
    .mockRejectedValueOnce(new TypeError('lost response'))
    .mockResolvedValueOnce(rejection('SCOPE_CONFLICT'));
  const fetchMock = scopeService({ put: mock });
  await start();
  await fireEvent.press(screen.getByRole('button', { name: 'Konfirmasi cakupan' }));
  expect(await screen.findByText('Hasil penyimpanan belum diketahui')).toBeOnTheScreen();
  const marker = await AsyncStorage.getItem(key);
  expect(JSON.parse(marker!)).toEqual({ id: expect.any(String), base: { selection: 0, binding: 1 } });
  await fireEvent.press(screen.getByRole('button', { name: 'Periksa status simpan' }));
  await act(() => onlineManager.setOnline(false));
  await act(() => onlineManager.setOnline(true));
  await waitFor(() => expect(screen.getByText('Hasil penyimpanan belum diketahui')).toBeOnTheScreen());
  expect(fetchMock.mock.calls.filter(([, init]) => init?.method === 'PUT')).toHaveLength(1);
  await fireEvent.press(screen.getByRole('button', { name: 'Pratinjau cakupan' }));
  await screen.findByText('Periode yang ditinjau');
  expect(fetchMock.mock.calls.filter(([, init]) => init?.method === 'PUT')).toHaveLength(1);
  await fireEvent.press(screen.getByRole('button', { name: 'Konfirmasi cakupan' }));
  await screen.findByText('Perubahan ditolak layanan');
  expect(await AsyncStorage.getItem(key)).toBe(marker);
  expect(fetchMock.mock.calls.filter(([, init]) => init?.method === 'PUT')).toHaveLength(2);
});

it('treats a malformed 200 after dispatch as an unresolved outcome', async () => {
  await seedConfirmedWorkspace(scopeWorkspace);
  scopeService({ put: () => answer({ selected_asset_ids: [], selection_revision: 9, binding_revision: 1 }) });
  await start();
  await fireEvent.press(screen.getByRole('button', { name: 'Konfirmasi cakupan' }));
  expect(await screen.findByText('Hasil penyimpanan belum diketahui')).toBeOnTheScreen();
  expect(screen.queryByText('Cakupan tersimpan di layanan')).toBeNull();
});

it('keeps an older marker through a same-base no-op acknowledgment', async () => {
  const owner = await seedConfirmedWorkspace(scopeWorkspace);
  const key = ownerStorageKey(owner.epoch, 'scope-attempt');
  const explicit = { ...baseSelection, selection_revision: 1, selected_asset_ids: [meter], issues: [] };
  const proposal = { selected_asset_ids: [meter], period: { start_date: '2026-10-25', end_date: '2026-10-25' } };
  const confirmed = previewResult(proposal, explicit).summary;
  const put = jest.fn().mockRejectedValueOnce(new TypeError('lost response')).mockResolvedValueOnce(answer(explicit));
  scopeService({ put, selection: () => explicit, summary: () => answer(confirmed) });
  await renderRouter(routes, { initialUrl: '/cakupan' });
  await screen.findByText('Cakupan terkonfirmasi');
  await fireEvent.press(screen.getByRole('button', { name: 'Pratinjau cakupan' }));
  await screen.findByText('Periode yang ditinjau');
  await fireEvent.press(screen.getByRole('button', { name: 'Konfirmasi cakupan' }));
  await screen.findByText('Hasil penyimpanan belum diketahui');
  const marker = await AsyncStorage.getItem(key);
  expect(JSON.parse(marker!)).toMatchObject({ base: { selection: 1, binding: 1 } });

  await fireEvent.press(screen.getByRole('button', { name: 'Pratinjau cakupan' }));
  await screen.findByText('Periode yang ditinjau');
  await fireEvent.press(screen.getByRole('button', { name: 'Konfirmasi cakupan' }));
  await screen.findByText('Cakupan tersimpan di layanan');
  expect(screen.getByText('Hasil penyimpanan belum diketahui')).toBeOnTheScreen();
  expect(await AsyncStorage.getItem(key)).toBe(marker);
  expect(put).toHaveBeenCalledTimes(2);
});

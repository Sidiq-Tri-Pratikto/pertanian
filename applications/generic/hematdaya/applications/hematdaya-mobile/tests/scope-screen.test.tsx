import AsyncStorage from '@react-native-async-storage/async-storage';
import { act, fireEvent, renderRouter, screen, waitFor } from 'expo-router/testing-library';

import type { ScopeProposal, ScopeSelection } from '@/api/client';
import { ownerStorageKey } from '@/features/offline/owner-storage';
import * as focus from '@/lib/focus';

import { answer, baseSelection, meter, previewResult, scopeService, scopeSummary, scopeWorkspace } from './fixtures/scope';
import { seedConfirmedWorkspace } from './fixtures/workspaces';

// The first Expo Router render cold-loads the route graph.
jest.setTimeout(30_000);

afterEach(() => jest.restoreAllMocks());

async function openScope() {
  await renderRouter('./src/app', { initialUrl: '/beranda' });
  await fireEvent.press(await screen.findByRole('button', { name: 'Atur cakupan dan sumber' }));
  expect(await screen.findByRole('heading', { name: 'Cakupan dan sumber' })).toBeOnTheScreen();
}

async function reviewMeter() {
  await fireEvent.press(await screen.findByRole('radio', { name: 'Meter utama · 10,000 kWh' }));
  await fireEvent.press(screen.getByRole('button', { name: 'Pratinjau cakupan' }));
  await screen.findByText('Periode yang ditinjau');
}

it('keeps the tab and period on preview and cancel without a PUT', async () => {
  await seedConfirmedWorkspace(scopeWorkspace);
  const fetchMock = scopeService();
  const restoreFocus = jest.spyOn(focus, 'moveFocus');
  await openScope();
  expect(screen.getByRole('tab', { name: 'Beranda', selected: true })).toBeOnTheScreen();
  await reviewMeter();
  await fireEvent.press(screen.getByRole('button', { name: 'Batal' }));
  await screen.findByRole('heading', { name: 'Beranda' });
  await waitFor(() => expect(restoreFocus).toHaveBeenCalledTimes(1));
  expect(screen.getAllByText(/25 Oktober 2026/).length).toBeGreaterThan(0);
  expect(fetchMock.mock.calls.some(([, init]) => init?.method === 'PUT')).toBe(false);
  await fireEvent.press(screen.getByRole('tab', { name: 'Perangkat' }));
  await fireEvent.press(await screen.findByRole('button', { name: 'Selesaikan cakupan' }));
  expect(await screen.findByRole('tab', { name: 'Perangkat', selected: true })).toBeOnTheScreen();
  await fireEvent.press(screen.getByRole('button', { name: 'Batal' }));
  expect(await screen.findByRole('heading', { name: 'Perangkat' })).toBeOnTheScreen();
  await fireEvent.press(await screen.findByRole('link', { name: /^Kulkas,/ }));
  await screen.findByRole('heading', { name: 'Kulkas' });
  await fireEvent.press(await screen.findByRole('button', { name: 'Selesaikan cakupan' }));
  await screen.findByRole('heading', { name: 'Cakupan dan sumber' });
  expect(screen.getByRole('tab', { name: 'Perangkat', selected: true })).toBeOnTheScreen();
  await screen.findByText('Cakupan terkonfirmasi');
  expect(screen.getByRole('checkbox', { name: 'Meter utama', checked: true })).toBeOnTheScreen();
  await fireEvent.press(screen.getByRole('button', { name: 'Batal' }));
  expect(await screen.findByRole('heading', { name: 'Kulkas' })).toBeOnTheScreen();
  await waitFor(() => expect(restoreFocus).toHaveBeenCalledTimes(3));
  expect(fetchMock.mock.calls.some(([, init]) => init?.method === 'PUT')).toBe(false);
});

it('sends the exact reviewed PUT once and keeps previous figures labelled until the matching GET', async () => {
  await seedConfirmedWorkspace(scopeWorkspace);
  let current = baseSelection;
  let release: ((body: Response) => void) | undefined;
  let captured: ScopeProposal | undefined;
  const fetchMock = scopeService({
    selection: () => current,
    put: (body) => {
      captured = body;
      current = { ...baseSelection, selection_revision: 1, selected_asset_ids: [meter], issues: [] } satisfies ScopeSelection;
      return answer(current);
    },
    summary: () => current === baseSelection ? answer(scopeSummary) :
      new Promise((resolve) => { release = resolve; }),
  });
  await openScope();
  await reviewMeter();
  const confirm = screen.getByRole('button', { name: 'Konfirmasi cakupan' });
  await fireEvent.press(confirm);
  if (screen.queryByRole('button', { name: 'Konfirmasi cakupan' })) {
    await fireEvent.press(screen.getByRole('button', { name: 'Konfirmasi cakupan' }));
  }
  await waitFor(() => expect(release).toBeDefined());
  expect(await screen.findByText('Ringkasan masih memakai cakupan sebelumnya')).toBeOnTheScreen();
  const { start_date, end_date, timezone } = scopeSummary.window;
  expect(captured).toEqual({
    selected_asset_ids: [meter], authority_actions: [], disjoint_confirmations: [],
    period: { start_date, end_date }, expected_selection_revision: 0, expected_binding_revision: 1,
    resolved_period: { start_date, end_date, timezone },
  });
  expect(fetchMock.mock.calls.filter(([, init]) => init?.method === 'PUT')).toHaveLength(1);
  await act(() => release!(answer(previewResult(captured!, current).summary)));
  expect(await screen.findByText('Cakupan tersimpan di layanan')).toBeOnTheScreen();
  expect(screen.queryByText('Ringkasan masih memakai cakupan sebelumnya')).toBeNull();
});


it('cancels a confirmation that is still waiting on the local marker', async () => {
  const owner = await seedConfirmedWorkspace(scopeWorkspace);
  const marker = ownerStorageKey(owner.epoch, 'scope-attempt');
  const fetchMock = scopeService();
  await openScope();
  await reviewMeter();
  const setItem = AsyncStorage.setItem;
  let release: (() => void) | undefined;
  jest.spyOn(AsyncStorage, 'setItem').mockImplementationOnce((key, value) => {
    expect(key).toBe(marker);
    return new Promise((resolve) => { release = () => { void setItem(key, value).then(resolve); }; });
  });
  await fireEvent.press(screen.getByRole('button', { name: 'Konfirmasi cakupan' }));
  await waitFor(() => expect(release).toBeDefined());
  await fireEvent.press(screen.getByRole('button', { name: 'Batal' }));
  await act(() => release!());
  await screen.findByRole('heading', { name: 'Beranda' });
  await waitFor(async () => expect(await AsyncStorage.getItem(marker)).toBe('null'));
  expect(fetchMock.mock.calls.some(([, init]) => init?.method === 'PUT')).toBe(false);
});

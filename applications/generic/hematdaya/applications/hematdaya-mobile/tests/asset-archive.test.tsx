import { focusManager, onlineManager } from '@tanstack/react-query';
import { act, fireEvent, render, renderHook, screen, waitFor, within } from '@testing-library/react-native';
import { createRef, type ComponentRef } from 'react';
import type { View } from 'react-native';
import { seedConfirmedWorkspace } from './fixtures/workspaces';

import type { Asset } from '@/api/client';
import { ArchiveAssetSheet } from '@/features/assets/ArchiveAssetSheet';
import { useArchivedAssets } from '@/features/assets/useAssets';
import { WorkspaceProvider } from '@/features/workspace/WorkspaceProvider';

const asset: Asset = {
  id: 'asset', name: 'Kulkas', category: null, location: 'Dapur', archived: false,
  scope_kind: 'device', parent_asset_id: null, expected_use: 'unknown',
};
const workspace = {
  siteId: 'site', token: 'token', scenarioId: 'h-base', expiresAt: '2099-01-01T00:00:00Z',
  initialPeriod: { preset: 'last_7_days', start_date: '2026-10-19', end_date: '2026-10-25' },
};
function response(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status });
}

afterEach(() => {
  jest.restoreAllMocks();
  jest.useRealTimers();
  onlineManager.setOnline(true);
  focusManager.setFocused(undefined);
});

it.each([true, false])('names the affected asset and submits only archived=%s after confirmation', async (archive) => {
  const submit = jest.fn();
  const close = jest.fn();
  await render(<ArchiveAssetSheet open asset={asset} archive={archive} state={undefined} blocked={false}
    onSubmit={submit} onReview={jest.fn()} onClose={close} returnFocusTo={createRef<ComponentRef<typeof View>>()} />);
  const action = archive ? 'Arsipkan' : 'Pulihkan';
  const dialog = screen.getByLabelText(`${action} Kulkas?`);
  expect(within(dialog).getByText(/Cakupan pengukuran: 1 perangkat/)).toBeOnTheScreen();
  expect(within(dialog).getByText(/Riwayat pengukuran dan sumber data tetap tersimpan/)).toBeOnTheScreen();
  await fireEvent.press(within(dialog).getByRole('button', { name: 'Batal' }));
  expect(close).toHaveBeenCalledTimes(1);
  expect(submit).not.toHaveBeenCalled();
  await fireEvent.press(within(dialog).getByRole('button', { name: action }));
  expect(submit).toHaveBeenCalledWith({ archived: archive });
});

it.each([1, 3])('limits a failing archived cursor to %i attempts, including the first', async (maxAttempts) => {
  await seedConfirmedWorkspace(workspace);
  const fetchMock = jest.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
    const cursor = new URL(String(input)).searchParams.get('cursor');
    if (cursor === null) return response({ items: [{ ...asset, archived: true }], next_cursor: 'cursor-2' });
    return response({ error: {
      code: 'DATABASE_UNAVAILABLE', message: 'Daftar belum tersedia. Coba lagi nanti.', request_id: 'archive-cursor',
      recovery: { retryable: true, retry_after_seconds: 2, max_attempts: maxAttempts },
    } }, 503);
  });
  const { result, rerender } = await renderHook(({ open }: { open: boolean }) => useArchivedAssets(open),
    { wrapper: WorkspaceProvider, initialProps: { open: false } });
  jest.useFakeTimers();
  await rerender({ open: true });
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  for (let attempt = 1; attempt < maxAttempts; attempt += 1) {
    await act(async () => { await jest.advanceTimersByTimeAsync(1900); });
    expect(fetchMock).toHaveBeenCalledTimes(attempt + 1);
    await act(async () => { await jest.advanceTimersByTimeAsync(100); });
    expect(fetchMock).toHaveBeenCalledTimes(attempt + 2);
  }
  await waitFor(() => expect(result.current.error?.requestId).toBe('archive-cursor'));
  expect(result.current.data).toMatchObject({ items: [{ ...asset, archived: true }], next_cursor: 'cursor-2' });
  await rerender({ open: false });
  await rerender({ open: true });
  await act(async () => {
    focusManager.setFocused(false);
    focusManager.setFocused(true);
    await result.current.refetch();
    await jest.advanceTimersByTimeAsync(6000);
  });
  const archiveCalls = fetchMock.mock.calls.filter(([url]) => String(url).includes('include_archived=true'));
  expect(archiveCalls).toHaveLength(maxAttempts + 1);
});

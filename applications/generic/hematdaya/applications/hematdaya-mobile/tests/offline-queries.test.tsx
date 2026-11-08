import { act, renderHook, waitFor } from '@testing-library/react-native';
import type { ReactNode } from 'react';

import { compareScopePairs, summaryMatchesMembership, type Summary } from '@/api/client';
import { previousSnapshotFor, readSummaryStore, rememberSummary, snapshotFor } from '@/features/offline/persist-queries';

import { useSummary } from '@/features/energy/useSummary';
import { NavigationContextProvider } from '@/features/navigation-context/NavigationContextProvider';
import { WorkspaceProvider } from '@/features/workspace/WorkspaceProvider';

import { answer, scopeSummary, scopeWorkspace } from './fixtures/scope';
import { seedConfirmedWorkspace } from './fixtures/workspaces';
import assets from './fixtures/assets.json';

const data = { ...assets['h-base'].summary, selection_revision: null, binding_revision: 1 } as Summary;
const pair = { selection: 0, binding: 1 };
const period = { preset: 'last_7_days', start_date: data.window.start_date, end_date: data.window.end_date };
const active = { kind: 'all-active' } as const;

it('restores an exact selection with the original fetch timestamp and window', () => {
  const saved = rememberSummary(readSummaryStore(null), data, period, active, 0, 1_800_000_000_000);
  const restored = readSummaryStore(JSON.stringify(saved));
  expect(snapshotFor(restored, period, active, 0, pair)).toMatchObject({
    fetchedAt: 1_800_000_000_000,
    data: { window: data.window },
  });
  expect(snapshotFor(restored, period, active, 1, pair)).toBeUndefined();
  expect(snapshotFor(restored, period, { kind: 'asset', assetId: 'foreign' }, 0)).toBeUndefined();
});

it('cannot substitute a different local range or parse a corrupted record', () => {
  const saved = rememberSummary(readSummaryStore(null), data, period, active, 0, 1_800_000_000_000);
  expect(snapshotFor(saved, { ...period, preset: 'custom', start_date: '2026-01-01' }, active, 0)).toBeUndefined();
  expect(readSummaryStore('{corrupt').snapshots).toEqual([]);
});


it('keeps the chosen window when an earlier request completes after the selection changed', () => {
  const first = rememberSummary(readSummaryStore(null), data, period, active, 0, 1_800_000_000_000);
  const other = { ...data, window: { ...data.window,
    start: '2026-10-25T17:00:00Z', end: '2026-10-26T17:00:00Z', effective_end: '2026-10-26T17:00:00Z',
    start_date: '2026-10-26', end_date: '2026-10-26',
  } };
  const otherPeriod = { preset: 'range', start_date: '2026-10-26', end_date: '2026-10-26' };
  const after = rememberSummary(first, other, otherPeriod, active, 0, 1_800_000_000_001, false);
  expect(after.chosen).toEqual(period);
  expect(snapshotFor(after, otherPeriod, active, 0, pair)?.fetchedAt).toBe(1_800_000_000_001);
});

it('projects away unexpected credential-looking fields in summary records', () => {
  const untrusted = { ...data, token: 'fake-token', window: { ...data.window, authorization: 'fake-auth' } };
  const saved = rememberSummary(readSummaryStore(null), untrusted, period, active, 0, 1_800_000_000_000);
  expect(JSON.stringify(saved)).not.toMatch(/fake-token|fake-auth/);
});

it('keys site summaries by both scope revisions even when all figures and the combined revision are equal', () => {
  const first = rememberSummary(readSummaryStore(null), data, period, active, 0, 1_800_000_000_000);
  const explicit = { ...data, selection_revision: 1 };
  const next = rememberSummary(first, explicit, period, active, 1, 1_800_000_000_001);
  expect(snapshotFor(next, period, active, 1, pair)).toBeUndefined();
  expect(snapshotFor(next, period, active, 1, { selection: 1, binding: 1 })?.data).toEqual(explicit);
  expect(previousSnapshotFor(next, period, active, 1, { selection: 1, binding: 1 })?.fetchedAt).toBe(1_800_000_000_000);
  expect(compareScopePairs({ selection: 0, binding: 2 }, { selection: 1, binding: 1 })).toBeGreaterThan(0);
});

it('only uses a legacy site snapshot as previous and preserves an independent exact asset snapshot', () => {
  const asset = data.scope.included[0];
  const single = { ...data, scope: { ...data.scope, included: [asset] } };
  const scope = { kind: 'asset', assetId: asset.asset_id } as const;
  const current = rememberSummary(rememberSummary(readSummaryStore(null), data, period, active, 0, 1_800_000_000_000),
    single, period, scope, 0, 1_800_000_000_001);
  const legacy = readSummaryStore(JSON.stringify({ ...current, version: 1 }));
  expect(snapshotFor(legacy, period, active, 0, pair)).toBeUndefined();
  expect(previousSnapshotFor(legacy, period, active, 0, pair)?.data.window).toEqual(data.window);
  expect(snapshotFor(legacy, period, scope, 0)?.fetchedAt).toBe(1_800_000_000_001);
});

it('matches exact eligible membership after accounting for archived raw members', () => {
  const members = data.scope.included.map((asset) => asset.asset_id);
  const archived = { name: 'Diarsipkan', asset_id: 'archived', reason: 'archived' };
  const scoped = { ...data, scope: { ...data.scope, excluded: [...data.scope.excluded, archived] } };
  expect(summaryMatchesMembership(scoped, [...members, archived.asset_id])).toBe(true);
  expect(summaryMatchesMembership(scoped, members.slice(1))).toBe(false);
  expect(summaryMatchesMembership(scoped, [...members, 'unknown'])).toBe(false);
});

it('does not let old-pair snapshots substitute after binding-only changes or reset', () => {
  const first = rememberSummary(readSummaryStore(null), data, period, active, 0, 1_800_000_000_000);
  const bindingOnly = { ...data, binding_revision: 2 };
  const explicit = { ...bindingOnly, selection_revision: 1 };
  const reset = { ...data, binding_revision: 3 };
  const changed = rememberSummary(first, bindingOnly, period, active, 1, 1_800_000_000_001);
  const selected = rememberSummary(changed, explicit, period, active, 2, 1_800_000_000_002);
  const stored = rememberSummary(selected, reset, period, active, 3, 1_800_000_000_003);
  expect(snapshotFor(stored, period, active, 3, { binding: 3, selection: 0 })?.data).toEqual(reset);
  expect(snapshotFor(stored, period, active, 3, { binding: 2, selection: 1 })).toBeUndefined();
});


function Wrapper({ children }: { children: ReactNode }) {
  return <WorkspaceProvider><NavigationContextProvider>{children}</NavigationContextProvider></WorkspaceProvider>;
}

it('uses one summary GET to observe and display a newer binding pair and rejects an older completion', async () => {
  await seedConfirmedWorkspace(scopeWorkspace);
  const newer = { ...scopeSummary, binding_revision: 2 };
  const fetchMock = jest.spyOn(globalThis, 'fetch').mockResolvedValueOnce(answer(scopeSummary))
    .mockResolvedValueOnce(answer(newer)).mockResolvedValueOnce(answer(scopeSummary));
  try {
    const hook = await renderHook(useSummary, { wrapper: Wrapper });
    await waitFor(() => expect(hook.result.current.data?.binding_revision).toBe(1));
    await act(() => hook.result.current.refresh());
    await waitFor(() => expect(hook.result.current.data?.binding_revision).toBe(2));
    expect(hook.result.current.previousSelection).toBe(false);
    expect(hook.result.current.confirmedAtFor(hook.result.current.data!)).toBeDefined();
    expect(fetchMock).toHaveBeenCalledTimes(2);
    await act(() => hook.result.current.refresh());
    await waitFor(() => expect(hook.result.current.error?.message).toMatch(/tidak dikenali/));
    expect(hook.result.current.data?.binding_revision).toBe(2);
    expect(fetchMock.mock.calls.every(([url, init]) => String(url).includes('/summary?') && init?.method === 'GET')).toBe(true);
  } finally {
    fetchMock.mockRestore();
  }
});

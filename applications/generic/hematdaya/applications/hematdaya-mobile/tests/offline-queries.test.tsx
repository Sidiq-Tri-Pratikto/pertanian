import type { Summary } from '@/api/client';
import { readSummaryStore, rememberSummary, snapshotFor } from '@/features/offline/persist-queries';

import assets from './fixtures/assets.json';

const data = assets['h-base'].summary as Summary;
const period = { preset: 'last_7_days', start_date: data.window.start_date, end_date: data.window.end_date };
const active = { kind: 'all-active' } as const;

it('restores an exact selection with the original fetch timestamp and window', () => {
  const saved = rememberSummary(readSummaryStore(null), data, period, active, 0, 1_800_000_000_000);
  const restored = readSummaryStore(JSON.stringify(saved));
  expect(snapshotFor(restored, period, active, 0)).toMatchObject({
    fetchedAt: 1_800_000_000_000,
    data: { window: data.window },
  });
  expect(snapshotFor(restored, period, active, 1)).toBeUndefined();
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
  expect(snapshotFor(after, otherPeriod, active, 0)?.fetchedAt).toBe(1_800_000_000_001);
});

it('projects away unexpected credential-looking fields in summary records', () => {
  const untrusted = { ...data, token: 'fake-token', window: { ...data.window, authorization: 'fake-auth' } };
  const saved = rememberSummary(readSummaryStore(null), untrusted, period, active, 0, 1_800_000_000_000);
  expect(JSON.stringify(saved)).not.toMatch(/fake-token|fake-auth/);
});

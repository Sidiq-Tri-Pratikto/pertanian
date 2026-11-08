import { isSummary, type Summary } from '@/api/client';
import type { Period } from '@/features/workspace/workspace-store';

export type SummaryScope = { kind: 'all-active' } | { kind: 'asset'; assetId: string };
export type SummarySnapshot = {
  data: Summary;
  fetchedAt: number;
  period: Period;
  scope: SummaryScope;
  scopeIds: string[];
  scopeEpoch: number;
  /** 028 selection revisions are separate from the combined data revision returned by SummaryResponse. */
  selectionRevision: null;
};

export type SummaryStore = {
  version: 1;
  scopeEpoch: number;
  chosen: Period | null;
  snapshots: SummarySnapshot[];
};

const LIMIT = 18;
const MAX_BYTES = 750_000;
const PRESETS = new Set(['today', 'this_week', 'last_7_days']);
const EMPTY: SummaryStore = { version: 1, scopeEpoch: 0, chosen: null, snapshots: [] };

export function isServicePreset(preset: string): boolean {
  return PRESETS.has(preset);
}

function isPeriod(value: unknown): value is Period {
  const period = value as Partial<Period> | null;
  return typeof period?.preset === 'string' && period.preset.length <= 32 &&
    typeof period.start_date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(period.start_date) &&
    typeof period.end_date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(period.end_date) &&
    period.start_date <= period.end_date;
}

function isEpoch(value: unknown): value is number {
  return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0;
}

function ids(data: Summary): string[] {
  return [...new Set(data.scope.included.map((asset) => asset.asset_id))].sort();
}

function scopeMatches(data: Summary, scope: SummaryScope): boolean {
  return scope.kind === 'all-active' || (scope.kind === 'asset' && ids(data).length === 1 && ids(data)[0] === scope.assetId);
}

export function matchesSummary(data: Summary, period: Period, scope: SummaryScope): boolean {
  return scopeMatches(data, scope) && (isServicePreset(period.preset) ||
    (data.window.start_date === period.start_date && data.window.end_date === period.end_date));
}

function isSnapshot(value: unknown): value is SummarySnapshot {
  const row = value as Partial<SummarySnapshot> | null;
  return row !== null && row !== undefined && isSummary(row.data) && isPeriod(row.period) &&
    row.data.window.start_date === row.period.start_date && row.data.window.end_date === row.period.end_date &&
    typeof row.fetchedAt === 'number' && Number.isSafeInteger(row.fetchedAt) && row.fetchedAt > 0 &&
    row.scope != null && scopeMatches(row.data, row.scope) && Array.isArray(row.scopeIds) &&
    JSON.stringify(ids(row.data)) === JSON.stringify(row.scopeIds) &&
    isEpoch(row.scopeEpoch) && row.selectionRevision === null;
}

export function readSummaryStore(raw: string | null): SummaryStore {
  if (!raw || raw.length > MAX_BYTES) return EMPTY;
  try {
    const parsed = JSON.parse(raw) as Partial<SummaryStore> | null;
    if (parsed?.version !== 1 || !isEpoch(parsed.scopeEpoch) || !Array.isArray(parsed.snapshots)) return EMPTY;
    const epoch = parsed.scopeEpoch;
    return {
      version: 1, scopeEpoch: epoch,
      chosen: isPeriod(parsed.chosen) ? parsed.chosen : null,
      snapshots: parsed.snapshots.filter(isSnapshot).filter((row) => row.scopeEpoch <= epoch).slice(0, LIMIT).map((row) => ({
        data: projectSummary(row.data), fetchedAt: row.fetchedAt,
        period: pick(row.period, 'preset', 'start_date', 'end_date'),
        scope: row.scope.kind === 'asset' ? { kind: 'asset', assetId: row.scope.assetId } : { kind: 'all-active' },
        scopeIds: row.scopeIds, scopeEpoch: row.scopeEpoch, selectionRevision: null,
      })),
    };
  } catch {
    return EMPTY;
  }
}

/** A preset's resolved period remains fixed on disk until the service confirms another window. */
export function resolvedPreset(store: SummaryStore, period: Period, epoch: number): Period {
  if (!isServicePreset(period.preset) || period.start_date) return period;
  return store.snapshots.find((row) => row.scopeEpoch === epoch && row.period.preset === period.preset)?.period ?? period;
}

export function snapshotFor(store: SummaryStore, period: Period, scope: SummaryScope, epoch: number) {
  return store.snapshots.find((row) => row.scopeEpoch === epoch && row.scope.kind === scope.kind &&
    (scope.kind === 'all-active' || (row.scope.kind === 'asset' && row.scope.assetId === scope.assetId)) &&
    row.period.start_date === period.start_date && row.period.end_date === period.end_date);
}

function sameKey(a: SummarySnapshot, b: SummarySnapshot) {
  return a.scopeEpoch === b.scopeEpoch && a.scope.kind === b.scope.kind &&
    JSON.stringify(a.scopeIds) === JSON.stringify(b.scopeIds) &&
    a.data.window.start === b.data.window.start && a.data.window.end === b.data.window.end &&
    a.data.window.effective_end === b.data.window.effective_end && a.data.window.timezone === b.data.window.timezone;
}

export function rememberSummary(store: SummaryStore, data: Summary, period: Period, scope: SummaryScope, scopeEpoch: number, fetchedAt: number, rememberSelection = true): SummaryStore {
  const { start_date, end_date } = data.window;
  const resolved = { preset: period.preset, start_date, end_date };
  const snapshot = { data: projectSummary(data), fetchedAt, period: resolved, scope, scopeIds: ids(data), scopeEpoch, selectionRevision: null };
  return {
    version: 1, scopeEpoch, chosen: rememberSelection ? resolved : store.chosen,
    snapshots: [snapshot, ...store.snapshots.filter((row) => !sameKey(row, snapshot))].slice(0, LIMIT),
  };
}

function pick<T extends object, K extends keyof T>(item: T, ...fields: K[]): Pick<T, K> {
  return Object.fromEntries(fields.map((key) => [key, item[key]])) as Pick<T, K>;
}

/** Persist only the summary contract fields. Unexpected response extras never enter durable storage. */
function projectSummary(data: Summary): Summary {
  return {
    ...pick(data, 'energy_kwh', 'energy_unavailable_reason', 'latest_measurement_at', 'origins', 'revision'),
    window: pick(data.window, 'start', 'end', 'effective_end', 'start_date', 'end_date', 'timezone', 'is_current'),
    scope: {
      valid: data.scope.valid,
      included: data.scope.included.map((row) => pick(row, 'asset_id', 'name')),
      excluded: data.scope.excluded.map((row) => pick(row, 'asset_id', 'name', 'reason')),
      issues: data.scope.issues.map((row) => pick(row, 'type', 'asset_ids', 'message')),
    },
    coverage: pick(data.coverage, 'minimum', 'concurrent', 'allocated_estimate'),
    assets: data.assets.map((asset) => ({
      ...pick(asset, 'asset_id', 'name', 'scope_kind', 'energy_kwh', 'energy_unavailable_reason', 'share_percent', 'coverage'),
      gaps: asset.gaps.map((row) => pick(row, 'start', 'end')),
      conflict_sources: asset.conflict_sources?.map((row) => pick(row, 'source_id', 'label', 'energy_kwh')) ?? null,
    })),
    ...(data.source_freshness ? {
      source_freshness: data.source_freshness.map((row) => ({
        ...pick(row, 'source_id', 'asset_id', 'label', 'origin', 'state', 'last_capture_at', 'cadence_seconds', 'policy_version'),
        historical_range: row.historical_range ? pick(row.historical_range, 'start', 'end') : null,
      })),
    } : {}),
  };
}

export function serializeSummaryStore(store: SummaryStore): string {
  const snapshots = [...store.snapshots];
  let value = JSON.stringify({ ...store, snapshots });
  while (value.length > MAX_BYTES && snapshots.length > 0) {
    snapshots.pop();
    value = JSON.stringify({ ...store, snapshots });
  }
  return value;
}

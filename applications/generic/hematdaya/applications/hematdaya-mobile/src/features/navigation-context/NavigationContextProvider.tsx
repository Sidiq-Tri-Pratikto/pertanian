import { createContext, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';

import type { PeriodQuery, Summary } from '@/api/client';
import {
  isServicePreset, previousSnapshotFor, readSummaryStore, rememberSummary, resolvedPreset, serializeSummaryStore, snapshotFor,
  type SummaryScope, type SummarySnapshot, type SummaryStore,
} from '@/features/offline/persist-queries';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';
import type { Period } from '@/features/workspace/workspace-store';

/** An observation just hidden from the evidence screen, so the screen it returns to can offer Pulihkan. */
export type HiddenItem = { id: string; revision: number; title: string; titles?: { id: string; en: string } };

type NavigationContextValue = {
  period: Period | null;
  setPeriod: (period: Period) => void;
  isCurrentPeriod: (period: Period) => boolean;
  currentPeriodVersion: () => number;
  periodRevision: number;
  recentlyHidden: HiddenItem | null;
  setRecentlyHidden: (item: HiddenItem | null) => void;
  snapshot: (period: Period, scope: SummaryScope, previous?: boolean) => SummarySnapshot | undefined;
  record: (data: Summary, period: Period, scope: SummaryScope, epoch: number, fetchedAt: number) => void;
  fetchedAt: (data: Summary) => number | undefined;
};

const NavigationContext = createContext<NavigationContextValue>({
  period: null, setPeriod: () => undefined, isCurrentPeriod: () => false, currentPeriodVersion: () => 0, periodRevision: 0, recentlyHidden: null, setRecentlyHidden: () => undefined,
  snapshot: () => undefined, record: () => undefined, fetchedAt: () => undefined,
});

export function periodQuery(period: Period): PeriodQuery {
  return isServicePreset(period.preset)
    ? { preset: period.preset }
    : { start_date: period.start_date, end_date: period.end_date };
}

type Hydrated = { epoch: string; store: SummaryStore };
type Chosen = { generation: number; value: Period };
type Hidden = { generation: number; value: HiddenItem | null };

function matchesRequest(a: Period, b: Period): boolean {
  return a.preset === b.preset && (isServicePreset(a.preset) ||
    (a.start_date === b.start_date && a.end_date === b.end_date));
}

/** One owner-scoped selection for every tab, with the last server-resolved period on cold start. */
export function NavigationContextProvider({ children }: { children: ReactNode }) {
  const { workspace, storage, credentialGeneration, isCurrentCredential, scopeEpoch, currentScopeEpoch, scopePair, scopeAttempt } = useWorkspace();
  const [chosen, setChosen] = useState<Chosen | null>(null);
  const [hidden, setHidden] = useState<Hidden | null>(null);
  const [hydrated, setHydrated] = useState<Hydrated | null>(null);
  const persisted = useRef<Hydrated | null>(null);
  const fetchTimes = useRef(new WeakMap<Summary, number>());
  const pending = storage !== null && hydrated?.epoch !== storage.epoch;
  const recordForOwner = storage && !pending ? hydrated : null;
  const period = pending ? null : (chosen?.generation === credentialGeneration ? chosen.value :
    recordForOwner?.store.chosen ?? workspace?.initialPeriod ?? null);
  const currentPeriod = useRef<Period | null>(null);
  const periodVersion = useRef(0);
  const [periodRevision, setPeriodRevision] = useState(0);
  useEffect(() => { currentPeriod.current = period; }, [period]);
  const recentlyHidden = hidden?.generation === credentialGeneration ? hidden.value : null;

  useEffect(() => {
    if (!storage) return;
    let live = true;
    void storage.read('summaries').then((raw) => {
      if (!live || !isCurrentCredential(credentialGeneration)) return;
      const store = readSummaryStore(raw);
      for (const snapshot of store.snapshots) fetchTimes.current.set(snapshot.data, snapshot.fetchedAt);
      const resolved = { epoch: storage.epoch, store };
      persisted.current = resolved;
      setHydrated(resolved);
    });
    return () => { live = false; };
  }, [credentialGeneration, isCurrentCredential, storage]);

  const value = useMemo<NavigationContextValue>(() => ({
    period,
    setPeriod: (next) => {
      if (!isCurrentCredential(credentialGeneration)) return;
      const owner = persisted.current;
      const selected = storage?.epoch === owner?.epoch && owner
        ? resolvedPreset(owner.store, next, scopeEpoch) : next;
      const before = currentPeriod.current;
      if (!before || !matchesRequest(before, selected) || before.start_date !== selected.start_date || before.end_date !== selected.end_date) {
        setPeriodRevision(++periodVersion.current);
      }
      currentPeriod.current = selected;
      setChosen({ generation: credentialGeneration, value: selected });
    },
    currentPeriodVersion: () => periodVersion.current,
    periodRevision,
    isCurrentPeriod: (expected) => currentPeriod.current !== null &&
      matchesRequest(currentPeriod.current, expected) &&
      currentPeriod.current.start_date === expected.start_date && currentPeriod.current.end_date === expected.end_date,
    recentlyHidden,
    setRecentlyHidden: (next) => {
      if (isCurrentCredential(credentialGeneration)) setHidden({ generation: credentialGeneration, value: next });
    },
    snapshot: (selected, selection, previous = false) => {
      if (!recordForOwner || storage?.epoch !== recordForOwner.epoch) return undefined;
      const unresolved = selection.kind === 'all-active' && scopeAttempt !== null;
      const pair = unresolved ? null : scopePair;
      if (previous) return previousSnapshotFor(recordForOwner.store, selected, selection, scopeEpoch, pair);
      if (unresolved) return undefined;
      return snapshotFor(recordForOwner.store, selected, selection, scopeEpoch, pair);
    },
    fetchedAt: (data) => fetchTimes.current.get(data),
    record: (data, selected, selection, epoch, fetchedAt) => {
      if (!isCurrentCredential(credentialGeneration) || epoch !== currentScopeEpoch()) return;
      fetchTimes.current.set(data, fetchedAt);
      if (!storage) return;
      const state = persisted.current;
      if (state?.epoch !== storage.epoch) return;
      const chosenNow = currentPeriod.current;
      state.store = rememberSummary(state.store, data, selected, selection, epoch, fetchedAt,
        chosenNow !== null && matchesRequest(chosenNow, selected));
      void storage.write('summaries', serializeSummaryStore(state.store));
    },
  }), [period, periodRevision, credentialGeneration, currentScopeEpoch, isCurrentCredential, recentlyHidden, recordForOwner, scopeEpoch, scopePair, scopeAttempt, storage]);

  return <NavigationContext.Provider value={value}>{children}</NavigationContext.Provider>;
}

export function useNavigationContext(): NavigationContextValue {
  return useContext(NavigationContext);
}

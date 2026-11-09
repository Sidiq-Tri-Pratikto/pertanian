import AsyncStorage from '@react-native-async-storage/async-storage';
import { focusManager, onlineManager, QueryClientProvider } from '@tanstack/react-query';
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { Platform } from 'react-native';

import {
  compareScopePairs, confirmDemoSite, resetDemoSession, sameScopeIds, summaryMatchesMembership,
  type DemoSession, type RequestCredential, type ScopePair, type Summary,
} from '@/api/client';
import { ApiError } from '@/api/errors';
import { getPilotSession, getPilotSite } from '@/api/meter-pilot';
import { createQueryClient, endsSession } from '@/api/query-client';
import {
  ownerStorageKey, readScopeAttempt, readScopeFence, removeOwnerData,
  type OwnerStorage, type ScopeAttempt, type ScopeFence, type StorageSection,
} from '@/features/offline/owner-storage';
import { isKnownOffline } from '@/features/offline/useConnectivity';
import { localParts } from '@/lib/format';
import { randomToken } from '@/lib/random';
import {
  attestWorkspace, clearWorkspace, isUnexpired, loadWorkspaceRecord, revokeWorkspace, saveWorkspace, tombstoneWorkspace,
  type Attestation, type Workspace, type WorkspaceRecord,
} from '@/features/workspace/workspace-store';

type Active = {
  workspace: Workspace;
  credential: RequestCredential;
  attestation: Attestation | null;
  storage: OwnerStorage | null;
};

type ScopeEvidence = { rawIds?: string[]; summary?: Summary };
type ScopeObservation = { epoch: number; durable: Promise<boolean> };
type ScopeWrite = { id: string; sole: boolean };

type WorkspaceValue = {
  status: 'loading' | 'ready';
  workspace: Workspace | null;
  credential: RequestCredential | null;
  storage: OwnerStorage | null;
  legacyImport: boolean;
  credentialGeneration: number;
  isCurrentCredential: (generation: number) => boolean;
  scopeEpoch: number;
  currentScopeEpoch: () => number;
  currentScopePair: () => ScopePair | null;
  advanceScope: () => Promise<void>;
  scopePair: ScopePair | null;
  scopeAttempt: ScopeAttempt | null;
  scopeWriting: boolean;
  isScopeCurrent: (epoch: number, pair: ScopePair) => boolean;
  observeScope: (pair: ScopePair, evidence: ScopeEvidence, publish?: (epoch: number) => void) => ScopeObservation | null;
  beginScopeWrite: (base: ScopePair, epoch: number) => Promise<ScopeWrite>;
  finishScopeWrite: (write: ScopeWrite, definite: boolean) => Promise<boolean>;
  ended: 'expired' | 'pilot-expired' | null;
  pilotEndReference: string | null;
  storageError: boolean;
  open: (workspace: Workspace, response?: DemoSession) => Promise<void>;
  end: (reason: 'expired' | null) => Promise<void>;
  resetDemo: () => Promise<void>;
  pilot: boolean;
  openPilot: (code: string, stillOpen: () => boolean) => Promise<void>;
  closePilot: () => Promise<void>;
};

const WorkspaceContext = createContext<WorkspaceValue | null>(null);

function isMatchingCreate(workspace: Workspace, response?: DemoSession): boolean {
  return response !== undefined && response.token === workspace.token && response.site_id === workspace.siteId &&
    response.scenario_id === workspace.scenarioId && response.expires_at === workspace.expiresAt;
}

/** One credential lifecycle owns the query client and the only route to durable owner records. */
export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<'loading' | 'ready'>('loading');
  const [active, setActive] = useState<Active | null>(null);
  const [ended, setEnded] = useState<WorkspaceValue['ended']>(null);
  const [pilotEndReference, setPilotEndReference] = useState<string | null>(null);
  const [storageError, setStorageError] = useState(false);
  const [queryClient] = useState(createQueryClient);
  const generation = useRef(0);
  const [credentialGeneration, setCredentialGeneration] = useState(0);
  const scope = useRef(0);
  const [scopeEpoch, setScopeEpoch] = useState(0);
  const scopeFence = useRef<ScopeFence>({ epoch: 0, pair: null });
  const [scopePair, setScopePair] = useState<ScopePair | null>(null);
  const scopeEvidence = useRef<ScopeEvidence>({});
  const fenceWrite = useRef(Promise.resolve(true));
  const locallyAdvanced = useRef(false);
  const attempt = useRef<ScopeAttempt | null>(null);
  const [scopeAttempt, setScopeAttempt] = useState<ScopeAttempt | null>(null);
  const inFlight = useRef<string | null>(null);
  const [scopeWriting, setScopeWriting] = useState(false);
  const control = useRef<WorkspaceRecord | null>(null);
  const pilotActive = useRef(false);
  const controller = useRef(new AbortController());
  const tail = useRef<Promise<unknown>>(Promise.resolve());
  const isCurrentCredential = useCallback((id: number) => generation.current === id, []);
  const currentScopeEpoch = useCallback(() => scope.current, []);
  const currentScopePair = useCallback(() => scopeFence.current.pair, []);

  const serial = useCallback(<T,>(task: () => Promise<T>): Promise<T> => {
    const result = tail.current.then(task, task);
    tail.current = result.catch(() => undefined);
    return result;
  }, []);

  const block = useCallback(() => {
    const next = ++generation.current;
    controller.current.abort();
    controller.current = new AbortController();
    scope.current = 0;
    scopeFence.current = { epoch: 0, pair: null };
    scopeEvidence.current = {};
    fenceWrite.current = Promise.resolve(true);
    locallyAdvanced.current = false;
    attempt.current = null;
    inFlight.current = null;
    setScopeEpoch(0);
    setScopePair(null);
    setScopeAttempt(null);
    setScopeWriting(false);
    setCredentialGeneration(next);
    setActive(null);
    queryClient.clear();
    return next;
  }, [queryClient]);

  const clean = useCallback(async (record: WorkspaceRecord, id: number) => {
    if (record.kind !== 'confirmed') return;
    const epoch = record.attestation.epoch;
    const removals = [removeOwnerData(epoch)];
    if (Platform.OS === 'web') removals.push(Promise.resolve().then(() =>
      globalThis.sessionStorage.removeItem(ownerStorageKey(epoch, 'import-recovery'))));
    const result = await Promise.allSettled(removals);
    if (isCurrentCredential(id) && result.some((entry) => entry.status === 'rejected')) setStorageError(true);
  }, [isCurrentCredential]);

  const end = useCallback(async (reason: 'expired' | null) => {
    const id = block();
    setEnded(reason);
    await serial(async () => {
      const previous = control.current;
      let revoked = false;
      if (previous) {
        try {
          await tombstoneWorkspace();
          revoked = true;
        } catch {
          if (isCurrentCredential(id)) setStorageError(true);
        }
      }
      try {
        await clearWorkspace();
        revoked = true;
      } catch {
        if (isCurrentCredential(id)) setStorageError(true);
      }
      if (revoked) control.current = null;
      if (previous && revoked) await clean(previous, id);
    });
  }, [block, clean, isCurrentCredential, serial]);

  const lease = useCallback((workspace: Workspace, id: number): RequestCredential => ({
    token: workspace.token,
    signal: controller.current.signal,
    current: () => {
      if (!isCurrentCredential(id)) return false;
      if (isUnexpired(workspace)) return true;
      void end('expired');
      return false;
    },
    reject: () => {
      if (isCurrentCredential(id)) void end('expired');
    },
  }), [end, isCurrentCredential]);

  const activate = useCallback(async (record: WorkspaceRecord & { kind: 'confirmed' }, id: number) => {
    if (!isCurrentCredential(id)) return;
    const { workspace, attestation } = record;
    const credential = lease(workspace, id);
    const epoch = attestation.epoch;
    const update = (section: StorageSection, change: (before: string | null) => string, readBefore: boolean) => serial(async () => {
      if (!credential.current()) return false;
      try {
        const key = ownerStorageKey(epoch, section);
        const previous = readBefore ? await AsyncStorage.getItem(key) : null;
        if (!credential.current()) return false;
        await AsyncStorage.setItem(key, change(previous));
        return credential.current();
      } catch {
        if (credential.current()) setStorageError(true);
        return false;
      }
    });
    let storage: OwnerStorage | null = {
      epoch,
      read: (section) => serial(async () => {
        if (!credential.current()) return null;
        try {
          const data = await AsyncStorage.getItem(ownerStorageKey(epoch, section));
          return credential.current() ? data : null;
        } catch {
          if (credential.current()) setStorageError(true);
          return null;
        }
      }),
      write: (section, value) => update(section, () => value, false),
      update: (section, change) => update(section, change, true),
    };
    try {
      const [rawFence, rawAttempt] = await Promise.all([
        AsyncStorage.getItem(ownerStorageKey(epoch, 'scope')),
        AsyncStorage.getItem(ownerStorageKey(epoch, 'scope-attempt')),
      ]);
      const fence = readScopeFence(rawFence);
      const pending = readScopeAttempt(rawAttempt);
      if (!credential.current()) return;
      scope.current = fence.epoch;
      scopeFence.current = fence;
      attempt.current = pending;
      setScopeEpoch(fence.epoch);
      setScopePair(fence.pair);
      setScopeAttempt(pending);
    } catch {
      if (!credential.current()) return;
      setStorageError(true);
      storage = null;
    }
    setEnded(null);
    setActive({ workspace, credential, attestation, storage });
  }, [isCurrentCredential, lease, serial]);

  // A pilot credential and its query cache are memory-only. The stored demo is parked until the pilot ends.
  const closePilot = useCallback(async (expired = false, reference: string | null = null) => {
    if (!pilotActive.current) return;
    const id = block();
    pilotActive.current = false;
    setEnded(expired ? 'pilot-expired' : null);
    setPilotEndReference(reference);
    await serial(async () => {
      const previous = control.current;
      if (!isCurrentCredential(id) || previous?.kind !== 'confirmed' || !isUnexpired(previous.workspace)) return;
      await activate(previous, id);
      if (expired && isCurrentCredential(id)) setEnded('pilot-expired');
    });
  }, [activate, block, isCurrentCredential, serial]);

  const openPilot = useCallback(async (code: string, stillOpen: () => boolean) => {
    if (isKnownOffline()) throw ApiError.offline();
    const before = generation.current;
    const session = await getPilotSession(code);
    if (!stillOpen() || !isCurrentCredential(before)) throw ApiError.revoked();
    const site = await getPilotSite(session.site_id, code);
    if (!stillOpen() || !isCurrentCredential(before)) throw ApiError.revoked();
    const today = localParts(site.now, site.timezone).date;
    const workspace: Workspace = {
      token: code, siteId: site.id, scenarioId: null, expiresAt: session.expires_at,
      initialPeriod: { preset: 'today', start_date: today, end_date: today },
    };
    if (!isUnexpired(workspace)) throw new ApiError('PILOT_ACCESS_EXPIRED',
      'Kode akses sudah kedaluwarsa. Minta kode baru dari pengelola uji coba.', { retryable: false });
    const id = block();
    pilotActive.current = true;
    setEnded(null);
    const current = () => {
      if (!isCurrentCredential(id)) return false;
      if (isUnexpired(workspace)) return true;
      void closePilot(true);
      return false;
    };
    const credential: RequestCredential = {
      token: code, signal: controller.current.signal, current,
      reject: (error) => { if (isCurrentCredential(id)) void closePilot(true, error.requestId); },
    };
    setActive({ workspace, credential, attestation: null, storage: null });
  }, [block, closePilot, isCurrentCredential]);

  // Called inside the serialized lifecycle queue. A superseded save remains visible only to the queued revoker.
  const install = useCallback(async (workspace: Workspace, id: number, legacyImport = false) => {
    const attestation = await attestWorkspace(workspace, legacyImport);
    if (!isCurrentCredential(id)) return;
    const record = { kind: 'confirmed', workspace, attestation } as const;
    await saveWorkspace(workspace, attestation);
    control.current = record;
    await activate(record, id);
  }, [activate, isCurrentCredential]);

  const revokeCurrent = useCallback(async (id: number, recoverable = false) => {
    const previous = control.current;
    if (!previous) return;
    if (recoverable) await revokeWorkspace(previous.workspace);
    else await tombstoneWorkspace();
    control.current = recoverable ? { kind: 'revoked', workspace: previous.workspace } : null;
    await clean(previous, id);
  }, [clean]);

  const open = useCallback(async (workspace: Workspace, response?: DemoSession) => {
    if (!isUnexpired(workspace)) throw ApiError.expired();
    const id = block();
    pilotActive.current = false;
    await serial(async () => {
      if (!isCurrentCredential(id)) throw ApiError.revoked();
      try {
        await revokeCurrent(id);
        if (!isCurrentCredential(id)) throw ApiError.revoked();
        if (!isMatchingCreate(workspace, response)) await confirmDemoSite(workspace.siteId, lease(workspace, id));
        await install(workspace, id);
      } catch (error) {
        if (!(error instanceof ApiError)) {
          if (isCurrentCredential(id)) setStorageError(true);
          throw ApiError.storage();
        }
        throw error;
      }
    });
    if (!isCurrentCredential(id)) throw ApiError.revoked();
  }, [block, install, isCurrentCredential, lease, revokeCurrent, serial]);

  const persistFence = useCallback(async (fence: ScopeFence) => {
    if (!active?.credential.current() || !active.storage) return false;
    if (await active.storage.write('scope', JSON.stringify(fence))) return true;
    // A durable attempt already protects a reload. External changes without one require namespace revocation.
    if (!active.credential.current() || attempt.current) return false;
    await serial(async () => {
      if (!active.credential.current() || attempt.current) return;
      try {
        await revokeCurrent(credentialGeneration);
      } catch {
        try {
          await clearWorkspace();
          control.current = null;
        } catch {
          setStorageError(true);
        }
      }
      if (active.credential.current()) setActive({ ...active, storage: null });
    });
    return false;
  }, [active, credentialGeneration, revokeCurrent, serial]);

  const cancelScopedReads = useCallback((epoch: number) => {
    void queryClient.cancelQueries({
      predicate: ({ queryKey }) =>
        ['summary', 'asset-summary', 'asset-history', 'insights', 'hidden-insights', 'scope-selection'].includes(String(queryKey[0])) &&
        queryKey.at(-1) !== epoch,
    });
  }, [queryClient]);

  const advanceScope = useCallback(async () => {
    if (!active?.credential.current()) return;
    const epoch = ++scope.current;
    locallyAdvanced.current = true;
    scopeEvidence.current = {};
    const fence = { ...scopeFence.current, epoch };
    scopeFence.current = fence;
    cancelScopedReads(epoch);
    setScopeEpoch(epoch);
    fenceWrite.current = persistFence(fence);
    await fenceWrite.current;
  }, [active, cancelScopedReads, persistFence]);

  const clearAttempt = useCallback(async (marker: ScopeAttempt) => {
    if (!active?.storage || !active.credential.current()) return false;
    if (attempt.current !== marker) return attempt.current === null;
    const cleared = await active.storage.update('scope-attempt', (raw) =>
      readScopeAttempt(raw)?.id === marker.id ? 'null' : (raw ?? 'null'));
    if (cleared && attempt.current === marker && active.credential.current()) {
      attempt.current = null;
      setScopeAttempt(null);
    }
    return cleared;
  }, [active]);

  const isScopeCurrent = useCallback((epoch: number, pair: ScopePair) => {
    const fence = scopeFence.current;
    return epoch === fence.epoch && fence.pair !== null && compareScopePairs(fence.pair, pair) === 0;
  }, []);

  const observeScope = useCallback((pair: ScopePair, evidence: ScopeEvidence, publish?: (epoch: number) => void) => {
    if (!active?.credential.current()) return null;
    const before = scopeFence.current;
    const order = before.pair === null ? 1 : compareScopePairs(pair, before.pair);
    if (order < 0) return null;
    const previous = order === 0 ? scopeEvidence.current : {};
    const rawIds = evidence.rawIds ?? previous.rawIds;
    const summary = evidence.summary ?? previous.summary;
    if ((evidence.rawIds && previous.rawIds && !sameScopeIds(evidence.rawIds, previous.rawIds)) ||
      (rawIds && summary && !summaryMatchesMembership(summary, rawIds)) ||
      (evidence.summary && previous.summary && !sameScopeIds(
        evidence.summary.scope.included.map((asset) => asset.asset_id), previous.summary.scope.included.map((asset) => asset.asset_id),
      ))) throw ApiError.unexpected();

    scopeEvidence.current = { rawIds, summary };
    const epoch = before.epoch + Number(order > 0 && before.pair !== null && !locallyAdvanced.current);
    locallyAdvanced.current = false;
    if (order > 0) {
      const fence = { epoch, pair };
      scopeFence.current = fence;
      scope.current = epoch;
      fenceWrite.current = persistFence(fence);
    }
    publish?.(epoch);
    if (order > 0) setScopePair(pair);
    if (epoch !== before.epoch) {
      cancelScopedReads(epoch);
      setScopeEpoch(epoch);
    }
    const durable = fenceWrite.current.then(async (stored) => {
      const pending = attempt.current;
      if (stored && pending && active.credential.current() && compareScopePairs(pair, pending.base) > 0) {
        return clearAttempt(pending);
      }
      return stored;
    });
    return { epoch, durable };
  }, [active, cancelScopedReads, clearAttempt, persistFence]);

  const beginScopeWrite = useCallback(async (base: ScopePair, epoch: number): Promise<ScopeWrite> => {
    if (!active?.credential.current()) throw ApiError.revoked();
    if (!active.storage) throw ApiError.storage();
    if (isKnownOffline()) throw ApiError.offline();
    if (inFlight.current || !isScopeCurrent(epoch, base)) throw ApiError.revoked();
    const id = randomToken(16);
    inFlight.current = id;
    setScopeWriting(true);
    try {
      const pending = attempt.current;
      if (pending && compareScopePairs(base, pending.base) <= 0) return { id, sole: false };
      // A previous marker cannot protect a write at a higher base, where that marker may be reconciled.
      if (pending && !await fenceWrite.current) throw ApiError.storage();
      if (!active.credential.current() || !isScopeCurrent(epoch, base)) throw ApiError.revoked();
      const marker = { id, base };
      if (!await active.storage.write('scope-attempt', JSON.stringify(marker))) throw ApiError.storage();
      if (!active.credential.current()) throw ApiError.revoked();
      attempt.current = marker;
      setScopeAttempt(marker);
      return { id, sole: true };
    } catch (failure) {
      if (inFlight.current === id) {
        inFlight.current = null;
        setScopeWriting(false);
      }
      throw failure;
    }
  }, [active, isScopeCurrent]);

  const finishScopeWrite = useCallback(async (write: ScopeWrite, definite: boolean) => {
    if (inFlight.current !== write.id || !active?.credential.current()) return false;
    const pending = attempt.current;
    const cleared = definite && write.sole && pending?.id === write.id ? await clearAttempt(pending) : true;
    if (inFlight.current === write.id) {
      inFlight.current = null;
      setScopeWriting(false);
    }
    return cleared;
  }, [active, clearAttempt]);

  const resetDemo = useCallback(async () => {
    const record = control.current;
    if (pilotActive.current || record?.kind !== 'confirmed' || !active?.credential.current()) throw ApiError.revoked();
    if (isKnownOffline()) throw ApiError.offline();
    const id = block();
    await serial(async () => {
      if (!isCurrentCredential(id)) return;
      try {
        await revokeCurrent(id, true);
        if (!isCurrentCredential(id)) return;
        const result = await resetDemoSession(lease(record.workspace, id));
        if (result.site_id !== record.workspace.siteId || result.scenario_id !== record.workspace.scenarioId) {
          throw ApiError.unexpected();
        }
        await install({
          ...record.workspace,
          expiresAt: result.expires_at,
          initialPeriod: result.initial_period,
        }, id);
      } catch (error) {
        if (!(error instanceof ApiError)) {
          if (isCurrentCredential(id)) setStorageError(true);
          throw ApiError.storage();
        }
        throw error;
      }
    });
  }, [active, block, install, isCurrentCredential, lease, revokeCurrent, serial]);

  const validateOnline = useCallback(async (id: number) => {
    const stored = control.current;
    if (pilotActive.current || !stored || !isCurrentCredential(id)) return;
    if (!isUnexpired(stored.workspace)) {
      void end('expired');
      return;
    }
    if (isKnownOffline()) return;
    const credential = lease(stored.workspace, id);
    try {
      await confirmDemoSite(stored.workspace.siteId, credential);
      if (stored.kind !== 'confirmed') {
        await serial(async () => {
          if (control.current !== stored || !credential.current()) return;
          await install(stored.workspace, id, stored.kind === 'legacy');
        });
      }
    } catch (failure) {
      if (!isCurrentCredential(id)) return;
      const error = ApiError.from(failure);
      if (endsSession(error) || error.status === 404) void end('expired');
      else if (!(failure instanceof ApiError)) setStorageError(true);
    }
  }, [end, install, isCurrentCredential, lease, serial]);

  useEffect(() => {
    let mounted = true;
    const id = generation.current;
    async function load() {
      try {
        const stored = await serial(loadWorkspaceRecord);
        if (!mounted || !isCurrentCredential(id)) return;
        control.current = stored;
        if (stored && !isUnexpired(stored.workspace)) void end('expired');
        else if (stored?.kind === 'confirmed') await activate(stored, id);
        else if (stored) await validateOnline(id);
      } catch {
        if (mounted && isCurrentCredential(id)) setStorageError(true);
      } finally {
        if (mounted) setStatus('ready');
      }
    }
    void load();
    const unsubscribeOnline = onlineManager.subscribe((online) => {
      if (online) void validateOnline(generation.current);
    });
    const unsubscribeFocus = focusManager.subscribe((focused) => {
      if (focused) void validateOnline(generation.current);
    });
    return () => {
      mounted = false;
      unsubscribeOnline();
      unsubscribeFocus();
    };
  }, [activate, end, isCurrentCredential, serial, validateOnline]);

  useEffect(() => {
    if (!active) return;
    let timer: ReturnType<typeof setTimeout>;
    const check = () => {
      if (!active.credential.current()) return;
      timer = setTimeout(check, Math.min(2_147_483_647, Date.parse(active.workspace.expiresAt) - Date.now()));
    };
    check();
    return () => clearTimeout(timer);
  }, [active]);

  const value = useMemo(() => ({
    status, workspace: active?.workspace ?? null, credential: active?.credential ?? null,
    storage: active?.storage ?? null, legacyImport: active?.attestation?.legacyImport ?? false,
    pilot: active?.attestation === null, openPilot, closePilot,
    credentialGeneration, isCurrentCredential, scopeEpoch, currentScopeEpoch, currentScopePair, advanceScope,
    scopePair, scopeAttempt, scopeWriting, isScopeCurrent, observeScope, beginScopeWrite, finishScopeWrite,
    ended, pilotEndReference, storageError, open, end, resetDemo,
  }), [status, active, credentialGeneration, isCurrentCredential, scopeEpoch, currentScopeEpoch, currentScopePair, advanceScope,
    scopePair, scopeAttempt, scopeWriting, isScopeCurrent, observeScope, beginScopeWrite, finishScopeWrite,
    ended, pilotEndReference, storageError, open, end, resetDemo, openPilot, closePilot]);

  return (
    <QueryClientProvider client={queryClient}>
      <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>
    </QueryClientProvider>
  );
}

export function useWorkspace(): WorkspaceValue {
  const value = useContext(WorkspaceContext);
  if (!value) throw new Error('useWorkspace needs WorkspaceProvider');
  return value;
}

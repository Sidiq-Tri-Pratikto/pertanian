import AsyncStorage from '@react-native-async-storage/async-storage';
import { focusManager, onlineManager, QueryClientProvider } from '@tanstack/react-query';
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { Platform } from 'react-native';

import { confirmDemoSite, resetDemoSession, type DemoSession, type RequestCredential } from '@/api/client';
import { ApiError } from '@/api/errors';
import { createQueryClient, endsSession } from '@/api/query-client';
import { ownerStorageKey, removeOwnerData, type OwnerStorage, type StorageSection } from '@/features/offline/owner-storage';
import { isKnownOffline } from '@/features/offline/useConnectivity';
import {
  attestWorkspace, clearWorkspace, isUnexpired, loadWorkspaceRecord, revokeWorkspace, saveWorkspace, tombstoneWorkspace,
  type Attestation, type Workspace, type WorkspaceRecord,
} from '@/features/workspace/workspace-store';

type Active = {
  workspace: Workspace;
  credential: RequestCredential;
  attestation: Attestation;
  storage: OwnerStorage | null;
};

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
  advanceScope: () => Promise<void>;
  ended: 'expired' | null;
  storageError: boolean;
  open: (workspace: Workspace, response?: DemoSession) => Promise<void>;
  end: (reason: 'expired' | null) => Promise<void>;
  resetDemo: () => Promise<void>;
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
  const [ended, setEnded] = useState<'expired' | null>(null);
  const [storageError, setStorageError] = useState(false);
  const [queryClient] = useState(createQueryClient);
  const generation = useRef(0);
  const [credentialGeneration, setCredentialGeneration] = useState(0);
  const scope = useRef(0);
  const [scopeEpoch, setScopeEpoch] = useState(0);
  const control = useRef<WorkspaceRecord | null>(null);
  const controller = useRef(new AbortController());
  const tail = useRef<Promise<unknown>>(Promise.resolve());
  const isCurrentCredential = useCallback((id: number) => generation.current === id, []);
  const currentScopeEpoch = useCallback(() => scope.current, []);

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
    setScopeEpoch(0);
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
      const raw = await AsyncStorage.getItem(ownerStorageKey(epoch, 'scope'));
      const persistedScope = raw === null ? 0 : Number(raw);
      if (!Number.isSafeInteger(persistedScope) || persistedScope < 0) throw ApiError.storage();
      if (!credential.current()) return;
      scope.current = persistedScope;
      setScopeEpoch(persistedScope);
    } catch {
      if (!credential.current()) return;
      setStorageError(true);
      storage = null;
    }
    setEnded(null);
    setActive({ workspace, credential, attestation, storage });
  }, [isCurrentCredential, lease, serial]);

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

  const advanceScope = useCallback(async () => {
    if (!active?.credential.current()) return;
    const next = ++scope.current;
    void queryClient.cancelQueries({
      predicate: ({ queryKey }) => ['summary', 'asset-summary', 'asset-history', 'insights', 'hidden-insights'].includes(String(queryKey[0])),
    });
    setScopeEpoch(next);
    if (!active.storage || await active.storage.write('scope', String(next)) || !active.credential.current()) return;
    // An old namespace must not become current again after a failed durable scope update.
    await serial(async () => {
      if (!active.credential.current()) return;
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
  }, [active, credentialGeneration, queryClient, revokeCurrent, serial]);

  const resetDemo = useCallback(async () => {
    const record = control.current;
    if (record?.kind !== 'confirmed' || !active?.credential.current()) throw ApiError.revoked();
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
    if (!stored || !isCurrentCredential(id)) return;
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
    storage: active?.storage ?? null, legacyImport: active?.attestation.legacyImport ?? false,
    credentialGeneration, isCurrentCredential, scopeEpoch, currentScopeEpoch, advanceScope,
    ended, storageError, open, end, resetDemo,
  }), [status, active, credentialGeneration, isCurrentCredential, scopeEpoch, currentScopeEpoch, advanceScope,
    ended, storageError, open, end, resetDemo]);

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

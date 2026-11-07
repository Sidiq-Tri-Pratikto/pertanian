import { QueryClientProvider } from '@tanstack/react-query';
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';

import { createQueryClient, endsSession } from '@/api/query-client';
import { clearWorkspace, loadWorkspace, saveWorkspace, type Workspace } from '@/features/workspace/workspace-store';

type WorkspaceValue = {
  status: 'loading' | 'ready';
  workspace: Workspace | null;
  /** Opaque cache identity. It changes even when a replacement credential opens the same site. */
  credentialGeneration: number;
  isCurrentCredential: (generation: number) => boolean;
  /** Set when a stored workspace stopped working, so the app can explain it once. */
  ended: 'expired' | null;
  open: (workspace: Workspace) => Promise<void>;
  end: (reason: 'expired' | null) => Promise<void>;
};

const WorkspaceContext = createContext<WorkspaceValue | null>(null);

/** Holds the device's workspace and the one query client, and keeps cached server state separate per workspace. */
export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<'loading' | 'ready'>('loading');
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [ended, setEnded] = useState<'expired' | null>(null);
  const [queryClient] = useState(createQueryClient);
  const currentGeneration = useRef(0);
  const [credentialGeneration, setCredentialGeneration] = useState(0);
  const isCurrentCredential = useCallback((generation: number) => currentGeneration.current === generation, []);

  const end = useCallback(
    async (reason: 'expired' | null) => {
      setCredentialGeneration(++currentGeneration.current);
      setWorkspace(null);
      setEnded(reason);
      queryClient.clear();
      await clearWorkspace();
    },
    [queryClient],
  );

  // A rejected credential ends the workspace and its cached data, wherever the query ran.
  useEffect(
    () =>
      queryClient.getQueryCache().subscribe((event) => {
        if (event.type === 'updated' && event.action.type === 'error' && endsSession(event.action.error)) {
          void end('expired');
        }
      }),
    [queryClient, end],
  );

  useEffect(() => {
    let active = true;
    loadWorkspace().then((stored) => {
      if (!active) {
        return;
      }
      if (stored && Date.parse(stored.expiresAt) <= Date.now()) {
        void end('expired');
      } else {
        setWorkspace(stored);
      }
      setStatus('ready');
    });
    return () => {
      active = false;
    };
  }, [end]);

  const open = useCallback(
    async (next: Workspace) => {
      const generation = ++currentGeneration.current;
      queryClient.clear();
      try {
        await saveWorkspace(next);
      } catch (error) {
        if (isCurrentCredential(generation)) setCredentialGeneration(generation);
        throw error;
      }
      if (!isCurrentCredential(generation)) return;
      setCredentialGeneration(generation);
      setEnded(null);
      setWorkspace(next);
    },
    [queryClient, isCurrentCredential],
  );

  const value = useMemo(
    () => ({ status, workspace, credentialGeneration, isCurrentCredential, ended, open, end }),
    [status, workspace, credentialGeneration, isCurrentCredential, ended, open, end],
  );
  return (
    <QueryClientProvider client={queryClient}>
      <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>
    </QueryClientProvider>
  );
}

export function useWorkspace(): WorkspaceValue {
  const value = useContext(WorkspaceContext);
  if (!value) {
    throw new Error('useWorkspace needs WorkspaceProvider');
  }
  return value;
}

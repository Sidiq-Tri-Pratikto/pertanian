import { QueryClientProvider } from '@tanstack/react-query';
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

import { createQueryClient, endsSession } from '@/api/query-client';
import { clearWorkspace, loadWorkspace, saveWorkspace, type Workspace } from '@/features/workspace/workspace-store';

type WorkspaceValue = {
  status: 'loading' | 'ready';
  workspace: Workspace | null;
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

  const end = useCallback(
    async (reason: 'expired' | null) => {
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
      queryClient.clear();
      await saveWorkspace(next);
      setEnded(null);
      setWorkspace(next);
    },
    [queryClient],
  );

  const value = useMemo(() => ({ status, workspace, ended, open, end }), [status, workspace, ended, open, end]);
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

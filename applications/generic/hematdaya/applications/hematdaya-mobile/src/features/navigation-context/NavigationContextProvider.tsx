import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';

import type { PeriodQuery } from '@/api/client';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';
import type { Period } from '@/features/workspace/workspace-store';

/** An observation just hidden from the evidence screen, so the screen it returns to can offer Pulihkan. */
export type HiddenItem = { id: string; revision: number; title: string };

type NavigationContextValue = {
  period: Period | null;
  setPeriod: (period: Period) => void;
  recentlyHidden: HiddenItem | null;
  setRecentlyHidden: (item: HiddenItem | null) => void;
};

const NavigationContext = createContext<NavigationContextValue>({
  period: null,
  setPeriod: () => undefined,
  recentlyHidden: null,
  setRecentlyHidden: () => undefined,
});

/** Presets the service resolves against site time; anything else is an explicit local range. */
const SERVICE_PRESETS = new Set(['today', 'this_week', 'last_7_days']);

export function periodQuery(period: Period): PeriodQuery {
  return SERVICE_PRESETS.has(period.preset)
    ? { preset: period.preset }
    : { start_date: period.start_date, end_date: period.end_date };
}

/** Period and site for every tab, starting from the period the service acknowledged for this workspace. */
export function NavigationContextProvider({ children }: { children: ReactNode }) {
  const { workspace } = useWorkspace();
  const [chosen, setChosen] = useState<{ siteId: string; period: Period } | null>(null);
  const [recentlyHidden, setRecentlyHidden] = useState<HiddenItem | null>(null);
  const period =
    workspace === null ? null : chosen?.siteId === workspace.siteId ? chosen.period : workspace.initialPeriod;

  const value = useMemo(
    () => ({
      period,
      setPeriod: (next: Period) => workspace && setChosen({ siteId: workspace.siteId, period: next }),
      recentlyHidden,
      setRecentlyHidden,
    }),
    [period, recentlyHidden, workspace],
  );
  return <NavigationContext.Provider value={value}>{children}</NavigationContext.Provider>;
}

export function useNavigationContext(): NavigationContextValue {
  return useContext(NavigationContext);
}

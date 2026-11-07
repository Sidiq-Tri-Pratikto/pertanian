import { keepPreviousData, useQuery } from '@tanstack/react-query';

import { getInsight, getInsights } from '@/api/client';
import { periodQuery, useNavigationContext } from '@/features/navigation-context/NavigationContextProvider';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';

/** Observations and notices for the shared period. */
export function useInsights() {
  const { workspace } = useWorkspace();
  const { period } = useNavigationContext();
  return useQuery({
    queryKey: ['insights', workspace?.siteId, period],
    queryFn: () => getInsights(workspace!.siteId, periodQuery(period!), workspace!.token),
    enabled: workspace !== null && period !== null,
    placeholderData: keepPreviousData,
  });
}

/** One frozen evidence revision; the revision is part of the key so a newer one never replaces it. */
export function useInsight(insightId: string | undefined, revision: number | undefined) {
  const { workspace } = useWorkspace();
  return useQuery({
    queryKey: ['insight', insightId, revision],
    queryFn: () => getInsight(insightId!, revision!, workspace!.token),
    enabled: workspace !== null && insightId !== undefined && revision !== undefined && revision >= 1,
    staleTime: Infinity,
  });
}

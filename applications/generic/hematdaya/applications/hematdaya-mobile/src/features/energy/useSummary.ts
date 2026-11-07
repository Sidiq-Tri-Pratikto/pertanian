import { keepPreviousData, useQuery } from '@tanstack/react-query';

import { getSummary } from '@/api/client';
import { periodQuery, useNavigationContext } from '@/features/navigation-context/NavigationContextProvider';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';

/** The site summary for the shared period. A refresh keeps the confirmed numbers on screen until new ones arrive. */
export function useSummary() {
  const { workspace } = useWorkspace();
  const { period } = useNavigationContext();
  return useQuery({
    queryKey: ['summary', workspace?.siteId, period],
    queryFn: () => getSummary(workspace!.siteId, periodQuery(period!), workspace!.token),
    enabled: workspace !== null && period !== null,
    placeholderData: keepPreviousData,
  });
}

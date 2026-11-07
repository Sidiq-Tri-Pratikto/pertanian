import { keepPreviousData, useQuery } from '@tanstack/react-query';

import { getSummary } from '@/api/client';
import { assetKeys } from '@/features/assets/useAssets';
import { periodQuery, useNavigationContext } from '@/features/navigation-context/NavigationContextProvider';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';

/** The site summary for the shared period. A refresh keeps the confirmed numbers on screen until new ones arrive. */
export function useSummary() {
  const { workspace, credentialGeneration } = useWorkspace();
  const { period } = useNavigationContext();
  return useQuery({
    queryKey: [...assetKeys(workspace?.siteId, credentialGeneration).summary, period],
    queryFn: () => getSummary(workspace!.siteId, periodQuery(period!), workspace!.token),
    enabled: workspace !== null && period !== null,
    structuralSharing: false,
    placeholderData: keepPreviousData,
  });
}

import { keepPreviousData, useQuery } from '@tanstack/react-query';

import { getAssetSummary } from '@/api/client';
import { periodQuery, useNavigationContext } from '@/features/navigation-context/NavigationContextProvider';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';

/** One asset's summary for the shared period. */
export function useAssetSummary(assetId: string | undefined) {
  const { workspace } = useWorkspace();
  const { period } = useNavigationContext();
  return useQuery({
    queryKey: ['asset-summary', workspace?.siteId, assetId, period],
    queryFn: () => getAssetSummary(assetId!, periodQuery(period!), workspace!.token),
    enabled: workspace !== null && period !== null && assetId !== undefined,
    placeholderData: keepPreviousData,
  });
}

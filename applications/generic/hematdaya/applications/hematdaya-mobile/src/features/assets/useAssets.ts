import { useQuery } from '@tanstack/react-query';

import { getAsset, getAssets } from '@/api/client';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';

/** Every asset of the workspace, for the location and category a summary row does not carry. */
export function useAssets() {
  const { workspace } = useWorkspace();
  return useQuery({
    queryKey: ['assets', workspace?.siteId],
    queryFn: () => getAssets(workspace!.siteId, workspace!.token),
    enabled: workspace !== null,
  });
}

/** One asset with its bindings and sources. */
export function useAsset(assetId: string | undefined) {
  const { workspace } = useWorkspace();
  return useQuery({
    queryKey: ['asset', assetId],
    queryFn: () => getAsset(assetId!, workspace!.token),
    enabled: workspace !== null && assetId !== undefined,
  });
}

import { CancelledError, keepPreviousData, useQuery } from '@tanstack/react-query';

import { getAssetSummary, getSummary } from '@/api/client';
import { ApiError } from '@/api/errors';
import { assetKeys } from '@/features/assets/useAssets';
import { periodQuery, useNavigationContext } from '@/features/navigation-context/NavigationContextProvider';
import { matchesSummary, type SummaryScope } from '@/features/offline/persist-queries';
import { isKnownOffline, useConnectivity } from '@/features/offline/useConnectivity';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';

/** Site and asset summaries share a single scoped GET and successful-read persistence path. */
export function useScopedSummary(scope: SummaryScope, requested = true) {
  const { workspace, credential, credentialGeneration, scopeEpoch, currentScopeEpoch } = useWorkspace();
  const { period, record, snapshot, fetchedAt } = useNavigationContext();
  useConnectivity();
  const offline = isKnownOffline();
  const keys = assetKeys(workspace?.siteId, credentialGeneration);
  const prefix = scope.kind === 'asset' ? keys.assetSummary(scope.assetId) : keys.summary;
  const saved = period ? snapshot(period, scope) : undefined;
  const query = useQuery({
    queryKey: [...prefix, period, scopeEpoch],
    queryFn: async () => {
      if (!workspace || !period || !credential || currentScopeEpoch() !== scopeEpoch) throw new CancelledError({ revert: true });
      const data = scope.kind === 'asset'
        ? await getAssetSummary(scope.assetId, periodQuery(period), credential)
        : await getSummary(workspace.siteId, periodQuery(period), credential);
      const completed = Date.now();
      if (!credential.current() || currentScopeEpoch() !== scopeEpoch) throw new CancelledError({ revert: true });
      if (!matchesSummary(data, period, scope)) throw ApiError.unexpected();
      record(data, period, scope, scopeEpoch, completed);
      return data;
    },
    enabled: credential !== null && period !== null && requested,
    initialData: saved?.data,
    initialDataUpdatedAt: saved?.fetchedAt,
    structuralSharing: false,
    placeholderData: offline ? undefined : keepPreviousData,
    refetchOnReconnect: 'always',
  });
  return {
    ...query, offline,
    confirmedAtFor: fetchedAt,
    previousSelection: query.isPlaceholderData,
    refresh: () => {
      if (!isKnownOffline()) void query.refetch();
    },
  };
}

/** The all-active site summary for the shared period. */
export function useSummary() {
  return useScopedSummary({ kind: 'all-active' });
}

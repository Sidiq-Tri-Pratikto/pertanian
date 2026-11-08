import { CancelledError, keepPreviousData, useQuery, useQueryClient } from '@tanstack/react-query';

import { compareScopePairs, getAssetSummary, getSummary, summaryScopePair, type Summary } from '@/api/client';
import { ApiError } from '@/api/errors';
import { assetKeys } from '@/features/assets/useAssets';
import { periodQuery, useNavigationContext } from '@/features/navigation-context/NavigationContextProvider';
import { matchesSummary, type SummaryScope } from '@/features/offline/persist-queries';
import { isKnownOffline, useConnectivity } from '@/features/offline/useConnectivity';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';
import type { Period } from '@/features/workspace/workspace-store';

/** Site and asset summaries share a single scoped GET and successful-read persistence path. */
export function useScopedSummary(scope: SummaryScope, requested = true) {
  const {
    workspace, credential, credentialGeneration, scopeEpoch, currentScopeEpoch, currentScopePair, scopePair, observeScope,
  } = useWorkspace();
  const { period, record, snapshot, fetchedAt } = useNavigationContext();
  const client = useQueryClient();
  useConnectivity();
  const offline = isKnownOffline();
  const keys = assetKeys(workspace?.siteId, credentialGeneration);
  const prefix = scope.kind === 'asset' ? keys.assetSummary(scope.assetId) : keys.summary;
  const saved = period ? snapshot(period, scope) : undefined;
  const previous = period ? snapshot(period, scope, true) : undefined;

  const options = (selected: Period | null, epoch: number) => ({
    queryKey: [...prefix, selected, epoch],
    queryFn: async () => {
      const current = () => Boolean(credential?.current()) && currentScopeEpoch() === epoch;
      if (!workspace || !selected || !credential || !current()) throw new CancelledError({ revert: true });
      const data = scope.kind === 'asset'
        ? await getAssetSummary(scope.assetId, periodQuery(selected), credential)
        : await getSummary(workspace.siteId, periodQuery(selected), credential);
      const completed = Date.now();
      if (!current()) throw new CancelledError({ revert: true });
      if (!matchesSummary(data, selected, scope)) throw ApiError.unexpected();
      const pair = scope.kind === 'all-active' ? summaryScopePair(data) : null;
      if (pair !== null) {
        const observed = observeScope(pair, { summary: data }, (nextEpoch) => {
          record(data, selected, scope, nextEpoch, completed);
          if (nextEpoch !== epoch) client.setQueryData([...prefix, selected, nextEpoch], data, { updatedAt: completed });
        });
        if (!observed) throw ApiError.unexpected();
      } else {
        if (scope.kind === 'all-active' && currentScopePair() !== null) throw ApiError.unexpected();
        record(data, selected, scope, epoch, completed);
      }
      return data;
    },
  });

  const query = useQuery({
    ...options(period, scopeEpoch),
    enabled: credential !== null && period !== null && requested,
    initialData: saved?.data,
    initialDataUpdatedAt: saved?.fetchedAt,
    structuralSharing: false,
    placeholderData: offline ? undefined : keepPreviousData,
    refetchOnReconnect: 'always',
  });
  const returnedPair = query.data ? summaryScopePair(query.data) : null;
  const earlierPair = scope.kind === 'all-active' && query.data !== undefined && scopePair !== null &&
    (returnedPair === null || compareScopePairs(returnedPair, scopePair) !== 0);
  const usingPrevious = earlierPair || query.isPlaceholderData || (query.data === undefined && previous !== undefined);
  return {
    ...query,
    data: query.data ?? previous?.data,
    isPlaceholderData: usingPrevious,
    offline,
    confirmedAtFor: fetchedAt,
    previousSelection: usingPrevious,
    refresh: () => {
      if (!isKnownOffline()) void query.refetch();
    },
    /** A write always verifies with a confirmed GET for its captured period, even after its screen closes. */
    readFresh: async (selected: Period) => {
      const epoch = currentScopeEpoch();
      try {
        return await client.fetchQuery({ ...options(selected, epoch), staleTime: 0, retry: false });
      } catch (failure) {
        const newer = currentScopeEpoch();
        const observed = newer !== epoch && client.getQueryData<Summary>([...prefix, selected, newer]);
        if (observed && credential?.current()) return observed;
        throw failure;
      }
    },
  };
}

/** The current site selection for the shared period. */
export function useSummary() {
  return useScopedSummary({ kind: 'all-active' });
}

import { CancelledError, isCancelledError, skipToken, useQuery } from '@tanstack/react-query';

import { getAssetHistory, type HistoryResponse, type HistorySelection } from '@/api/client';
import { ApiError, DEFAULT_MAX_ATTEMPTS } from '@/api/errors';
import { retryDelay } from '@/api/query-client';
import type { Workspace } from '@/features/workspace/workspace-store';

type HistoryRead = {
  open: boolean;
  workspace: Workspace | null;
  assetId: string;
  /** Pass only the confirmed asset summary window for the selected period. */
  confirmed: HistoryResponse['window'] | null;
};

type Operation = { result: Promise<HistoryResponse>; terminal: boolean };

// A cache entry owns its in-flight or terminal operation, even if its observer unmounts. Garbage collection
// of that entry releases the operation. A successful operation leaves the entry eligible for future refreshes.
const operations = new WeakMap<object, Operation>();

async function readWithBudget(
  read: () => Promise<HistoryResponse>,
  setWait: (attempt: number, failure: ApiError | null) => void,
): Promise<HistoryResponse> {
  let maxAttempts: number | undefined;
  for (let attempt = 1; ; attempt += 1) {
    try {
      return await read();
    } catch (error) {
      if (isCancelledError(error)) throw error;
      const failure = ApiError.from(error);
      const limit = failure.recovery.max_attempts ?? DEFAULT_MAX_ATTEMPTS;
      maxAttempts = Math.min(maxAttempts ?? limit, limit);
      if (failure.recovery.retryable !== true || !(attempt < maxAttempts)) throw failure;

      setWait(attempt, failure);
      await new Promise<void>((resolve) => setTimeout(resolve, retryDelay(attempt, failure)));
      setWait(attempt, null);
    }
  }
}

/** Load one confirmed asset period only on disclosure, with a single bounded retry sequence per read. */
export function useHistory({ open, workspace, assetId, confirmed }: HistoryRead) {
  const selection: HistorySelection | null = confirmed && {
    start_date: confirmed.start_date,
    end_date: confirmed.end_date,
    timezone: confirmed.timezone,
    bucket: confirmed.start_date === confirmed.end_date ? 'hour' : 'day',
  };
  const queryKey = ['asset-history', workspace?.siteId, assetId, selection] as const;
  const ready = workspace !== null && assetId.length > 0 && selection !== null;
  return useQuery<HistoryResponse, ApiError>({
    queryKey,
    enabled: (query) => open && ready && !operations.get(query)?.terminal,
    retry: false,
    queryFn: !ready ? skipToken : ({ client }) => {
      const query = client.getQueryCache().find<HistoryResponse, ApiError>({ queryKey });
      if (!query) throw new CancelledError({ revert: true });

      const existing = operations.get(query);
      if (existing) return existing.result;
      // A refetch of all cached keys can reach an inactive query. History starts only for an open observer.
      if (!query.isActive()) throw new CancelledError({ revert: true });

      const operation: Operation = {
        terminal: false,
        result: readWithBudget(
          () => {
            if (client.getQueryCache().find<HistoryResponse, ApiError>({ queryKey }) !== query) throw new CancelledError({ revert: true });
            return getAssetHistory(assetId, selection, workspace.token);
          },
          (attempt, failure) => query.setState({ fetchFailureCount: attempt, fetchFailureReason: failure }),
        ).then(
          (data) => {
            operations.delete(query);
            return data;
          },
          (failure: unknown) => {
            operation.terminal = true;
            throw failure;
          },
        ),
      };
      operations.set(query, operation);
      return operation.result;
    },
  });
}

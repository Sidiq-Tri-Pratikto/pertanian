import { CancelledError, isCancelledError, skipToken, useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query';

import { getArchivedAssets, getAsset, getAssets, type AssetPage, type Summary } from '@/api/client';
import { ApiError, DEFAULT_MAX_ATTEMPTS } from '@/api/errors';
import { retryDelay } from '@/api/query-client';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';

export function assetKeys(siteId: string | undefined, credential: number) {
  return {
    active: ['assets', siteId, credential] as const,
    archived: ['archived-assets', siteId, credential] as const,
    detail: (id: string | undefined) => ['asset', siteId, credential, id] as const,
    write: (id: string) => ['asset-write', siteId, credential, id] as const,
    summary: ['summary', siteId, credential] as const,
    assetSummary: (id: string | undefined) => ['asset-summary', siteId, credential, id] as const,
    previousScope: ['previous-asset-scope', siteId, credential] as const,
  };
}

/** One read owner. Each server cap includes the first call, and a later error can only lower the cap. */
export async function readAssetWithBudget<T>(
  read: () => Promise<T>,
  current: () => boolean,
  waiting?: (attempt: number, failure: ApiError) => void,
): Promise<T> {
  let limit = Infinity;
  for (let attempt = 1; current(); attempt += 1) {
    try {
      return await read();
    } catch (error) {
      if (isCancelledError(error)) throw error;
      const failure = ApiError.from(error);
      limit = Math.min(limit, failure.recovery.max_attempts ?? DEFAULT_MAX_ATTEMPTS);
      if (!current() || !failure.recovery.retryable || attempt >= limit) throw failure;
      waiting?.(attempt, failure);
      await new Promise<void>((resolve) => setTimeout(resolve, retryDelay(attempt, failure)));
    }
  }
  throw new CancelledError({ revert: true });
}

/** The active-only list supplies metadata that the ranked summary does not carry. */
export function useAssets() {
  const { workspace, credentialGeneration } = useWorkspace();
  const keys = assetKeys(workspace?.siteId, credentialGeneration);
  return useQuery({
    queryKey: keys.active,
    queryFn: () => getAssets(workspace!.siteId, workspace!.token),
    enabled: workspace !== null,
  });
}

export type ArchiveRead = AssetPage & { incomplete?: boolean };

const archiveReadFailures = new WeakMap<object, ApiError>();
const archiveReads = new WeakMap<object, object>();

/** Publication invalidates a read that started before the confirmed change. */
export function cancelArchiveRead(client: QueryClient, queryKey: readonly unknown[]) {
  const entry = client.getQueryCache().find({ queryKey });
  if (entry) archiveReads.delete(entry);
}

/** Archive cursor reads are independent of site summaries and keep their terminal budget on reopen. */
export function useArchivedAssets(open: boolean) {
  const { workspace, credentialGeneration, isCurrentCredential } = useWorkspace();
  const queryKey = assetKeys(workspace?.siteId, credentialGeneration).archived;
  const queryClient = useQueryClient();
  const query = useQuery<ArchiveRead, ApiError>({
    queryKey,
    enabled: (entry) => open && workspace !== null && !archiveReadFailures.has(entry),
    retry: false,
    gcTime: Infinity,
    retryOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    queryFn: async ({ client }) => {
      const entry = client.getQueryCache().find<ArchiveRead, ApiError>({ queryKey });
      if (!entry || !workspace) throw new CancelledError({ revert: true });
      const terminal = archiveReadFailures.get(entry);
      if (terminal) throw terminal;
      const read = {};
      archiveReads.set(entry, read);
      const current = () => archiveReads.get(entry) === read && isCurrentCredential(credentialGeneration);
      let partial: AssetPage | undefined;
      try {
        return await getArchivedAssets(
          workspace.siteId,
          workspace.token,
          (readPage) => readAssetWithBudget(readPage, current, (attempt, failure) =>
            entry.setState({ fetchFailureCount: attempt, fetchFailureReason: failure }),
          ),
          (page) => { partial = page; },
        );
      } catch (error) {
        if (!current()) throw new CancelledError({ revert: true });
        if (partial && (!entry.state.data || entry.state.data.incomplete)) {
          const items = new Map((entry.state.data?.items ?? []).map((asset) => [asset.id, asset]));
          for (const asset of partial.items) items.set(asset.id, asset);
          client.setQueryData<ArchiveRead>(queryKey, { ...partial, items: [...items.values()] });
        }
        const failure = ApiError.from(error);
        archiveReadFailures.set(entry, failure);
        throw failure;
      } finally {
        if (archiveReads.get(entry) === read) archiveReads.delete(entry);
      }
    },
  });
  const entry = query.error === null ? queryClient.getQueryCache().find({ queryKey }) : undefined;
  return { ...query, error: (entry && archiveReadFailures.get(entry)) ?? query.error };
}

/** One owned asset with its bindings and sources. */
export function useAsset(assetId: string | undefined) {
  const { workspace, credentialGeneration } = useWorkspace();
  const keys = assetKeys(workspace?.siteId, credentialGeneration);
  return useQuery({
    queryKey: keys.detail(assetId),
    queryFn: () => getAsset(assetId!, workspace!.token),
    enabled: workspace !== null && assetId !== undefined,
  });
}

/** Cached site summaries that predate a confirmed membership change. */
export type PreviousAssetScope = { summaries: WeakSet<Summary>; restored: ReadonlySet<string> };

export function usePreviousAssetScope() {
  const { workspace, credentialGeneration } = useWorkspace();
  return useQuery<PreviousAssetScope>({
    queryKey: assetKeys(workspace?.siteId, credentialGeneration).previousScope,
    queryFn: skipToken,
    enabled: false,
    gcTime: Infinity,
  }).data;
}

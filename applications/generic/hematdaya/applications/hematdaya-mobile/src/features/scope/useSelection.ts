import { currentCopy } from '@/features/localization/messages';
import { CancelledError, skipToken, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  compareScopePairs, confirmScope, getSelection, isScopeRefusal, selectionScopePair, summaryScopePair,
  type ScopePreview, type ScopeProposal, type ScopeSelection, type Summary,
} from '@/api/client';
import { ApiError } from '@/api/errors';
import { useScopedSummary } from '@/features/energy/useSummary';
import { isKnownOffline } from '@/features/offline/useConnectivity';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';
import type { Period } from '@/features/workspace/workspace-store';

export type ScopeReview = {
  proposal: ScopeProposal;
  response: ScopePreview;
  base: ScopeSelection;
  period: Period;
  epoch: number;
};

type SaveStatus = (
  | { kind: 'saving'; dispatched: boolean }
  | { kind: 'checking' | 'acknowledged' | 'observed' }
  | { kind: 'unsent' | 'refused' | 'stale' | 'uncertain' | 'check-failed' | 'refresh-failed'; error: ApiError }
  | { kind: 'local-failed'; refreshError: ApiError | null }
) & { knownAttemptId?: string };

export function scopeReviewStale(): ApiError {
  return new ApiError('SCOPE_STALE', currentCopy("Cakupan atau periode berubah. Tinjau kembali pratinjau sebelum menyimpan.", "Scope or period changed. Review a new preview before saving."), { retryable: false });
}

/** One owned bounded GET. Membership stays raw until a matching confirmed summary resolves eligibility. */
export function useSelection() {
  const { workspace, credential, credentialGeneration, scopeEpoch, currentScopeEpoch, observeScope } = useWorkspace();
  const client = useQueryClient();
  const prefix = ['scope-selection', workspace?.siteId, credentialGeneration] as const;
  const options = (epoch: number) => ({
    queryKey: [...prefix, epoch],
    queryFn: async () => {
      const current = () => Boolean(credential?.current()) && currentScopeEpoch() === epoch;
      if (!workspace || !credential || !current()) throw new CancelledError({ revert: true });
      const data = await getSelection(workspace.siteId, credential);
      if (!current()) throw new CancelledError({ revert: true });
      const observed = observeScope(selectionScopePair(data), { rawIds: data.selected_asset_ids }, (next) => {
        if (next !== epoch) client.setQueryData([...prefix, next], data);
      });
      if (!observed) throw ApiError.unexpected();
      return data;
    },
    retry: false,
  });
  const query = useQuery({ ...options(scopeEpoch), enabled: credential !== null });
  return {
    ...query,
    publish: (data: ScopeSelection) => observeScope(selectionScopePair(data), { rawIds: data.selected_asset_ids }, (epoch) =>
      client.setQueryData([...prefix, epoch], data)),
    readFresh: async () => {
      const epoch = currentScopeEpoch();
      try {
        return await client.fetchQuery({ ...options(epoch), staleTime: 0 });
      } catch (failure) {
        const newer = currentScopeEpoch();
        const observed = newer !== epoch && client.getQueryData<ScopeSelection>([...prefix, newer]);
        if (observed && credential?.current()) return observed;
        throw failure;
      }
    },
  };
}

/** The owned save and observation survive route unmounts. Drafts never enter this cache. */
export function useScopeSave(
  selection: ReturnType<typeof useSelection>,
  summary: ReturnType<typeof useScopedSummary>,
) {
  const {
    workspace, credential, credentialGeneration, currentScopeEpoch, isScopeCurrent,
    beginScopeWrite, finishScopeWrite, scopeWriting, scopeAttempt, scopePair,
  } = useWorkspace();
  const client = useQueryClient();
  const key = ['scope-write', workspace?.siteId, credentialGeneration] as const;
  const { data: status } = useQuery<SaveStatus>({ queryKey: key, queryFn: skipToken, enabled: false, gcTime: Infinity });
  const current = () => Boolean(credential?.current());
  const setStatus = (state: SaveStatus) => { if (current()) client.setQueryData(key, state); };
  const pending = scopeAttempt !== null && scopeAttempt.id !== status?.knownAttemptId && (scopePair === null || compareScopePairs(scopePair, scopeAttempt.base) <= 0);

  async function verifySummary(period: Period): Promise<Summary> {
    if (isKnownOffline()) throw ApiError.offline();
    const result = await summary.readFresh(period);
    const pair = summaryScopePair(result);
    if (!pair || !isScopeCurrent(currentScopeEpoch(), pair) || !current()) throw ApiError.unexpected();
    return result;
  }

  async function check(period: Period) {
    if (!current() || scopeWriting || isKnownOffline() || client.getQueryData<SaveStatus>(key)?.kind === 'checking') return;
    setStatus({ kind: 'checking' });
    try {
      await selection.readFresh();
      if (!current()) return;
      await verifySummary(period);
      setStatus({ kind: 'observed' });
    } catch (failure) {
      setStatus({ kind: 'check-failed', error: ApiError.from(failure) });
    }
  }

  async function save(review: ScopeReview, reviewIsCurrent: () => boolean, wasDiscarded: () => boolean) {
    if (!workspace || !credential || !current() || scopeWriting ||
      ['saving', 'checking'].includes(client.getQueryData<SaveStatus>(key)?.kind ?? '')) return;
    if (!reviewIsCurrent()) {
      setStatus({ kind: 'stale', error: scopeReviewStale() });
      return false;
    }
    const basePair = selectionScopePair(review.response);
    setStatus({ kind: 'saving', dispatched: false });
    let write: Awaited<ReturnType<typeof beginScopeWrite>> | undefined;
    let dispatched = false;
    let acknowledged: ScopeSelection;
    try {
      write = await beginScopeWrite(basePair, review.epoch);
      acknowledged = await confirmScope(workspace.siteId, review.proposal, review.response, review.base, credential, () => {
        if (!reviewIsCurrent() || !isScopeCurrent(review.epoch, basePair)) throw scopeReviewStale();
        dispatched = true;
        setStatus({ kind: 'saving', dispatched });
      });
    } catch (failure) {
      if (!current()) return;
      const error = ApiError.from(failure);
      const refused = dispatched && isScopeRefusal(error);
      const definite = !dispatched || refused;
      if (write) await finishScopeWrite(write, definite);
      if (!dispatched && wasDiscarded()) {
        if (current()) void client.resetQueries({ queryKey: key, exact: true });
        return;
      }
      const kind = error.code === 'SCOPE_STALE' ? 'stale' : !dispatched ? 'unsent' : refused ? 'refused' : 'uncertain';
      setStatus({ kind, error, knownAttemptId: definite && write?.sole ? write.id : undefined });
      if (kind === 'stale') {
        // This observation is read-only. Another save always starts with a new explicit preview.
        void selection.readFresh().catch(() => undefined);
        void summary.readFresh(review.period).catch(() => undefined);
      }
      return false;
    }
    if (!current()) return;
    const pair = selectionScopePair(acknowledged);
    const changed = compareScopePairs(pair, basePair) > 0;
    let durable = true;
    let refreshError: ApiError | null = null;
    try {
      const observed = selection.publish(acknowledged);
      if (observed) durable = await observed.durable;
      if (!current()) return;
      const affected = new Set(review.proposal.authority_actions?.flatMap((action) => action.action === 'choose' ? [action.asset_id] : []));
      if (pair.binding > basePair.binding && affected.size > 0) {
        const predicate = ({ queryKey }: { queryKey: readonly unknown[] }) =>
          queryKey[1] === workspace.siteId && queryKey[2] === credentialGeneration &&
          ['asset', 'asset-summary', 'asset-history'].includes(String(queryKey[0])) && affected.has(String(queryKey[3]));
        await client.cancelQueries({ predicate: ({ queryKey }) => queryKey[0] === 'asset' && predicate({ queryKey }) });
        if (current()) void client.invalidateQueries({ predicate: ({ queryKey }) => queryKey[0] === 'asset' && predicate({ queryKey }) });
      }
      await verifySummary(review.period);
    } catch (failure) {
      refreshError = ApiError.from(failure);
    } finally {
      durable = await finishScopeWrite(write, !changed) && durable;
      if (!durable) setStatus({ kind: 'local-failed', refreshError, knownAttemptId: !changed && write.sole ? write.id : undefined });
      else if (refreshError) setStatus({ kind: 'refresh-failed', error: refreshError });
      else setStatus({ kind: 'acknowledged' });
    }
    return true;
  }

  return { status, pending, check, save };
}

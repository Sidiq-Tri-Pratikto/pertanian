import { skipToken, useQuery, useQueryClient, type Query } from '@tanstack/react-query';

import {
  getAsset, isAssetPatchRefusal, matchesAssetChanges, normalizeAssetText, patchAsset,
  type Asset, type AssetChanges, type AssetDetail, type Summary,
} from '@/api/client';
import { ApiError } from '@/api/errors';
import { assetKeys, cancelArchiveRead, readAssetWithBudget, type ArchiveRead, type PreviousAssetScope } from '@/features/assets/useAssets';
import { assetValues, EDITABLE_FIELDS, type AssetValues } from '@/features/offline/persist-drafts';
import { isKnownOffline } from '@/features/offline/useConnectivity';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';

export type AssetWriteState =
  | { kind: 'offline' | 'saving'; changes: AssetChanges }
  | { kind: 'refused' | 'checking'; changes: AssetChanges; error: ApiError }
  | { kind: 'unresolved'; changes: AssetChanges; error: ApiError; readError: ApiError; before?: AssetDetail }
  | { kind: 'diverged' | 'reviewed'; changes: AssetChanges; error: ApiError; observed: AssetDetail }
  | { kind: 'draft-checking'; changes: AssetChanges }
  | { kind: 'draft-review' | 'draft-ready'; changes: AssetChanges; observed: AssetDetail }
  | { kind: 'draft-blocked'; changes: AssetChanges; error: ApiError }
  | { kind: 'acknowledged' | 'observed'; changes: AssetChanges; asset: Asset };

function blocked(state: AssetWriteState | undefined): boolean {
  return state?.kind === 'saving' || state?.kind === 'checking' || state?.kind === 'unresolved' || state?.kind === 'diverged' || state?.kind === 'draft-checking' || state?.kind === 'draft-review';
}

function upsert(items: Asset[], asset: Asset): Asset[] {
  return items.some((item) => item.id === asset.id)
    ? items.map((item) => item.id === asset.id ? asset : item)
    : [...items, asset];
}

function metadata(asset: Asset): Asset {
  const { id, name, category, location, archived, scope_kind, parent_asset_id, expected_use } = asset;
  return { id, name, category, location, archived, scope_kind, parent_asset_id, expected_use };
}

/** One explicit write per intent, followed by an observation when the write outcome is unknown. */
export function useAssetMutations(assetId: string) {
  const { workspace, credential, credentialGeneration, isCurrentCredential, advanceScope } = useWorkspace();
  const client = useQueryClient();
  const keys = assetKeys(workspace?.siteId, credentialGeneration);
  const key = keys.write(assetId);
  const detailKey = keys.detail(assetId);
  const { data: state } = useQuery<AssetWriteState>({ queryKey: key, queryFn: skipToken, enabled: false, gcTime: Infinity });
  const current = () => isCurrentCredential(credentialGeneration) && Boolean(credential?.current());
  const latest = () => client.getQueryData<AssetWriteState>(key);
  const setState = (next: AssetWriteState) => {
    if (current()) client.setQueryData(key, next);
  };
  const scopedSummary = (query: Query) => {
    const [type, siteId, generation, id] = query.queryKey;
    return siteId === workspace?.siteId && generation === credentialGeneration &&
      (type === 'summary' || (type === 'asset-summary' && id === assetId));
  };

  async function publish(asset: Asset, before: AssetDetail | undefined, detail?: AssetDetail) {
    const confirmed = metadata(asset);
    const relevant = (query: Query) => scopedSummary(query) ||
      (query.queryKey[1] === workspace?.siteId && query.queryKey[2] === credentialGeneration &&
        (query.queryKey[0] === 'assets' || query.queryKey[0] === 'archived-assets'));
    let scopeChange: Promise<void> | undefined;
    if (before && before.archived !== confirmed.archived) {
      const previousScope = client.getQueryData<PreviousAssetScope>(keys.previousScope);
      const summaries = previousScope?.summaries ?? new WeakSet<Summary>();
      const restored = new Set(previousScope?.restored);
      if (confirmed.archived) restored.delete(assetId);
      else restored.add(assetId);
      for (const [, summary] of client.getQueriesData<Summary>({ queryKey: keys.summary })) {
        if (summary) summaries.add(summary);
      }
      client.setQueryData(keys.previousScope, { summaries, restored });
      scopeChange = advanceScope();
    }

    cancelArchiveRead(client, keys.archived);
    await client.cancelQueries({
      predicate: (query) => relevant(query) || (query.queryKey[0] === 'asset' &&
        query.queryKey[1] === detailKey[1] && query.queryKey[2] === detailKey[2] && query.queryKey[3] === assetId),
    });
    await scopeChange;
    if (!current()) return;
    client.setQueryData<AssetDetail>(detailKey, (previous) => detail ?? (previous ? { ...previous, ...confirmed } : previous));
    client.setQueryData<Asset[]>(keys.active, (previous) =>
      confirmed.archived ? previous?.filter((item) => item.id !== assetId) : upsert(previous ?? [], confirmed));
    client.setQueryData<ArchiveRead>(keys.archived, (previous) => ({
      items: upsert(previous?.items ?? [], confirmed),
      next_cursor: previous?.next_cursor ?? null,
      incomplete: previous?.incomplete ?? !previous,
    }));
    void client.invalidateQueries({ predicate: relevant });
  }

  async function observe(changes: AssetChanges, error: ApiError, before?: AssetDetail) {
    if (!credential || !current()) return;
    if (isKnownOffline()) {
      setState({ kind: 'unresolved', changes, error, readError: ApiError.offline(), before });
      return;
    }
    setState({ kind: 'checking', changes, error });
    try {
      const observed = await readAssetWithBudget(() => getAsset(assetId, credential), () => current() && !isKnownOffline());
      if (!current()) return;
      await publish(observed, before, observed);
      if (matchesAssetChanges(observed, changes)) {
        setState({ kind: 'observed', changes, asset: observed });
      } else {
        setState({ kind: 'diverged', changes, error, observed });
      }
    } catch (failure) {
      const readError = isKnownOffline() ? ApiError.offline() : ApiError.from(failure);
      setState({ kind: 'unresolved', changes, error, readError, before });
    }
  }

  async function checkOutcome() {
    const pending = latest();
    if (pending?.kind === 'unresolved') await observe(pending.changes, pending.error, pending.before);
  }

  async function submit(input: AssetChanges) {
    if (!credential || !current() || blocked(latest()) || Object.keys(input).length === 0) return;
    const changes = { ...input };
    if (isKnownOffline()) {
      setState({ kind: 'offline', changes });
      return;
    }
    const before = client.getQueryData<AssetDetail>(detailKey);
    setState({ kind: 'saving', changes });
    let acknowledgment: Asset;
    try {
      acknowledgment = await patchAsset(assetId, changes, credential);
    } catch (failure) {
      if (!current()) return;
      const error = ApiError.from(failure);
      if (error.code === 'OFFLINE_UNSENT') {
        setState({ kind: 'offline', changes });
        return;
      }
      if (isAssetPatchRefusal(error)) {
        setState({ kind: 'refused', changes, error });
        return;
      }

      await observe(changes, error, before);
      return;
    }
    if (!current()) return;
    await publish(acknowledgment, before);
    setState({ kind: 'acknowledged', changes, asset: acknowledgment });
  }

  async function reconcileDraft(changes: AssetChanges, baseline: AssetValues) {
    if (!credential || !current() || blocked(latest())) return;
    if (isKnownOffline()) {
      setState({ kind: 'offline', changes });
      return;
    }
    setState({ kind: 'draft-checking', changes });
    try {
      const observed = await readAssetWithBudget(() => getAsset(assetId, credential), () => current() && !isKnownOffline());
      if (!current()) return;
      const before = client.getQueryData<AssetDetail>(detailKey);
      await publish(observed, before, observed);
      if (!current()) return;
      if (matchesAssetChanges(observed, changes)) {
        setState({ kind: 'observed', changes, asset: observed });
        return;
      }
      const values = assetValues(observed);
      const changed = EDITABLE_FIELDS.some((field) => changes[field] !== undefined &&
        normalizeAssetText(values[field]) !== changes[field] &&
        normalizeAssetText(values[field]) !== normalizeAssetText(baseline[field]));
      setState({ kind: changed ? 'draft-review' : 'draft-ready', changes, observed });
    } catch (failure) {
      setState({ kind: 'draft-blocked', changes, error: ApiError.from(failure) });
    }
  }

  function review() {
    const pending = latest();
    if (pending?.kind === 'diverged') setState({ ...pending, kind: 'reviewed' });
    if (pending?.kind === 'draft-review') setState({ ...pending, kind: 'draft-ready' });
  }

  function dismiss() {
    if (current() && !blocked(latest())) void client.resetQueries({ queryKey: key, exact: true });
  }

  return { state, submit, reconcileDraft, checkOutcome, review, dismiss, blocked: blocked(state) };
}

import { useQueries } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';

import {
  compareScopePairs, historyInstant, previewScope, sameScopeIds, selectionScopePair,
  type ScopeBinding, type ScopePreview, type ScopeProposal, type ScopeSelection, type Summary,
} from '@/api/client';
import { ApiError } from '@/api/errors';
import { periodQuery, useNavigationContext } from '@/features/navigation-context/NavigationContextProvider';
import { isKnownOffline } from '@/features/offline/useConnectivity';
import { scopeReviewStale, type ScopeReview } from '@/features/scope/useSelection';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';
import type { Period } from '@/features/workspace/workspace-store';

type Authority = NonNullable<ScopeProposal['authority_actions']>[number];
type Pair = NonNullable<ScopeProposal['disjoint_confirmations']>[number];

export function candidateCutover(bindingId: string, candidates: ScopeBinding[], window: Summary['window']): Extract<Authority, { action: 'choose' }> | null {
  const candidate = candidates.find((row) => row.binding_id === bindingId);
  if (!candidate) return null;
  const effective = historyInstant(candidate.effective_from) > historyInstant(window.start) ? candidate.effective_from : window.start;
  const instant = historyInstant(effective);
  const covers = (row: ScopeBinding) => historyInstant(row.effective_from) <= instant &&
    (row.effective_to === null || instant < historyInstant(row.effective_to));
  if (instant >= historyInstant(window.effective_end) || !covers(candidate) ||
    candidates.filter((row) => row.asset_id === candidate.asset_id && row.source_id === candidate.source_id && covers(row)).length !== 1) return null;
  return { action: 'choose', asset_id: candidate.asset_id, source_id: candidate.source_id, effective_from: effective };
}

export function pruneScopeProposal(proposal: ScopeProposal, members: string[], archived: ReadonlySet<string>): ScopeProposal {
  const eligible = new Set(members.filter((id) => !archived.has(id)));
  return {
    ...proposal, selected_asset_ids: members,
    authority_actions: proposal.authority_actions?.filter((action) => eligible.has(action.asset_id)) ?? [],
    disjoint_confirmations: proposal.disjoint_confirmations?.filter((pair) =>
      eligible.has(pair.first_asset_id) && eligible.has(pair.second_asset_id)) ?? [],
  };
}

function descendants(parent: string, relations: ScopeSelection['relations']): Set<string> {
  const visited = new Set([parent]);
  const pending = [parent];
  const children = new Map<string, string[]>();
  for (const row of relations) {
    if (row.kind === 'contains') children.set(row.from_asset_id, [...children.get(row.from_asset_id) ?? [], row.to_asset_id]);
  }
  while (pending.length) {
    for (const child of children.get(pending.pop()!) ?? []) {
      if (!visited.has(child)) {
        pending.push(child);
        visited.add(child);
      }
    }
  }
  visited.delete(parent);
  return visited;
}

function candidateGroups(confirmed: Summary, reviewed: Summary | undefined, selection: ScopeSelection, proposal: ScopeProposal, archived: Set<string>) {
  const relevant = [...confirmed.scope.issues, ...(reviewed?.scope.issues ?? [])];
  const parentIssue = relevant.find((issue) => issue.type === 'parent_child');
  const parent = parentIssue?.asset_ids[0];
  const parentChildren = parent && !archived.has(parent) ? descendants(parent, selection.relations) : new Set<string>();
  const children = [...new Set([...selection.selected_asset_ids, ...proposal.selected_asset_ids])]
    .filter((id) => parentChildren.has(id) && !archived.has(id));
  const disjoint = new Map(proposal.disjoint_confirmations?.map((pair) => [pairKey(pair), pair]));
  for (const issue of relevant) {
    const [first_asset_id, second_asset_id] = [...issue.asset_ids].sort();
    if ((issue.type === 'unknown_overlap' || issue.type === 'unconfirmed') && issue.asset_ids.length === 2) {
      disjoint.set(JSON.stringify([first_asset_id, second_asset_id]), { first_asset_id, second_asset_id });
    }
  }
  return { parent, children, disjoint: [...disjoint.values()] };
}

function proposalPeriod(period: Period): ScopeProposal['period'] {
  return periodQuery(period) as ScopeProposal['period'];
}

function pairKey(pair: Pair): string {
  return JSON.stringify([pair.first_asset_id, pair.second_asset_id].sort());
}

type Draft = { proposal: ScopeProposal; chosen: Record<string, string> };
type ReadOption = { id: string; proposal: ScopeProposal };

/** Draft edits and optional display calculations cannot publish a review or a confirmed summary. */
export function useScopeDraft(selection: ScopeSelection | undefined, confirmed: Summary | undefined, period: Period | null) {
  const { workspace, credential, credentialGeneration, scopeEpoch, scopePair, isScopeCurrent } = useWorkspace();
  const { isCurrentPeriod, currentPeriodVersion, periodRevision } = useNavigationContext();
  const [edits, setEdits] = useState<Draft>();
  const [review, setReview] = useState<{ value: ScopeReview; version: number; periodVersion: number }>();
  const [previewing, setPreviewing] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const version = useRef(0);
  const mounted = useRef(true);
  const discarded = useRef(false);
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);

  const archived = new Set(confirmed?.scope.excluded.filter((row) => row.reason === 'archived').map((row) => row.asset_id));
  const pair = selection && selectionScopePair(selection);
  const draft = edits ?? (selection && period ? {
    chosen: {},
    proposal: {
      period: proposalPeriod(period), selected_asset_ids: selection.selected_asset_ids, authority_actions: [], disjoint_confirmations: [],
    },
  } : undefined);
  const proposal = draft && period ? pruneScopeProposal(
    { ...draft.proposal, period: proposalPeriod(period) }, draft.proposal.selected_asset_ids, archived,
  ) : undefined;
  const sameInput = (value: ScopeReview, generation: number, expectedPeriodVersion: number) =>
    mounted.current && Boolean(credential?.current()) && generation === version.current && currentPeriodVersion() === expectedPeriodVersion &&
    isScopeCurrent(value.epoch, selectionScopePair(value.response)) && isCurrentPeriod(value.period);
  const reviewed = review && scopePair && review.periodVersion === periodRevision && review.value.epoch === scopeEpoch &&
    compareScopePairs(scopePair, selectionScopePair(review.value.response)) === 0 ? review.value : undefined;
  const groups = confirmed && selection && proposal ? candidateGroups(confirmed, reviewed?.response.summary, selection, proposal, archived) : undefined;

  const variants: ReadOption[] = [];
  if (proposal && groups) {
    if (groups.parent && groups.children.length > 0) {
      variants.push(
        { id: 'parent', proposal: pruneScopeProposal(proposal, [groups.parent], archived) },
        { id: 'children', proposal: pruneScopeProposal(proposal, groups.children, archived) },
      );
    }
    // Keep this initial screen bounded even for a site with many pair conflicts.
    const individualIds = new Set(groups.disjoint.flatMap((pair) => [pair.first_asset_id, pair.second_asset_id]).slice(0, 8));
    for (const id of individualIds) {
      if (!archived.has(id)) variants.push({ id, proposal: pruneScopeProposal(proposal, [id], archived) });
    }
    variants.push({ id: 'candidates', proposal: { ...proposal, authority_actions: [], disjoint_confirmations: [] } });
  }
  const grouped = new Map<string, { proposal: ScopeProposal; ids: string[] }>();
  for (const variant of variants) {
    const key = JSON.stringify(variant.proposal);
    const existing = grouped.get(key);
    if (existing) existing.ids.push(variant.id);
    else grouped.set(key, { proposal: variant.proposal, ids: [variant.id] });
  }
  const requests = [...grouped.values()];
  const optionReads = useQueries({
    queries: requests.map(({ proposal: body }) => ({
      queryKey: ['scope-option', workspace?.siteId, credentialGeneration, scopeEpoch, pair, body] as const,
      enabled: Boolean(confirmed && credential && workspace && pair && body.selected_asset_ids.length > 0 &&
        body.selected_asset_ids.length <= 100 && !isKnownOffline()),
      queryFn: async () => {
        const result = await previewScope(workspace!.siteId, body, credential!);
        if (!credential?.current() || !isScopeCurrent(scopeEpoch, selectionScopePair(result))) throw scopeReviewStale();
        return result;
      },
      retry: false,
      refetchOnWindowFocus: false,
      refetchOnReconnect: false,
    })),
  });
  const options = new Map<string, ScopePreview>();
  requests.forEach(({ ids }, index) => {
    const result = optionReads[index].data;
    if (result) for (const id of ids) options.set(id, result);
  });

  function invalidateReview() {
    version.current += 1;
    setReview(undefined);
    setError(null);
    setPreviewing(false);
  }

  function update(next: ScopeProposal, chosen: Record<string, string> = draft?.chosen ?? {}) {
    invalidateReview();
    const retained = new Set(next.authority_actions?.map((row) => row.asset_id));
    setEdits({ proposal: next, chosen: Object.fromEntries(Object.entries(chosen).filter(([id]) => retained.has(id))) });
  }

  function selectMembers(ids: string[]) {
    if (proposal) update(pruneScopeProposal(proposal, ids, archived));
  }

  function chooseAuthority(assetId: string, bindingId: string) {
    const candidates = options.get('candidates');
    if (!proposal || !candidates) return;
    const action: Authority | null = bindingId === 'skip' ? { action: 'skip', asset_id: assetId }
      : candidateCutover(bindingId, candidates.candidates, candidates.summary.window);
    if (!action || action.asset_id !== assetId) return;
    update({
      ...proposal,
      authority_actions: [...(proposal.authority_actions ?? []).filter((item) => item.asset_id !== assetId), action],
    }, { ...draft?.chosen, [assetId]: bindingId });
  }

  function changeDisjoint(pair: Pair, checked: boolean) {
    if (!proposal) return;
    const kept = proposal.disjoint_confirmations?.filter((row) => pairKey(row) !== pairKey(pair)) ?? [];
    update({ ...proposal, disjoint_confirmations: checked ? [...kept, pair] : kept });
  }

  async function preview() {
    if (!workspace || !credential || !selection || !pair || !period || !proposal || previewing || isKnownOffline()) return;
    invalidateReview();
    const generation = version.current;
    const selectedPeriodVersion = currentPeriodVersion();
    const current = () => mounted.current && credential.current() && version.current === generation &&
      currentPeriodVersion() === selectedPeriodVersion && isCurrentPeriod(period);
    setPreviewing(true);
    try {
      const response = await previewScope(workspace.siteId, proposal, credential);
      if (!current()) return;
      if (!isScopeCurrent(scopeEpoch, selectionScopePair(response)) ||
        pair.selection !== response.selection_revision || pair.binding !== response.binding_revision ||
        proposal.authority_actions?.some((row) => {
          if (row.action !== 'choose') return false;
          const choice = candidateCutover(draft?.chosen[row.asset_id] ?? '', response.candidates, response.summary.window);
          return !choice || choice.source_id !== row.source_id || historyInstant(choice.effective_from) !== historyInstant(row.effective_from);
        })) throw scopeReviewStale();
      setReview({ value: { proposal, response, base: selection, period, epoch: scopeEpoch }, version: generation, periodVersion: selectedPeriodVersion });
    } catch (failure) {
      if (current()) setError(ApiError.from(failure));
    } finally {
      if (mounted.current && version.current === generation) setPreviewing(false);
    }
  }

  return {
    proposal, options, groups, reviewed, previewing, error, selectMembers, chooseAuthority, changeDisjoint,
    chosen: draft?.chosen ?? {},
    variant: groups?.parent && proposal && sameScopeIds(proposal.selected_asset_ids, [groups.parent]) ? 'parent' :
      groups?.children.length && proposal && sameScopeIds(proposal.selected_asset_ids, groups.children) ? 'children' : null,
    wasDiscarded: () => discarded.current,
    discard: () => {
      discarded.current = true;
      invalidateReview();
      setEdits(undefined);
    },
    reviewIsCurrent: () => Boolean(review && sameInput(review.value, review.version, review.periodVersion)),
    finishReview: (value: ScopeReview, acknowledged: boolean) => {
      if (mounted.current && review?.value === value && version.current === review.version) {
        invalidateReview();
        if (acknowledged) setEdits(undefined);
      }
    },
    preview,
  };
}

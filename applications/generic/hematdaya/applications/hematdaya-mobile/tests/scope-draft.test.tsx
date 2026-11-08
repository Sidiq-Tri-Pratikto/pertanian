import { act, renderHook, waitFor } from '@testing-library/react-native';
import type { ReactNode } from 'react';

import type { ScopeBinding, ScopeProposal, Summary } from '@/api/client';
import { useSummary } from '@/features/energy/useSummary';
import { NavigationContextProvider, useNavigationContext } from '@/features/navigation-context/NavigationContextProvider';
import { useSelection } from '@/features/scope/useSelection';
import { WorkspaceProvider } from '@/features/workspace/WorkspaceProvider';
import { candidateCutover, pruneScopeProposal, useScopeDraft } from '@/features/scope/useScopeDraft';

import { answer, meter, previewResult, scopeService, scopeWorkspace } from './fixtures/scope';
import { seedConfirmedWorkspace } from './fixtures/workspaces';

const window = {
  start: '2026-10-24T17:00:00Z', end: '2026-10-25T17:00:00Z', effective_end: '2026-10-25T11:00:00Z',
  start_date: '2026-10-25', end_date: '2026-10-25', timezone: 'Asia/Jakarta', is_current: true,
} satisfies Summary['window'];
const historical = {
  binding_id: 'old-binding', source_id: 'source', asset_id: 'fridge', label: 'Sumber lama', authoritative: false,
  effective_from: '2026-10-01T00:00:00Z', effective_to: '2026-10-25T10:00:00Z',
} satisfies ScopeBinding;

it('picks by binding ID and keeps the cutover inside an unambiguous half-open period', () => {
  const next = { ...historical, binding_id: 'next', effective_from: historical.effective_to, effective_to: null };
  expect(candidateCutover(historical.binding_id, [historical, next], window)).toEqual({
    action: 'choose', asset_id: 'fridge', source_id: 'source', effective_from: window.start,
  });
  expect(candidateCutover(next.binding_id, [historical, next], window)?.effective_from).toBe(historical.effective_to);
  expect(candidateCutover(next.binding_id, [historical, next], { ...window, effective_end: next.effective_from })).toBeNull();
  expect(candidateCutover(historical.binding_id, [historical, { ...historical, binding_id: 'overlap' }], window)).toBeNull();
  expect(candidateCutover('missing', [historical], window)).toBeNull();
});

it('retains raw archived membership while removing choose, skip and disjoint actions for ineligible members', () => {
  const proposal: ScopeProposal = {
    period: { preset: 'last_7_days' }, selected_asset_ids: ['fridge', 'meter', 'archived'],
    authority_actions: [
      { action: 'choose', asset_id: 'fridge', source_id: 'source', effective_from: window.start },
      { action: 'skip', asset_id: 'excluded' }, { action: 'skip', asset_id: 'archived' },
    ],
    disjoint_confirmations: [
      { first_asset_id: 'fridge', second_asset_id: 'meter' },
      { first_asset_id: 'fridge', second_asset_id: 'excluded' },
      { first_asset_id: 'fridge', second_asset_id: 'archived' },
    ],
  };
  const pruned = pruneScopeProposal(proposal, ['fridge', 'meter', 'archived'], new Set(['archived']));
  expect(pruned.selected_asset_ids).toEqual(proposal.selected_asset_ids);
  expect(pruned.authority_actions).toEqual([proposal.authority_actions![0]]);
  expect(pruned.disjoint_confirmations).toEqual([proposal.disjoint_confirmations![0]]);
});


function Wrapper({ children }: { children: ReactNode }) {
  return <WorkspaceProvider><NavigationContextProvider>{children}</NavigationContextProvider></WorkspaceProvider>;
}

it('keeps alternate reads out of review and rejects a late manual result after period or draft changes', async () => {
  await seedConfirmedWorkspace(scopeWorkspace);
  let hold = false;
  let withoutEnergy = false;
  let complete: (() => void) | undefined;
  const fetchMock = scopeService({
    preview: (proposal, selection) => {
      const result = previewResult(proposal, selection);
      if (hold) {
        hold = false;
        return new Promise((resolve) => { complete = () => resolve(answer(result)); });
      }
      return answer(withoutEnergy ? { ...result, summary: {
        ...result.summary, energy_kwh: null, energy_unavailable_reason: 'no_data',
      } } : result);
    },
  });
  try {
    const hook = await renderHook(() => {
      const { period, setPeriod } = useNavigationContext();
      const summary = useSummary();
      const selection = useSelection();
      const draft = useScopeDraft(selection.data, summary.data, period);
      return { draft, setPeriod };
    }, { wrapper: Wrapper });
    await waitFor(() => expect(hook.result.current.draft.options.get('candidates')).toBeDefined());
    expect(hook.result.current.draft.reviewed).toBeUndefined();
    hold = true;
    await act(() => { void hook.result.current.draft.preview(); });
    await waitFor(() => expect(complete).toBeDefined());
    await act(() => hook.result.current.setPeriod({ preset: 'today', start_date: '', end_date: '' }));
    await act(() => complete!());
    expect(hook.result.current.draft.reviewed).toBeUndefined();

    await act(() => hook.result.current.setPeriod(scopeWorkspace.initialPeriod));
    await act(() => { void hook.result.current.draft.preview(); });
    await waitFor(() => expect(hook.result.current.draft.reviewed).toBeDefined());
    await act(() => hook.result.current.draft.selectMembers([meter]));
    expect(hook.result.current.draft.reviewed).toBeUndefined();
    withoutEnergy = true;
    await act(() => { void hook.result.current.draft.preview(); });
    await waitFor(() => expect(hook.result.current.draft.reviewed?.response.summary).toMatchObject({
      scope: { valid: true }, energy_kwh: null, energy_unavailable_reason: 'no_data',
    }));
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === 'PUT')).toBe(false);
  } finally {
    fetchMock.mockRestore();
  }
});

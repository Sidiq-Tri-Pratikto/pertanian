import type { ScopeBinding, ScopePreview, ScopeProposal, ScopeSelection, Summary } from '@/api/client';
import type { Workspace } from '@/features/workspace/workspace-store';

import assets from './assets.json';

const fixture = assets['h-scope'];
export const scopeWorkspace: Workspace = {
  token: 'scope-test-bearer', siteId: 'scope-test-site', scenarioId: 'h-scope', expiresAt: '2099-01-01T00:00:00Z',
  initialPeriod: fixture.initial_period,
};
export const scopeSummary = { ...fixture.summary, selection_revision: null, binding_revision: 1 } as Summary;
export const meter = scopeSummary.scope.included.find((row) => row.name === 'Meter utama')!.asset_id;
export const fridge = scopeSummary.scope.included.find((row) => row.name === 'Kulkas')!.asset_id;
export const pump = scopeSummary.scope.included.find((row) => row.name === 'Pompa Air')!.asset_id;
const bindings = scopeSummary.assets.find((row) => row.asset_id === fridge)!.conflict_sources!.map((row, index): ScopeBinding => ({
  asset_id: fridge, source_id: row.source_id, label: row.label, binding_id: `candidate-${index}`, authoritative: false,
  effective_from: scopeSummary.window.start, effective_to: null,
}));

export const baseSelection: ScopeSelection = {
  selection_revision: 0, binding_revision: 1,
  selected_asset_ids: scopeSummary.scope.included.map((row) => row.asset_id),
  authority: [], candidates: bindings, issues: scopeSummary.scope.issues,
  relations: scopeSummary.scope.issues.flatMap((issue) => issue.type === 'parent_child' ? [{
    from_asset_id: issue.asset_ids[0], to_asset_id: issue.asset_ids[1], kind: 'contains',
  }] : []),
};

export function answer(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

export function rejection(code: 'SCOPE_STALE' | 'SCOPE_CONFLICT') {
  return answer({ error: { code, message: 'Cakupan perlu ditinjau. Periksa pratinjau.',
    request_id: 'ref-scope-test', recovery: { retryable: false }, debug_info: 'fake-secret' } }, 409);
}

type ScopeFixture = {
  put?: (body: ScopeProposal) => Response | Promise<Response>;
  summary?: () => Response | Promise<Response>;
  preview?: (body: ScopeProposal, selection: ScopeSelection) => Response | Promise<Response>;
  selection?: () => ScopeSelection;
};

export function previewResult(proposal: ScopeProposal, selection = baseSelection): ScopePreview {
  const ids = new Set(proposal.selected_asset_ids);
  const included = scopeSummary.scope.included.filter((row) => ids.has(row.asset_id));
  const excluded = scopeSummary.scope.included.filter((row) => !ids.has(row.asset_id)).map((row) => ({ ...row, reason: 'not_selected' }));
  const issues = scopeSummary.scope.issues.filter((issue) => issue.asset_ids.every((id) => ids.has(id)) &&
    !(issue.type === 'source_conflict' && proposal.authority_actions?.some((row) => row.action === 'choose')) &&
    !(issue.type === 'unknown_overlap' && proposal.disjoint_confirmations?.length));
  const energy = issues.length > 0 ? null : ids.has(meter) ? ids.has(pump) ? '10.300' : '10.000' :
    ids.has(fridge) ? '1.600' : '0.300';
  return {
    selection_revision: selection.selection_revision, binding_revision: selection.binding_revision,
    candidates: ids.has(fridge) ? bindings : [],
    summary: {
      ...scopeSummary, selection_revision: selection.selection_revision || null, binding_revision: selection.binding_revision,
      scope: { included, excluded, issues, valid: issues.length === 0 },
      assets: scopeSummary.assets.filter((row) => ids.has(row.asset_id)),
      energy_kwh: energy, energy_unavailable_reason: energy === null ? 'scope_conflict' : null,
    },
  };
}

export function scopeService(options: ScopeFixture = {}) {
  return jest.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    const path = new URL(String(input)).pathname;
    const selection = options.selection?.() ?? baseSelection;
    const site = `/api/v1/sites/${scopeWorkspace.siteId}`;
    if (path === site) return answer({ id: scopeWorkspace.siteId, kind: 'demo', timezone: 'Asia/Jakarta', name: 'Scope' });
    if (path === `${site}/aggregation-selection/preview`) {
      const proposal = JSON.parse(String(init?.body)) as ScopeProposal;
      return options.preview?.(proposal, selection) ?? answer(previewResult(proposal, selection));
    }
    if (path === `${site}/aggregation-selection`) {
      if (init?.method === 'PUT') return options.put?.(JSON.parse(String(init.body))) ?? answer({});
      return answer(selection);
    }
    if (path === `${site}/summary`) return options.summary?.() ?? answer(scopeSummary);
    if (path === `${site}/assets`) return answer(fixture.assets);
    if (path === `${site}/insights`) {
      return answer({ window: scopeSummary.window, observations: [], notices: [], learning_count: 0, comparable_count: 0 });
    }
    if (path === `/api/v1/assets/${fridge}/summary`) return answer(fixture.details.Kulkas.summary);
    if (path === `/api/v1/assets/${fridge}`) return answer(fixture.details.Kulkas.asset);
    return answer({ schema_version: 1, source_release: 'fixture', capabilities: [], adapters: [], policies: [],
      composition: { id: 'core', version: 1 } });
  });
}

import { ApiError, readFailure } from '@/api/errors';
import { endsSession } from '@/api/query-client';
import type { components, paths } from '@/api/schema.generated';
import { isKnownOffline } from '@/features/offline/useConnectivity';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';
const TIMEOUT_MS = 10_000;
/** A preview of a file at the limits took 8.94 s over local HTTP before any upload; this leaves room for a slow link. */
export const IMPORT_PREVIEW_TIMEOUT_MS = 120_000;
/** A commit at the limits took 9.12 s, and a counter commit 20.62 s; PRD §18 allows 60 s. A timeout is an unknown result. */
export const IMPORT_COMMIT_TIMEOUT_MS = 60_000;
const CAPABILITIES_PATH = '/api/v1/capabilities';

export type CapabilityManifest =
  paths[typeof CAPABILITIES_PATH]['get']['responses'][200]['content']['application/json'];
export type DemoSession = components['schemas']['DemoSessionResponse'];
export type Summary = components['schemas']['SummaryResponse'];

/** A credential lease belongs to one provider generation, even when a reset reuses the same token. */
export type RequestCredential = {
  token: string;
  signal: AbortSignal;
  current: () => boolean;
  reject: () => void;
};

type Credential = string | RequestCredential;

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  expectedStatus?: number;
  body?: unknown;
  token?: Credential | null;
  beforeDispatch?: () => void;
  headers?: Record<string, string>;
  query?: Record<string, string | undefined>;
  /** Sent as the body. The platform sets the multipart `Content-Type` with its boundary, so the client sets none. */
  form?: FormData;
  timeoutMs?: number;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/**
 * One request path for the whole app: bearer token, timeout, and the service's failure envelope. A body that
 * is not what the caller expects becomes `UNEXPECTED_RESPONSE`, never raw text on screen.
 */
export async function apiRequest<T>(
  path: string,
  { method = 'GET', body, token, headers, query, form, timeoutMs = TIMEOUT_MS, expectedStatus, beforeDispatch }: RequestOptions,
  isValid: (value: unknown) => value is T,
): Promise<T> {
  const search = new URLSearchParams(
    Object.entries(query ?? {}).filter((entry): entry is [string, string] => entry[1] !== undefined),
  ).toString();
  const lease = typeof token === 'object' ? token : null;
  const bearer = typeof token === 'string' ? token : lease?.token;
  const checkCurrent = () => {
    if (lease && (!lease.current() || lease.signal.aborted)) throw ApiError.revoked();
  };
  const controller = new AbortController();
  const abort = () => controller.abort();
  const timeout = setTimeout(abort, timeoutMs);
  lease?.signal.addEventListener('abort', abort);
  try {
    const init = {
      method,
      headers: {
        ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        ...(bearer ? { Authorization: `Bearer ${bearer}` } : {}),
        ...headers,
      },
      body: form ?? (body !== undefined ? JSON.stringify(body) : undefined),
      signal: controller.signal,
    };
    checkCurrent();
    if (method !== 'GET' && isKnownOffline()) throw ApiError.offline();
    beforeDispatch?.();

    let response: Response;
    try {
      response = await fetch(`${BASE_URL}${path}${search ? `?${search}` : ''}`, init);
    } catch {
      checkCurrent();
      throw ApiError.unreachable();
    }
    checkCurrent();
    if (!response.ok) {
      const error = await readFailure(response);
      checkCurrent();
      if (endsSession(error)) lease?.reject();
      throw error;
    }
    if (expectedStatus !== undefined && response.status !== expectedStatus) throw ApiError.unexpected();
    if (response.status === 204) return undefined as T;

    const payload: unknown = await response.json().catch(() => null);
    checkCurrent();
    if (!isValid(payload)) throw ApiError.unexpected();
    return payload;
  } finally {
    clearTimeout(timeout);
    lease?.signal.removeEventListener('abort', abort);
  }
}

function isVersionedEntry(value: unknown): boolean {
  return isRecord(value) && typeof value.id === 'string' && Number.isInteger(value.version);
}

function isStatusEntry(value: unknown): value is Record<string, unknown> {
  return (
    isRecord(value) &&
    typeof value.id === 'string' &&
    (value.status === 'planned' || value.status === 'simulated' || value.status === 'available')
  );
}

function isCapabilityManifest(value: unknown): value is CapabilityManifest {
  return (
    isRecord(value) &&
    Number.isInteger(value.schema_version) &&
    typeof value.source_release === 'string' &&
    value.source_release.trim().length > 0 &&
    isVersionedEntry(value.composition) &&
    Array.isArray(value.capabilities) &&
    value.capabilities.every((entry: unknown) => isStatusEntry(entry) && typeof entry.optional === 'boolean') &&
    Array.isArray(value.adapters) &&
    value.adapters.every(isStatusEntry) &&
    Array.isArray(value.policies) &&
    value.policies.every(isVersionedEntry)
  );
}

function isPeriod(value: unknown): boolean {
  return isRecord(value) && typeof value.preset === 'string' && isLocalDate(value.start_date) && isLocalDate(value.end_date);
}

function isDemoWorkspace(value: unknown): value is components['schemas']['DemoWorkspaceResponse'] {
  return isRecord(value) && typeof value.site_id === 'string' && value.site_id.length > 0 &&
    typeof value.scenario_id === 'string' && value.scenario_id.length > 0 &&
    typeof value.expires_at === 'string' && Number.isFinite(Date.parse(value.expires_at)) && isPeriod(value.initial_period);
}

function isDemoSession(value: unknown): value is DemoSession {
  return (
    isRecord(value) && typeof value.token === 'string' && value.token.length > 0 && isDemoWorkspace(value)
  );
}

/** An authenticated owned-site response is required to upgrade a pre-attestation session. */
export function confirmDemoSite(siteId: string, token: Credential): Promise<components['schemas']['SiteResponse']> {
  return apiRequest(`/api/v1/sites/${encodeURIComponent(siteId)}`, { token, expectedStatus: 200 },
    (value): value is components['schemas']['SiteResponse'] =>
      isRecord(value) && value.id === siteId && value.kind === 'demo' &&
      typeof value.timezone === 'string' && typeof value.name === 'string');
}

/** An explicit transition issues the only reset request allowed after revoking the old local epoch. */
export function resetDemoSession(token: RequestCredential): Promise<components['schemas']['DemoWorkspaceResponse']> {
  return apiRequest('/api/v1/demo/sessions/current/reset', { method: 'POST', token, expectedStatus: 200 }, isDemoWorkspace);
}

export type SourceFreshness = components['schemas']['SourceFreshnessResponse'];

const nullableString = (value: unknown) => value === null || typeof value === 'string';
const nullableEnergy = (value: unknown) => value === null || isEnergy(value);

function isSpan(value: unknown): value is { start: string; end: string } {
  return isRecord(value) && historyInstant(value.start) < historyInstant(value.end);
}

function isFreshness(value: unknown): value is SourceFreshness {
  if (!isRecord(value) || typeof value.source_id !== 'string' || typeof value.asset_id !== 'string' ||
    typeof value.label !== 'string' || !HISTORY_ORIGINS.has(value.origin) || value.policy_version !== 1 ||
    (value.cadence_seconds !== null && (!Number.isSafeInteger(value.cadence_seconds) || Number(value.cadence_seconds) <= 0)) ||
    (value.last_capture_at !== null && !Number.isFinite(historyInstant(value.last_capture_at)))) return false;
  switch (value.state) {
    case 'stale':
    case 'current':
      return value.last_capture_at !== null && value.cadence_seconds !== null && value.historical_range === null;
    case 'historical':
      return value.last_capture_at !== null && isSpan(value.historical_range);
    case 'unknown':
      return value.historical_range === null;
    default:
      return false;
  }
}

function isScopeAsset(value: unknown): value is Summary['scope']['included'][number] {
  return isRecord(value) && typeof value.asset_id === 'string' && typeof value.name === 'string';
}

function isScopeIssue(value: unknown): value is Summary['scope']['issues'][number] {
  return isRecord(value) &&
    typeof value.type === 'string' && ['parent_child', 'unknown_overlap', 'unconfirmed', 'source_conflict', 'shared_source'].includes(value.type) &&
    Array.isArray(value.asset_ids) && value.asset_ids.length > 0 && value.asset_ids.every(isScopeId) &&
    typeof value.message === 'string' && value.message.length > 0;
}

const isScopeId = (value: unknown): value is string => typeof value === 'string' && value.length > 0;
const isRevision = (value: unknown): value is number => typeof value === 'number' && Number.isSafeInteger(value) && value >= 0;
const isOptionalRevision = (value: unknown) => value === undefined || value === null || isRevision(value);

export function isSummary(value: unknown): value is Summary {
  if (!isRecord(value) || !isRecord(value.window) || !isRecord(value.scope) || !isRecord(value.coverage)) return false;
  const { window, scope, coverage } = value;
  const start = historyInstant(window.start);
  const end = historyInstant(window.end);
  const cutoff = historyInstant(window.effective_end);
  return start < end && start <= cutoff && cutoff <= end &&
    isLocalDate(window.start_date) && isLocalDate(window.end_date) && window.start_date <= window.end_date &&
    isTimezone(window.timezone) && typeof window.is_current === 'boolean' &&
    typeof scope.valid === 'boolean' && Array.isArray(scope.issues) && scope.issues.every(isScopeIssue) &&
    scope.valid === (scope.issues.length === 0) && (scope.valid || value.energy_kwh === null) &&
    isOptionalRevision(value.selection_revision) && isOptionalRevision(value.binding_revision) &&
    Array.isArray(scope.included) && scope.included.every(isScopeAsset) &&
    Array.isArray(scope.excluded) && scope.excluded.every((row) => isRecord(row) && isScopeAsset(row) && 'reason' in row && typeof row.reason === 'string') &&
    nullableEnergy(coverage.minimum) && nullableEnergy(coverage.concurrent) && typeof coverage.allocated_estimate === 'boolean' &&
    Array.isArray(value.assets) && value.assets.every((row) => isRecord(row) && typeof row.asset_id === 'string' &&
      typeof row.name === 'string' && typeof row.scope_kind === 'string' && nullableEnergy(row.energy_kwh) &&
      nullableString(row.energy_unavailable_reason) && nullableEnergy(row.share_percent) && nullableEnergy(row.coverage) &&
      Array.isArray(row.gaps) && row.gaps.every(isSpan) && (row.conflict_sources === null ||
      (Array.isArray(row.conflict_sources) && row.conflict_sources.every((source) => isRecord(source) &&
        typeof source.source_id === 'string' && typeof source.label === 'string' && isEnergy(source.energy_kwh))))) &&
    nullableEnergy(value.energy_kwh) && nullableString(value.energy_unavailable_reason) &&
    (value.latest_measurement_at === null || Number.isFinite(historyInstant(value.latest_measurement_at))) &&
    Array.isArray(value.origins) && value.origins.every((origin) => typeof origin === 'string') &&
    Number.isSafeInteger(value.revision) && (value.source_freshness === undefined ||
      (Array.isArray(value.source_freshness) && value.source_freshness.every((row) => isFreshness(row) &&
        (scope.included as Summary['scope']['included']).some((asset) => asset.asset_id === row.asset_id))));
}

export function getCapabilities(): Promise<CapabilityManifest> {
  return apiRequest(CAPABILITIES_PATH, {}, isCapabilityManifest);
}

/** Starts a demo, or recovers the same one: the key, proof and body must stay unchanged across retries. */
export function createDemoSession(scenarioId: string, operationId: string, replayProof: string, beforeDispatch?: () => void): Promise<DemoSession> {
  return apiRequest(
    '/api/v1/demo/sessions',
    {
      method: 'POST',
      body: { scenario_id: scenarioId },
      headers: { 'Idempotency-Key': operationId, 'X-Demo-Replay-Proof': replayProof }, beforeDispatch,
    },
    isDemoSession,
  );
}

export type PeriodQuery = { preset?: string; start_date?: string; end_date?: string };

export function getSummary(siteId: string, period: PeriodQuery, token: Credential): Promise<Summary> {
  return apiRequest(`/api/v1/sites/${encodeURIComponent(siteId)}/summary`, { token, query: period, expectedStatus: 200 }, isSummary);
}

export type ScopeSelection = components['schemas']['ScopeSelectionResponse'];
export type ScopePreview = components['schemas']['ScopePreviewResponse'];
export type ScopeProposal = components['schemas']['ScopeProposalRequest'];
export type ScopeBinding = components['schemas']['ScopeBindingResponse'];
export type ScopePair = { selection: number; binding: number };

export function selectionScopePair(value: Pick<ScopeSelection, 'selection_revision' | 'binding_revision'>): ScopePair {
  return { selection: value.selection_revision, binding: value.binding_revision };
}

export function summaryScopePair(value: Summary): ScopePair | null {
  return value.binding_revision != null && value.selection_revision !== undefined
    ? { selection: value.selection_revision ?? 0, binding: value.binding_revision } : null;
}

/** Reset can clear explicit selection but always advances the binding revision. */
export function compareScopePairs(a: ScopePair, b: ScopePair): number {
  return a.binding - b.binding || a.selection - b.selection;
}

export function sameScopeIds(a: readonly string[], b: readonly string[]): boolean {
  const sorted = [...b].sort();
  return a.length === b.length && [...a].sort().every((id, index) => id === sorted[index]);
}

export function summaryMatchesMembership(summary: Summary, rawIds: readonly string[]): boolean {
  const archived = new Set(summary.scope.excluded.filter((asset) => asset.reason === 'archived').map((asset) => asset.asset_id));
  return sameScopeIds(summary.scope.included.map((asset) => asset.asset_id), rawIds.filter((id) => !archived.has(id)));
}

function isScopeBinding(value: unknown): value is ScopeBinding {
  if (!isRecord(value)) return false;
  const start = historyInstant(value.effective_from);
  return isScopeId(value.binding_id) && isScopeId(value.source_id) && isScopeId(value.asset_id) &&
    typeof value.label === 'string' && typeof value.authoritative === 'boolean' &&
    Number.isFinite(start) && (value.effective_to === null || start < historyInstant(value.effective_to));
}

function isScopeBindings(value: unknown): value is ScopeBinding[] {
  return Array.isArray(value) && value.every(isScopeBinding) &&
    new Set(value.map((row) => row.binding_id)).size === value.length;
}

function isScopeSelection(value: unknown): value is ScopeSelection {
  return isRecord(value) && isRevision(value.selection_revision) && isRevision(value.binding_revision) &&
    Array.isArray(value.selected_asset_ids) && value.selected_asset_ids.every(isScopeId) &&
    new Set(value.selected_asset_ids).size === value.selected_asset_ids.length &&
    Array.isArray(value.issues) && value.issues.every(isScopeIssue) &&
    isScopeBindings(value.authority) && isScopeBindings(value.candidates) &&
    Array.isArray(value.relations) && value.relations.every((row) => isRecord(row) &&
      isScopeId(row.from_asset_id) && isScopeId(row.to_asset_id) && row.from_asset_id !== row.to_asset_id &&
      (row.kind === 'contains' || row.kind === 'disjoint' || row.kind === 'unknown_overlap'));
}

function selectionPath(siteId: string): string {
  return `/api/v1/sites/${encodeURIComponent(siteId)}/aggregation-selection`;
}

export function getSelection(siteId: string, token: Credential): Promise<ScopeSelection> {
  return apiRequest(selectionPath(siteId), { token, expectedStatus: 200 }, isScopeSelection);
}

/** This POST is a bounded, read-only calculation. Its result cannot publish confirmed figures. */
export function previewScope(siteId: string, proposal: ScopeProposal, token: Credential): Promise<ScopePreview> {
  return apiRequest(`${selectionPath(siteId)}/preview`, { method: 'POST', body: proposal, token, expectedStatus: 200 },
    (value): value is ScopePreview => {
      if (!isRecord(value) || !isRevision(value.selection_revision) || !isRevision(value.binding_revision) ||
        !isSummary(value.summary) || !isScopeBindings(value.candidates)) return false;
      const { summary } = value;
      const pair = summaryScopePair(summary);
      const { start, end, start_date, end_date } = summary.window;
      return pair?.selection === value.selection_revision && pair.binding === value.binding_revision &&
        (proposal.period.preset != null || (start_date === proposal.period.start_date && end_date === proposal.period.end_date)) &&
        summaryMatchesMembership(summary, proposal.selected_asset_ids) &&
        sameScopeIds(summary.assets.map((row) => row.asset_id), summary.scope.included.map((row) => row.asset_id)) &&
        value.candidates.every((row) => proposal.selected_asset_ids.includes(row.asset_id) &&
          historyInstant(row.effective_from) < historyInstant(end) &&
          (row.effective_to === null || historyInstant(start) < historyInstant(row.effective_to)));
    });
}

export function confirmScope(
  siteId: string, proposal: ScopeProposal, preview: ScopePreview, base: ScopeSelection, token: Credential,
  beforeDispatch?: () => void,
): Promise<ScopeSelection> {
  const { start_date, end_date, timezone } = preview.summary.window;
  const body: components['schemas']['ConfirmScopeRequest'] = {
    ...proposal,
    expected_selection_revision: preview.selection_revision,
    expected_binding_revision: preview.binding_revision,
    resolved_period: { start_date, end_date, timezone },
  };
  const selectionChanges = preview.selection_revision === 0 || !sameScopeIds(base.selected_asset_ids, proposal.selected_asset_ids);
  const canChangeBindings = proposal.authority_actions?.some((action) => action.action === 'choose') ||
    Boolean(proposal.disjoint_confirmations?.length);
  return apiRequest(selectionPath(siteId), { method: 'PUT', body, token, expectedStatus: 200, beforeDispatch },
    (value): value is ScopeSelection => isScopeSelection(value) &&
      sameScopeIds(value.selected_asset_ids, proposal.selected_asset_ids) &&
      value.selection_revision === preview.selection_revision + Number(selectionChanges) &&
      (value.binding_revision === preview.binding_revision ||
        (canChangeBindings && value.binding_revision === preview.binding_revision + 1)));
}

export function isScopeRefusal(failure: ApiError): boolean {
  return isAssetPatchRefusal(failure) || (!failure.recovery.retryable &&
    ((failure.status === 409 && (failure.code === 'SCOPE_CONFLICT' || failure.code === 'SCOPE_STALE')) ||
      (failure.status === 400 && failure.code === 'REQUEST_INVALID')));
}

export type InsightList = components['schemas']['InsightListResponse'];
export type Insight = components['schemas']['InsightResponse'];
export type InsightNotice = components['schemas']['NoticeResponse'];

function isInsight(value: unknown): value is Insight {
  return (
    isRecord(value) &&
    typeof value.id === 'string' &&
    Number.isInteger(value.revision) &&
    Number.isInteger(value.current_revision) &&
    typeof value.superseded === 'boolean' &&
    isRecord(value.evidence) &&
    isRecord(value.text) &&
    typeof value.text.title === 'string'
  );
}

function isInsightList(value: unknown): value is InsightList {
  return (
    isRecord(value) &&
    isRecord(value.window) &&
    Array.isArray(value.observations) &&
    value.observations.every(isInsight) &&
    Array.isArray(value.notices) &&
    Number.isInteger(value.learning_count) &&
    Number.isInteger(value.comparable_count)
  );
}

export function getInsights(siteId: string, period: PeriodQuery, token: Credential): Promise<InsightList> {
  return apiRequest(`/api/v1/sites/${encodeURIComponent(siteId)}/insights`, { token, query: period }, isInsightList);
}

/** Always one exact revision: the evidence screen must show what the card showed, even after a correction. */
export function getInsight(insightId: string, revision: number, token: Credential): Promise<Insight> {
  return apiRequest(
    `/api/v1/insights/${encodeURIComponent(insightId)}`,
    { token, query: { revision: String(revision) } },
    isInsight,
  );
}

export type FeedbackAction = components['schemas']['FeedbackAction'];
export type FeedbackResult = components['schemas']['FeedbackResponse'];
export type HiddenInsights = components['schemas']['HiddenInsightsResponse'];

function isFeedbackResult(value: unknown): value is FeedbackResult {
  return (
    isRecord(value) &&
    typeof value.insight_id === 'string' &&
    Number.isInteger(value.revision) &&
    typeof value.visibility === 'string' &&
    (value.until === null || typeof value.until === 'string')
  );
}

function isHiddenInsights(value: unknown): value is HiddenInsights {
  return isRecord(value) && isRecord(value.window) && Array.isArray(value.observations) && value.observations.every(isInsight);
}

/** One feedback intent. Retries resend the same key so a lost response never applies twice. */
export function sendFeedback(insightId: string, revision: number, action: FeedbackAction, key: string, token: Credential, beforeDispatch?: () => void): Promise<FeedbackResult> {
  return apiRequest(
    `/api/v1/insights/${encodeURIComponent(insightId)}/feedback`,
    { method: 'POST', token, body: { action, revision }, headers: { 'Idempotency-Key': key }, beforeDispatch },
    isFeedbackResult,
  );
}

export function getHiddenInsights(siteId: string, period: PeriodQuery, token: Credential): Promise<HiddenInsights> {
  return apiRequest(`/api/v1/sites/${encodeURIComponent(siteId)}/insights/hidden`, { token, query: period }, isHiddenInsights);
}

export type Asset = components['schemas']['AssetResponse'];
export type AssetPage = components['schemas']['AssetPageResponse'];
export type AssetDetail = components['schemas']['AssetDetailResponse'];
export type AssetSource = components['schemas']['SourceResponse'];
export type AssetBinding = components['schemas']['BindingResponse'];
export type AssetEnergy = components['schemas']['AssetEnergyResponse'];
export type HistoryResponse = components['schemas']['HistoryResponse'];
export type HistoryGranularity = components['schemas']['Granularity'];
export type HistorySelection = Pick<HistoryResponse['window'], 'start_date' | 'end_date' | 'timezone'> & {
  bucket: HistoryGranularity;
};
export type ScopeKind = components['schemas']['ScopeKind'];
export type SourceOrigin = components['schemas']['SourceOrigin'];
export type TransportStatus = components['schemas']['TransportStatus'];

const ASSET_PAGE_SIZE = '100';
const MAX_ASSET_PAGES = 20;

type UpdateAssetRequest = components['schemas']['UpdateAssetRequest'];
export type AssetChanges = {
  [Field in 'name' | 'category' | 'location' | 'archived']?: NonNullable<UpdateAssetRequest[Field]>;
};

/** Pydantic strips Unicode White_Space, including NEL and excluding a leading BOM. */
export function normalizeAssetText(value: string): string {
  return value.replace(/^\p{White_Space}+|\p{White_Space}+$/gu, '');
}

function nullableText(value: unknown): boolean {
  return value === null || typeof value === 'string';
}

function isAsset(value: unknown): value is Asset {
  return (
    isRecord(value) && typeof value.id === 'string' && value.id.length > 0 &&
    typeof value.name === 'string' && normalizeAssetText(value.name).length > 0 &&
    nullableText(value.category) && nullableText(value.location) && nullableText(value.parent_asset_id) &&
    typeof value.archived === 'boolean' &&
    (value.scope_kind === 'device' || value.scope_kind === 'group' || value.scope_kind === 'circuit' || value.scope_kind === 'site_total') &&
    (value.expected_use === 'unknown' || value.expected_use === 'continuous' ||
      value.expected_use === 'scheduled' || value.expected_use === 'intermittent')
  );
}

function isAssetPage(value: unknown): value is AssetPage {
  return isRecord(value) && Array.isArray(value.items) && value.items.every(isAsset) && nullableText(value.next_cursor);
}

function isBinding(value: unknown): boolean {
  return isRecord(value) && typeof value.id === 'string' && typeof value.source_id === 'string' &&
    typeof value.effective_from === 'string' && Number.isFinite(Date.parse(value.effective_from)) &&
    (value.effective_to === null || (typeof value.effective_to === 'string' && Number.isFinite(Date.parse(value.effective_to)))) &&
    typeof value.authoritative === 'boolean';
}

function isSource(value: unknown): boolean {
  return isRecord(value) && typeof value.id === 'string' && typeof value.label === 'string' &&
    (value.origin === 'live' || value.origin === 'import' || value.origin === 'dataset_replay' || value.origin === 'simulated') &&
    (value.measurement_kind === 'interval_energy' || value.measurement_kind === 'average_power' ||
      value.measurement_kind === 'instantaneous_power' || value.measurement_kind === 'counter') &&
    (value.transport_status === 'none' || value.transport_status === 'simulated_live' || value.transport_status === 'historical') &&
    (value.cadence_seconds === null || Number.isInteger(value.cadence_seconds)) &&
    (value.resolution_mwh === null || Number.isInteger(value.resolution_mwh));
}

function isAssetDetail(value: unknown): value is AssetDetail {
  return (
    isRecord(value) &&
    Array.isArray(value.bindings) && value.bindings.every(isBinding) &&
    Array.isArray(value.sources) && value.sources.every(isSource) && isAsset(value)
  );
}

type ReadAssetPage = (read: () => Promise<AssetPage>) => Promise<AssetPage>;

async function listAssets(
  siteId: string, token: Credential, includeArchived: boolean, readPage: ReadAssetPage, onPage?: (page: AssetPage) => void,
): Promise<AssetPage> {
  const assets: Asset[] = [];
  const collected = () => includeArchived ? [...new Map(assets.map((asset) => [asset.id, asset])).values()] : assets;
  let cursor: string | null = null;
  for (let page = 0; page < MAX_ASSET_PAGES; page += 1) {
    const { items, next_cursor: next }: AssetPage = await readPage(() => apiRequest(
      `/api/v1/sites/${encodeURIComponent(siteId)}/assets`,
      { token, query: { limit: ASSET_PAGE_SIZE, cursor: cursor ?? undefined, include_archived: includeArchived ? 'true' : undefined }, expectedStatus: 200 },
      isAssetPage,
    ));
    assets.push(...items);
    cursor = next;
    if (cursor === null) break;
    onPage?.({ items: collected(), next_cursor: cursor });
  }
  return { items: collected(), next_cursor: cursor };
}

/** Active assets in service order. */
export async function getAssets(siteId: string, token: Credential): Promise<Asset[]> {
  return (await listAssets(siteId, token, false, (read) => read())).items;
}

/** Includes archived assets on every cursor and reports if the client stops with pages still unread. */
export function getArchivedAssets(
  siteId: string, token: Credential, readPage: ReadAssetPage = (read) => read(), onPage?: (page: AssetPage) => void,
): Promise<AssetPage> {
  return listAssets(siteId, token, true, readPage, onPage);
}

export function getAsset(assetId: string, token: Credential): Promise<AssetDetail> {
  return apiRequest(
    `/api/v1/assets/${encodeURIComponent(assetId)}`,
    { token, expectedStatus: 200 },
    (value): value is AssetDetail => isAssetDetail(value) && value.id === assetId,
  );
}

export function matchesAssetChanges(asset: Asset, changes: AssetChanges): boolean {
  return (Object.keys(changes) as (keyof AssetChanges)[]).every((field) => asset[field] === changes[field]);
}

/** Only a matching HTTP 200 asset can acknowledge this intent. */
export function patchAsset(assetId: string, changes: AssetChanges, token: Credential): Promise<Asset> {
  return apiRequest(
    `/api/v1/assets/${encodeURIComponent(assetId)}`,
    { method: 'PATCH', body: changes, token, expectedStatus: 200 },
    (value): value is Asset => isAsset(value) && value.id === assetId && matchesAssetChanges(value, changes),
  );
}

/** Status and public code pairs that the asset route can return before it makes a write. */
export function isAssetPatchRefusal(failure: ApiError): boolean {
  if (failure.recovery.retryable) return false;
  return (failure.status === 401 && (failure.code === 'UNAUTHORIZED' || failure.code === 'SESSION_EXPIRED')) ||
    (failure.status === 404 && failure.code === 'NOT_FOUND') ||
    (failure.status === 422 && failure.code === 'VALIDATION_FAILED');
}

export function getAssetSummary(assetId: string, period: PeriodQuery, token: Credential): Promise<Summary> {
  return apiRequest(`/api/v1/assets/${encodeURIComponent(assetId)}/summary`, { token, query: period, expectedStatus: 200 }, isSummary);
}

const LOCAL_DATE = /^\d{4}-\d{2}-\d{2}$/;
const LOCAL_TIME = /^(?:[01]\d|2[0-3]):[0-5]\d$/;
const OFFSET = /^[+-](?:[01]\d|2[0-3]):[0-5]\d$/;
const INSTANT = /^(\d{4}-\d{2}-\d{2})T((?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d)(?:\.(\d{1,6}))?(Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/;
const DECIMAL = /^(?:0|[1-9]\d*)(?:\.\d+)?$/;
const ZERO = /^0(?:\.0+)?$/;
const ONE = /^1(?:\.0+)?$/;
const PARTIAL_RATIO = /^0(?:\.\d+)?$/;
const HISTORY_ORIGINS = new Set<unknown>(['live', 'import', 'dataset_replay', 'simulated'] satisfies SourceOrigin[]);

function isLocalDate(value: unknown): value is string {
  if (typeof value !== 'string' || !LOCAL_DATE.test(value) || value.startsWith('0000')) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return Number.isFinite(date.getTime()) && date.toISOString().startsWith(value);
}

/** Read an RFC 3339 instant at the service's microsecond precision, including non-Z offsets. */
export function historyInstant(value: unknown): number {
  const match = typeof value === 'string' ? INSTANT.exec(value) : null;
  if (match === null || !isLocalDate(match[1])) return NaN;
  // Parse whole seconds first so every engine handles the wire's fractional precision the same way.
  return Date.parse(`${match[1]}T${match[2]}${match[4]}`) + Number((match[3] ?? '').padEnd(6, '0')) / 1000;
}

function isTimezone(value: unknown): value is string {
  if (typeof value !== 'string' || value.length === 0) return false;
  try {
    new Intl.DateTimeFormat('en-GB', { timeZone: value });
    return true;
  } catch {
    return false;
  }
}

function isHistoryWindow(value: unknown, selection: HistorySelection): value is HistoryResponse['window'] {
  if (!isRecord(value) || value.timezone !== selection.timezone || !isTimezone(value.timezone) || !isLocalDate(value.start_date) ||
      !isLocalDate(value.end_date) || value.start_date !== selection.start_date ||
      value.end_date !== selection.end_date || value.start_date > value.end_date) return false;

  const start = historyInstant(value.start);
  const end = historyInstant(value.end);
  const cutoff = historyInstant(value.effective_end);
  return start < end && start <= cutoff && cutoff <= end && value.is_current === (cutoff < end);
}

function isEnergy(value: unknown): value is string {
  return typeof value === 'string' && DECIMAL.test(value);
}

function hasValidHistoryState(bucket: Record<string, unknown>, elapsed: boolean): boolean {
  const { state, energy_kwh, coverage, unavailable_reason } = bucket;
  if (state === 'unavailable') {
    return elapsed && energy_kwh === null && coverage === null &&
      typeof unavailable_reason === 'string' && unavailable_reason.trim().length > 0;
  }
  if (unavailable_reason !== null) return false;
  if (state === 'future') return !elapsed && energy_kwh === null && coverage === null;
  if (!elapsed || typeof coverage !== 'string') return false;
  if (state === 'missing') return energy_kwh === null && ZERO.test(coverage);
  if (state === 'measured') return isEnergy(energy_kwh) && ONE.test(coverage);
  return state === 'partial' && isEnergy(energy_kwh) && PARTIAL_RATIO.test(coverage);
}

function isHistoryBucket(
  value: unknown, start: number, window: HistoryResponse['window'], granularity: HistoryGranularity,
): value is HistoryResponse['buckets'][number] {
  if (!isRecord(value) || !isLocalDate(value.local_date) || value.local_date < window.start_date ||
      value.local_date > window.end_date || typeof value.utc_offset !== 'string' || !OFFSET.test(value.utc_offset)) return false;

  const localTime = value.local_time;
  if (granularity === 'day' ? localTime !== null : typeof localTime !== 'string' || !LOCAL_TIME.test(localTime)) return false;

  const actualStart = historyInstant(value.start);
  const actualEnd = historyInstant(value.end);
  return actualStart === start && actualEnd > actualStart &&
    actualEnd <= historyInstant(window.end) &&
    (granularity === 'day' || actualEnd - actualStart <= 3_600_000) &&
    hasValidHistoryState(value, actualStart < historyInstant(window.effective_end)) &&
    (value.comparison_kwh == null || isEnergy(value.comparison_kwh)) &&
    (value.reference_kwh == null || isEnergy(value.reference_kwh));
}

function isHistoryResponse(value: unknown, selection: HistorySelection): value is HistoryResponse {
  if (!isRecord(value) || value.bucket !== selection.bucket || !isHistoryWindow(value.window, selection) ||
      !Array.isArray(value.buckets) || value.buckets.length > 1_000 || !Array.isArray(value.origins) ||
      !value.origins.every((origin: unknown) => HISTORY_ORIGINS.has(origin)) ||
      (value.resolution_mwh !== null &&
        (typeof value.resolution_mwh !== 'number' || !Number.isSafeInteger(value.resolution_mwh) || value.resolution_mwh < 0)) ||
      (value.comparison_state != null && typeof value.comparison_state !== 'string')) return false;

  const { window, highest_bucket } = value;
  let nextStart = historyInstant(window.start);
  let highestMatched = false;
  const highestStart = isRecord(highest_bucket) ? historyInstant(highest_bucket.start) : NaN;
  for (const bucket of value.buckets as unknown[]) {
    if (!isHistoryBucket(bucket, nextStart, window, selection.bucket)) return false;
    if (nextStart === highestStart && bucket.state === 'measured') highestMatched = true;
    nextStart = historyInstant(bucket.end);
  }
  return (value.buckets.length === 0 || nextStart === historyInstant(window.end)) &&
    (highest_bucket === null || highestMatched);
}

/** Read the selected asset's recorded series, with the service's own bucket states and highest pointer. */
export async function getAssetHistory(
  assetId: string, selection: HistorySelection, token: Credential,
): Promise<HistoryResponse> {
  const { start_date, end_date, bucket } = selection;
  const history = await apiRequest(
    `/api/v1/assets/${encodeURIComponent(assetId)}/measurements`,
    { token, query: { start_date, end_date, bucket } },
    (value): value is HistoryResponse => isHistoryResponse(value, selection),
  );
  if (history === undefined) throw ApiError.unexpected();
  return history;
}

export type ImportPreview = components['schemas']['ImportPreviewResponse'];
export type ImportCommit = components['schemas']['ImportCommitResponse'];
export type ImportResult = components['schemas']['ImportCommitResultResponse'];
export type ImportQuestion = components['schemas']['ImportQuestionResponse'];
export type ImportRowError = components['schemas']['ImportRowErrorResponse'];
export type ImportErrorPage = components['schemas']['ImportErrorPageResponse'];
export type ImportPeriod = components['schemas']['ImportPeriodResponse'];
export type AssetCandidate = components['schemas']['AssetCandidateResponse'];

/**
 * The user's answers, sent as the `mapping` form part. Hand-written because the multipart body documents
 * `mapping` as a string: this mirrors the service's `ImportMappingRequest`.
 */
export type ImportAnswers = {
  value_kind?: 'interval_energy' | 'average_power' | 'counter';
  power_meaning?: 'average' | 'instantaneous';
  timezone_confirmed?: boolean;
  interval_minutes?: Record<string, number>;
  asset_map?: Record<string, string>;
  scope?: 'disjoint' | 'unknown_overlap';
};

/** What is checked: pasted text, a web `File`, or a native file the picker copied to the cache. */
export type ImportSource =
  | { kind: 'paste'; text: string }
  | { kind: 'file'; file: File }
  | { kind: 'file'; uri: string; name: string; mimeType?: string };

const IMPORT_ERROR_PAGE_SIZE = '50';
const IMPORT_COUNTS = ['total_rows', 'accepted_rows', 'invalid_rows', 'duplicate_rows', 'conflict_rows', 'pending_rows'] as const;

function isImportPreview(value: unknown): value is ImportPreview {
  return (
    isRecord(value) &&
    typeof value.id === 'string' &&
    typeof value.file_name === 'string' &&
    IMPORT_COUNTS.every((count) => Number.isInteger(value[count])) &&
    typeof value.blocked === 'boolean' &&
    typeof value.needs_acknowledgment === 'boolean' &&
    Array.isArray(value.questions) &&
    Array.isArray(value.errors) &&
    Array.isArray(value.assumptions) &&
    Array.isArray(value.block_reasons) &&
    isRecord(value.mapping)
  );
}

function isImportCommit(value: unknown): value is ImportCommit {
  return (
    isRecord(value) &&
    typeof value.import_id === 'string' &&
    Number.isInteger(value.rows_added) &&
    Number.isInteger(value.rows_skipped) &&
    Number.isInteger(value.rows_duplicate) &&
    Number.isInteger(value.rows_after_site_clock) &&
    typeof value.replayed === 'boolean'
  );
}

function isImportErrorPage(value: unknown): value is ImportErrorPage {
  return isRecord(value) && Array.isArray(value.items) && (value.next_cursor === null || typeof value.next_cursor === 'string');
}

/** The file part: a web `File` as it is, or a native `{ uri, name, type }` part that the platform uploads. */
function appendSource(form: FormData, source: ImportSource) {
  if (source.kind === 'paste') {
    form.append('text', source.text);
  } else if ('file' in source) {
    form.append('file', source.file);
  } else {
    // React Native's FormData takes this shape and streams the file; its types only know Blob.
    form.append('file', { uri: source.uri, name: source.name, type: source.mimeType ?? 'text/csv' } as unknown as Blob);
  }
}

/** Stores a preview. It saves no reading and carries no key, so a lost answer is simply sent again (027 D4). */
export function previewImport(siteId: string, source: ImportSource, answers: ImportAnswers, token: Credential): Promise<ImportPreview> {
  const form = new FormData();
  appendSource(form, source);
  form.append('mapping', JSON.stringify(answers));
  return apiRequest(
    `/api/v1/sites/${encodeURIComponent(siteId)}/imports/preview`,
    { method: 'POST', token, form, timeoutMs: IMPORT_PREVIEW_TIMEOUT_MS },
    isImportPreview,
  );
}

/** Reads a stored preview, including its result once committed. Checked before any commit is sent again. */
export function getImport(importId: string, token: Credential): Promise<ImportPreview> {
  return apiRequest(`/api/v1/imports/${encodeURIComponent(importId)}`, { token, expectedStatus: 200 },
    (value): value is ImportPreview => isImportPreview(value) && value.id === importId &&
      (!value.result || (value.status === 'committed' && value.result.import_id === importId)));
}

export function getImportErrors(importId: string, cursor: string, token: Credential): Promise<ImportErrorPage> {
  return apiRequest(
    `/api/v1/imports/${encodeURIComponent(importId)}/errors`,
    { token, query: { limit: IMPORT_ERROR_PAGE_SIZE, cursor } },
    isImportErrorPage,
  );
}

/** One commit intent: a resend keeps the key and the acknowledgment, so the service replays instead of importing twice. */
export function commitImport(importId: string, acknowledge: boolean, key: string, token: Credential, beforeDispatch?: () => void): Promise<ImportCommit> {
  return apiRequest(
    `/api/v1/imports/${encodeURIComponent(importId)}/commit`,
    {
      method: 'POST',
      token,
      body: { acknowledge_skipped: acknowledge },
      headers: { 'Idempotency-Key': key },
      timeoutMs: IMPORT_COMMIT_TIMEOUT_MS, beforeDispatch,
    },
    (value): value is ImportCommit => isImportCommit(value) && value.import_id === importId,
  );
}

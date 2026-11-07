import { ApiError, readFailure } from '@/api/errors';
import type { components, paths } from '@/api/schema.generated';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';
const TIMEOUT_MS = 10_000;
const CAPABILITIES_PATH = '/api/v1/capabilities';

export type CapabilityManifest =
  paths[typeof CAPABILITIES_PATH]['get']['responses'][200]['content']['application/json'];
export type DemoSession = components['schemas']['DemoSessionResponse'];
export type Summary = components['schemas']['SummaryResponse'];

type RequestOptions = {
  method?: 'GET' | 'POST' | 'DELETE';
  body?: unknown;
  token?: string | null;
  headers?: Record<string, string>;
  query?: Record<string, string | undefined>;
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
  { method = 'GET', body, token, headers, query }: RequestOptions,
  isValid: (value: unknown) => value is T,
): Promise<T> {
  const search = new URLSearchParams(
    Object.entries(query ?? {}).filter((entry): entry is [string, string] => entry[1] !== undefined),
  ).toString();
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}${search ? `?${search}` : ''}`, {
      method,
      headers: {
        ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...headers,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
  } catch {
    throw ApiError.unreachable();
  }
  if (!response.ok) {
    throw await readFailure(response);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  const payload: unknown = await response.json().catch(() => null);
  if (!isValid(payload)) {
    throw ApiError.unexpected();
  }
  return payload;
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
  return isRecord(value) && typeof value.start_date === 'string' && typeof value.end_date === 'string';
}

function isDemoSession(value: unknown): value is DemoSession {
  return (
    isRecord(value) &&
    typeof value.token === 'string' &&
    typeof value.site_id === 'string' &&
    typeof value.scenario_id === 'string' &&
    typeof value.expires_at === 'string' &&
    isPeriod(value.initial_period)
  );
}

function isSummary(value: unknown): value is Summary {
  return (
    isRecord(value) &&
    isRecord(value.window) &&
    isRecord(value.scope) &&
    isRecord(value.coverage) &&
    Array.isArray(value.assets) &&
    (value.energy_kwh === null || typeof value.energy_kwh === 'string')
  );
}

export function getCapabilities(): Promise<CapabilityManifest> {
  return apiRequest(CAPABILITIES_PATH, {}, isCapabilityManifest);
}

/** Starts a demo, or recovers the same one: the key, proof and body must stay unchanged across retries. */
export function createDemoSession(scenarioId: string, operationId: string, replayProof: string): Promise<DemoSession> {
  return apiRequest(
    '/api/v1/demo/sessions',
    {
      method: 'POST',
      body: { scenario_id: scenarioId },
      headers: { 'Idempotency-Key': operationId, 'X-Demo-Replay-Proof': replayProof },
    },
    isDemoSession,
  );
}

export type PeriodQuery = { preset?: string; start_date?: string; end_date?: string };

export function getSummary(siteId: string, period: PeriodQuery, token: string): Promise<Summary> {
  return apiRequest(`/api/v1/sites/${encodeURIComponent(siteId)}/summary`, { token, query: period }, isSummary);
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

export function getInsights(siteId: string, period: PeriodQuery, token: string): Promise<InsightList> {
  return apiRequest(`/api/v1/sites/${encodeURIComponent(siteId)}/insights`, { token, query: period }, isInsightList);
}

/** Always one exact revision: the evidence screen must show what the card showed, even after a correction. */
export function getInsight(insightId: string, revision: number, token: string): Promise<Insight> {
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
export function sendFeedback(insightId: string, revision: number, action: FeedbackAction, key: string, token: string): Promise<FeedbackResult> {
  return apiRequest(
    `/api/v1/insights/${encodeURIComponent(insightId)}/feedback`,
    { method: 'POST', token, body: { action, revision }, headers: { 'Idempotency-Key': key } },
    isFeedbackResult,
  );
}

export function getHiddenInsights(siteId: string, period: PeriodQuery, token: string): Promise<HiddenInsights> {
  return apiRequest(`/api/v1/sites/${encodeURIComponent(siteId)}/insights/hidden`, { token, query: period }, isHiddenInsights);
}

export type Asset = components['schemas']['AssetResponse'];
export type AssetPage = components['schemas']['AssetPageResponse'];
export type AssetDetail = components['schemas']['AssetDetailResponse'];
export type AssetSource = components['schemas']['SourceResponse'];
export type AssetBinding = components['schemas']['BindingResponse'];
export type AssetEnergy = components['schemas']['AssetEnergyResponse'];
export type ScopeKind = components['schemas']['ScopeKind'];
export type SourceOrigin = components['schemas']['SourceOrigin'];
export type TransportStatus = components['schemas']['TransportStatus'];

const ASSET_PAGE_SIZE = '100';
const MAX_ASSET_PAGES = 20;

function isAssetPage(value: unknown): value is AssetPage {
  return (
    isRecord(value) &&
    Array.isArray(value.items) &&
    value.items.every((item: unknown) => isRecord(item) && typeof item.id === 'string') &&
    (value.next_cursor === null || typeof value.next_cursor === 'string')
  );
}

function isAssetDetail(value: unknown): value is AssetDetail {
  return (
    isRecord(value) &&
    typeof value.id === 'string' &&
    typeof value.name === 'string' &&
    Array.isArray(value.bindings) &&
    Array.isArray(value.sources)
  );
}

/** Every asset of a site, following the cursor. The page limit stops a cursor that never ends. */
export async function getAssets(siteId: string, token: string): Promise<Asset[]> {
  const assets: Asset[] = [];
  let cursor: string | undefined;
  for (let page = 0; page < MAX_ASSET_PAGES; page += 1) {
    const { items, next_cursor: next }: AssetPage = await apiRequest(
      `/api/v1/sites/${encodeURIComponent(siteId)}/assets`,
      { token, query: { limit: ASSET_PAGE_SIZE, cursor } },
      isAssetPage,
    );
    assets.push(...items);
    if (next === null) {
      break;
    }
    cursor = next;
  }
  return assets;
}

export function getAsset(assetId: string, token: string): Promise<AssetDetail> {
  return apiRequest(`/api/v1/assets/${encodeURIComponent(assetId)}`, { token }, isAssetDetail);
}

export function getAssetSummary(assetId: string, period: PeriodQuery, token: string): Promise<Summary> {
  return apiRequest(`/api/v1/assets/${encodeURIComponent(assetId)}/summary`, { token, query: period }, isSummary);
}

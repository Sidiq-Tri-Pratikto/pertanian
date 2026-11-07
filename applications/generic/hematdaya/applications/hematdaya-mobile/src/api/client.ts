import { ApiError, readFailure } from '@/api/errors';
import type { components, paths } from '@/api/schema.generated';

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

type RequestOptions = {
  method?: 'GET' | 'POST' | 'DELETE';
  body?: unknown;
  token?: string | null;
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
  { method = 'GET', body, token, headers, query, form, timeoutMs = TIMEOUT_MS }: RequestOptions,
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
      body: form ?? (body !== undefined ? JSON.stringify(body) : undefined),
      signal: AbortSignal.timeout(timeoutMs),
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
export function previewImport(siteId: string, source: ImportSource, answers: ImportAnswers, token: string): Promise<ImportPreview> {
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
export function getImport(importId: string, token: string): Promise<ImportPreview> {
  return apiRequest(`/api/v1/imports/${encodeURIComponent(importId)}`, { token }, isImportPreview);
}

export function getImportErrors(importId: string, cursor: string, token: string): Promise<ImportErrorPage> {
  return apiRequest(
    `/api/v1/imports/${encodeURIComponent(importId)}/errors`,
    { token, query: { limit: IMPORT_ERROR_PAGE_SIZE, cursor } },
    isImportErrorPage,
  );
}

/** One commit intent: a resend keeps the key and the acknowledgment, so the service replays instead of importing twice. */
export function commitImport(importId: string, acknowledge: boolean, key: string, token: string): Promise<ImportCommit> {
  return apiRequest(
    `/api/v1/imports/${encodeURIComponent(importId)}/commit`,
    {
      method: 'POST',
      token,
      body: { acknowledge_skipped: acknowledge },
      headers: { 'Idempotency-Key': key },
      timeoutMs: IMPORT_COMMIT_TIMEOUT_MS,
    },
    isImportCommit,
  );
}

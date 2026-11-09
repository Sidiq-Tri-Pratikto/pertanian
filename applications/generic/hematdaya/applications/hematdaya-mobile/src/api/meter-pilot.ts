import { apiRequest, type RequestCredential } from '@/api/client';
import type { components } from '@/api/schema.generated';

export const PILOT_METER_ID = 'shelly-plug-pm-gen3';

type DeviceCatalog = components['schemas']['DeviceCatalogResponse'];
type PilotSession = components['schemas']['PilotSessionResponse'];
type Site = components['schemas']['SiteResponse'];
export type MeterEnrollment = components['schemas']['EnrollmentResponse'];

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isId(value: unknown): value is string {
  return typeof value === 'string' && value.length > 0;
}

function isInstant(value: unknown): value is string {
  return typeof value === 'string' && Number.isFinite(Date.parse(value));
}

function isCatalog(value: unknown): value is DeviceCatalog {
  return isObject(value) && Array.isArray(value.devices) && value.devices.every((entry: unknown) =>
    isObject(entry) && entry.id === PILOT_METER_ID && isId(entry.name) &&
    (entry.status === 'planned' || entry.status === 'available') && entry.measurement_kind === 'counter' &&
    entry.scope_kind === 'device' && Number.isSafeInteger(entry.cadence_seconds) && Number(entry.cadence_seconds) > 0);
}

function isEnrollment(value: unknown): value is MeterEnrollment {
  if (!isObject(value) || !isId(value.id) || !isInstant(value.expires_at)) return false;
  switch (value.status) {
    case 'waiting':
      return value.first_measured_at === null && value.asset_id === null;
    case 'ready':
      return isInstant(value.first_measured_at) && value.asset_id === null;
    case 'connected':
      return isInstant(value.first_measured_at) && isId(value.asset_id);
    case 'expired':
      return (value.first_measured_at === null || isInstant(value.first_measured_at)) && value.asset_id === null;
    default:
      return false;
  }
}

export function getDeviceCatalog(): Promise<DeviceCatalog> {
  return apiRequest('/api/v1/device-catalog', { expectedStatus: 200 }, isCatalog);
}

/** The operator-issued code is a bearer credential. It never enters a query key or persisted storage. */
export function getPilotSession(code: string): Promise<PilotSession> {
  return apiRequest('/api/v1/pilot/session', { token: code, expectedStatus: 200 },
    (value): value is PilotSession => isObject(value) && isId(value.site_id) && isInstant(value.expires_at));
}

export function getPilotSite(siteId: string, code: string): Promise<Site> {
  return apiRequest(`/api/v1/sites/${encodeURIComponent(siteId)}`, { token: code, expectedStatus: 200 },
    (value): value is Site => isObject(value) && value.id === siteId && value.kind === 'standard' && isId(value.timezone) && isInstant(value.now));
}

export function startMeterEnrollment(siteId: string, key: string, credential: RequestCredential): Promise<MeterEnrollment> {
  const body: components['schemas']['StartEnrollmentRequest'] = { model_id: PILOT_METER_ID };
  return apiRequest(`/api/v1/sites/${encodeURIComponent(siteId)}/enrollments`, {
    method: 'POST', body, token: credential, headers: { 'Idempotency-Key': key },
  }, isEnrollment);
}

export function getMeterEnrollment(id: string, credential: RequestCredential): Promise<MeterEnrollment> {
  return apiRequest(`/api/v1/enrollments/${encodeURIComponent(id)}`, { token: credential, expectedStatus: 200 },
    (value): value is MeterEnrollment => isEnrollment(value) && value.id === id);
}

export function confirmMeterEnrollment(
  id: string, assetName: string, key: string, credential: RequestCredential,
): Promise<MeterEnrollment> {
  const body: components['schemas']['ConfirmEnrollmentRequest'] = { asset_name: assetName };
  return apiRequest(`/api/v1/enrollments/${encodeURIComponent(id)}/confirm`, {
    method: 'POST', body, token: credential, headers: { 'Idempotency-Key': key },
  }, (value): value is MeterEnrollment => isEnrollment(value) && value.id === id && value.status === 'connected');
}

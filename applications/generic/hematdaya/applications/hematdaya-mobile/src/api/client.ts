import { ApiError, readFailure } from '@/api/errors';
import type { paths } from '@/api/schema.generated';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';
const TIMEOUT_MS = 10_000;
const CAPABILITIES_PATH = '/api/v1/capabilities';

export type CapabilityManifest =
  paths[typeof CAPABILITIES_PATH]['get']['responses'][200]['content']['application/json'];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
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

export async function getCapabilities(): Promise<CapabilityManifest> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${CAPABILITIES_PATH}`, { signal: AbortSignal.timeout(TIMEOUT_MS) });
  } catch {
    throw ApiError.unreachable();
  }
  if (!response.ok) {
    throw await readFailure(response);
  }

  const manifest: unknown = await response.json().catch(() => null);
  if (!isCapabilityManifest(manifest)) {
    throw ApiError.unexpected();
  }
  return manifest;
}

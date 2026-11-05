import { ApiError, readFailure } from '@/api/errors';
import type { components, paths } from '@/api/schema.generated';

// Same origin: next.config.ts forwards /api/v1 to the service, so cookies stay first-party.
const TIMEOUT_MS = 10_000;

type JsonOf<Path extends keyof paths> = paths[Path] extends {
  get: { responses: { 200: { content: { 'application/json': infer Body } } } };
}
  ? Body
  : never;

async function getJson<Path extends keyof paths>(path: Path): Promise<JsonOf<Path>> {
  let response: Response;
  try {
    response = await fetch(String(path), { signal: AbortSignal.timeout(TIMEOUT_MS), cache: 'no-store' });
  } catch {
    throw ApiError.unreachable();
  }
  if (!response.ok) {
    throw await readFailure(response);
  }
  return (await response.json()) as JsonOf<Path>;
}

export type CapabilityManifest = components['schemas']['CapabilityManifestResponse'];

export function getCapabilities(): Promise<CapabilityManifest> {
  return getJson('/api/v1/capabilities');
}

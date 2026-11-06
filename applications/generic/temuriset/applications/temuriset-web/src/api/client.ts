import { ApiError, readFailure } from '@/api/errors';
import type { components, paths } from '@/api/schema.generated';

// Same origin: next.config.ts forwards /api/v1 to the service, so cookies stay first-party.
const TIMEOUT_MS = 10_000;

type JsonOf<Path extends keyof paths> = paths[Path] extends {
  get: { responses: { 200: { content: { 'application/json': infer Body } } } };
}
  ? Body
  : never;

/** Make one bounded same-origin request and normalize the registered failure envelope. */
export async function getResponse(path: string, options?: RequestInit): Promise<Response> {
  let response: Response;
  try {
    response = await fetch(path, { ...options, signal: AbortSignal.timeout(TIMEOUT_MS), cache: 'no-store' });
  } catch {
    throw ApiError.unreachable();
  }
  if (!response.ok) {
    throw await readFailure(response);
  }
  return response;
}

export async function getJson<Path extends keyof paths>(path: Path): Promise<JsonOf<Path>> {
  return (await (await getResponse(path)).json()) as JsonOf<Path>;
}

export type CapabilityManifest = components['schemas']['CapabilityManifestResponse'];
export type Me = components['schemas']['MeResponse'];

type SendOptions = {
  /** Consequential POSTs send one key per user intent, so a retry never repeats the effect. */
  idempotencyKey?: string;
};

/**
 * Sends a change through the same-origin proxy. The browser adds the `Origin` header the service checks, and the
 * session cookie stays first-party.
 */
export async function send<Body>(method: 'POST' | 'PUT' | 'PATCH' | 'DELETE', path: string, body?: unknown, options: SendOptions = {}): Promise<Body> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (options.idempotencyKey) headers['Idempotency-Key'] = options.idempotencyKey;
  const response = await getResponse(path, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  return (response.status === 204 ? undefined : await response.json()) as Body;
}

export function newIdempotencyKey(): string {
  return crypto.randomUUID();
}

export function getCapabilities(): Promise<CapabilityManifest> {
  return getJson('/api/v1/capabilities');
}

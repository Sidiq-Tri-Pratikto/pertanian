import { ApiError, readFailure } from '@/api/errors';
import type { paths } from '@/api/schema.generated';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';
const TIMEOUT_MS = 10_000;

type JsonOf<Path extends keyof paths> = paths[Path] extends {
  get: { responses: { 200: { content: { 'application/json': infer Body } } } };
}
  ? Body
  : never;

async function getJson<Path extends keyof paths>(path: Path): Promise<JsonOf<Path>> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${String(path)}`, { signal: AbortSignal.timeout(TIMEOUT_MS) });
  } catch {
    throw ApiError.unreachable();
  }
  if (!response.ok) {
    throw await readFailure(response);
  }
  return (await response.json()) as JsonOf<Path>;
}

export function getHealth() {
  return getJson('/health') as Promise<{ status: string }>;
}

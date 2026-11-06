import { QueryClient } from '@tanstack/react-query';

import { ApiError, DEFAULT_MAX_ATTEMPTS } from '@/api/errors';

/** Codes that mean the stored credential no longer opens anything. */
export const SESSION_ENDED_CODES = new Set(['SESSION_EXPIRED', 'UNAUTHORIZED']);

/**
 * Retry only what the service says is retryable, and count the first attempt within `max_attempts`.
 *
 * @param failureCount Failures so far, including the one being judged.
 * @param error The failure.
 */
export function shouldRetry(failureCount: number, error: unknown): boolean {
  const { recovery } = ApiError.from(error);
  return recovery.retryable === true && failureCount < (recovery.max_attempts ?? DEFAULT_MAX_ATTEMPTS);
}

/** Wait as long as the service asks, or one second. */
export function retryDelay(_failureCount: number, error: unknown): number {
  return (ApiError.from(error).recovery.retry_after_seconds ?? 1) * 1000;
}

/** Whether a failure means the stored credential no longer opens anything. */
export function endsSession(error: unknown): boolean {
  return error instanceof ApiError && SESSION_ENDED_CODES.has(error.code);
}

/** The one client for server state. */
export function createQueryClient(): QueryClient {
  return new QueryClient({ defaultOptions: { queries: { retry: shouldRetry, retryDelay, staleTime: 30_000 } } });
}

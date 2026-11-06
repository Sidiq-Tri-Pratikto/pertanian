import { useEffect, useState } from 'react';

import { getCapabilities, type CapabilityManifest } from '@/api/client';
import { ApiError, DEFAULT_MAX_ATTEMPTS } from '@/api/errors';

type CapabilitiesState = (
  | { kind: 'loading' }
  | { kind: 'available'; manifest: CapabilityManifest }
  | { kind: 'failed'; error: ApiError; retryStatus: 'ready' | 'waiting' | 'unavailable' }
) & { attempt: number };

/** Reads the service manifest. It explains what is available and never decides what is allowed. */
export function useCapabilities() {
  const [state, setState] = useState<CapabilitiesState>({ kind: 'loading', attempt: 1 });
  const { attempt } = state;

  useEffect(() => {
    let active = true;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    getCapabilities().then(
      (manifest) => active && setState({ kind: 'available', attempt, manifest }),
      (failure: unknown) => {
        if (!active) {
          return;
        }
        const error = ApiError.from(failure);
        const maxAttempts = error.recovery.max_attempts ?? DEFAULT_MAX_ATTEMPTS;
        const canRetry =
          error.recovery.retryable === true && Number.isSafeInteger(maxAttempts) && attempt < maxAttempts;
        const delayMs = (error.recovery.retry_after_seconds ?? 0) * 1000;
        if (!canRetry) {
          setState({ kind: 'failed', attempt, error, retryStatus: 'unavailable' });
        } else if (delayMs > 0) {
          setState({ kind: 'failed', attempt, error, retryStatus: 'waiting' });
          retryTimer = setTimeout(() => setState({ kind: 'failed', attempt, error, retryStatus: 'ready' }), delayMs);
        } else {
          setState({ kind: 'failed', attempt, error, retryStatus: 'ready' });
        }
      },
    );
    return () => {
      active = false;
      clearTimeout(retryTimer);
    };
  }, [attempt]);

  const retry = () => {
    setState((current) =>
      current.kind === 'failed' && current.retryStatus === 'ready'
        ? { kind: 'loading', attempt: current.attempt + 1 }
        : current,
    );
  };

  return { state, retry };
}

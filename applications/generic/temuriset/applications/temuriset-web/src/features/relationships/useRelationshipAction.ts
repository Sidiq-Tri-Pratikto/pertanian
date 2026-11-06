'use client';

import { useRef, useState } from 'react';

import { newIdempotencyKey, send } from '@/api/client';
import { ApiError } from '@/api/errors';
import type { Partnership } from '@/features/relationships/model';

/** Reuse the same key for the same request until the service gives a definitive answer. */
export function useRelationshipAction() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<{ failure: ApiError; attempt: number } | null>(null);
  const pending = useRef(false);
  const intent = useRef<{ signature: string; key: string; attempts: number; max?: number } | null>(null);

  async function run(path: string, body: object): Promise<Partnership | null> {
    if (pending.current) return null;
    const signature = JSON.stringify([path, body]);
    if (intent.current?.signature !== signature) intent.current = { signature, key: newIdempotencyKey(), attempts: 0 };
    const request = intent.current;
    if (request.max !== undefined && request.attempts >= request.max) return null;

    request.attempts += 1;
    pending.current = true;
    setBusy(true);
    setError(null);
    try {
      const result = await send<Partnership>('POST', path, body, { idempotencyKey: request.key });
      intent.current = null;
      return result;
    } catch (caught) {
      const failure = ApiError.from(caught);
      if (failure.recovery.retryable) request.max = failure.recovery.max_attempts ?? 3;
      else intent.current = null;
      setError({ failure, attempt: request.attempts });
      return null;
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }

  return { run, busy, error, clearError: () => setError(null) };
}

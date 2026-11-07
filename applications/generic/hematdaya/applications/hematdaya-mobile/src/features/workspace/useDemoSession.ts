import { useCallback, useRef, useState } from 'react';

import { createDemoSession } from '@/api/client';
import { ApiError } from '@/api/errors';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';
import { randomToken } from '@/lib/random';

/** One intentional creation. Retries resend exactly this; a new start makes a new one. Never logged or drafted. */
type CreateIntent = { scenarioId: string; operationId: string; replayProof: string; attempts: number };

export type CreateState =
  | { kind: 'idle' }
  | { kind: 'pending' }
  | { kind: 'failed'; error: ApiError; canRetry: boolean }
  | { kind: 'unknown'; error: ApiError };

/** Starts a demo or empty workspace with one operation ID and replay proof per intent (spec 008). */
export function useDemoSession() {
  const { open } = useWorkspace();
  const intent = useRef<CreateIntent | null>(null);
  const [state, setState] = useState<CreateState>({ kind: 'idle' });

  const send = useCallback(async (): Promise<boolean> => {
    const current = intent.current;
    if (!current) {
      return false;
    }
    current.attempts += 1;
    setState({ kind: 'pending' });
    try {
      const session = await createDemoSession(current.scenarioId, current.operationId, current.replayProof);
      intent.current = null;
      await open({
        token: session.token,
        siteId: session.site_id,
        scenarioId: session.scenario_id,
        expiresAt: session.expires_at,
        initialPeriod: session.initial_period,
      });
      setState({ kind: 'idle' });
      return true;
    } catch (failure) {
      const error = ApiError.from(failure);
      if (error.code === 'CONFLICT') {
        // The replay window passed or the workspace ended: the first outcome is unknown, so never start silently.
        setState({ kind: 'unknown', error });
      } else {
        const maxAttempts = error.recovery.max_attempts ?? 3;
        setState({ kind: 'failed', error, canRetry: error.recovery.retryable === true && current.attempts < maxAttempts });
      }
      return false;
    }
  }, [open]);

  /** Begin a new intent, or resend the pending one for the same scenario. */
  const start = useCallback(
    (scenarioId: string) => {
      if (intent.current?.scenarioId !== scenarioId) {
        intent.current = { scenarioId, operationId: randomToken(16), replayProof: randomToken(32), attempts: 0 };
      }
      return send();
    },
    [send],
  );

  /** Explicitly start over after an unknown outcome, with a fresh key and proof. */
  const startOver = useCallback(
    (scenarioId: string) => {
      intent.current = null;
      return start(scenarioId);
    },
    [start],
  );

  const reset = useCallback(() => {
    intent.current = null;
    setState({ kind: 'idle' });
  }, []);

  return { state, start, retry: send, startOver, reset };
}

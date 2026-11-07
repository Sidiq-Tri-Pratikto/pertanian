import { useCallback, useRef, useState } from 'react';

import { createDemoSession } from '@/api/client';
import { ApiError } from '@/api/errors';
import { isKnownOffline } from '@/features/offline/useConnectivity';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';
import { randomToken } from '@/lib/random';

/** One intentional creation. Its proof stays in memory for explicit replay only. */
type CreateIntent = { owner: number; scenarioId: string; operationId: string; replayProof: string; attempts: number };

export type CreateState =
  | { kind: 'idle' }
  | { kind: 'pending' }
  | { kind: 'unsent'; error: ApiError }
  | { kind: 'failed'; error: ApiError; canRetry: boolean }
  | { kind: 'unknown'; error: ApiError; unsent?: boolean };

/** Starts or explicitly replays a demo using one operation ID and proof per actual dispatch. */
export function useDemoSession() {
  const { open, credentialGeneration, isCurrentCredential } = useWorkspace();
  const intent = useRef<CreateIntent | null>(null);
  const busy = useRef<{ owner: number } | null>(null);
  const [operation, setOperation] = useState<{ owner: number; state: CreateState } | null>(null);

  const reportUnsent = useCallback((error = ApiError.offline()) => {
    setOperation((previous) => ({
      owner: credentialGeneration,
      state: previous?.owner === credentialGeneration && previous.state.kind === 'unknown'
        ? { ...previous.state, unsent: true } : { kind: 'unsent', error },
    }));
  }, [credentialGeneration]);

  const send = useCallback(async (current: CreateIntent): Promise<boolean> => {
    if (!isCurrentCredential(current.owner) || busy.current?.owner === current.owner) return false;
    if (isKnownOffline()) {
      reportUnsent();
      return false;
    }
    const request = { owner: current.owner };
    busy.current = request;
    let opening = false;
    try {
      const session = await createDemoSession(current.scenarioId, current.operationId, current.replayProof, () => {
        if (!isCurrentCredential(current.owner)) throw ApiError.revoked();
        current.attempts += 1;
        intent.current = current;
        setOperation({ owner: current.owner, state: { kind: 'pending' } });
      });
      if (!isCurrentCredential(current.owner) || busy.current !== request) return false;
      opening = true;
      await open({
        token: session.token, siteId: session.site_id, scenarioId: session.scenario_id,
        expiresAt: session.expires_at, initialPeriod: session.initial_period,
      }, session);
      if (busy.current !== request || !isCurrentCredential(current.owner + 1)) return false;
      intent.current = null;
      setOperation(null);
      return true;
    } catch (failure) {
      if (!isCurrentCredential(current.owner) && !opening) return false;
      const error = ApiError.from(failure);
      if (error.code === 'WORKSPACE_CHANGED') return false;
      if (error.code === 'OFFLINE_UNSENT') {
        reportUnsent(error);
        return false;
      }
      const maxAttempts = error.recovery.max_attempts ?? 3;
      const state: CreateState = error.code === 'CONFLICT'
        ? { kind: 'unknown', error }
        : { kind: 'failed', error, canRetry: error.recovery.retryable === true && current.attempts < maxAttempts };
      setOperation({ owner: current.owner, state });
      return false;
    } finally {
      if (busy.current === request) busy.current = null;
    }
  }, [isCurrentCredential, open, reportUnsent]);

  const start = useCallback((scenarioId: string) => {
    if (!isCurrentCredential(credentialGeneration)) return Promise.resolve(false);
    if (isKnownOffline()) {
      reportUnsent();
      return Promise.resolve(false);
    }
    const existing = intent.current;
    return send(existing?.owner === credentialGeneration && existing.scenarioId === scenarioId ? existing : {
      owner: credentialGeneration, scenarioId, operationId: randomToken(16), replayProof: randomToken(32), attempts: 0,
    });
  }, [credentialGeneration, isCurrentCredential, reportUnsent, send]);

  const startOver = useCallback((scenarioId: string) => {
    if (!isKnownOffline()) intent.current = null;
    return start(scenarioId);
  }, [start]);

  const retry = useCallback(() => intent.current?.owner === credentialGeneration
    ? send(intent.current) : Promise.resolve(false), [credentialGeneration, send]);

  const reset = useCallback(() => {
    intent.current = null;
    setOperation(null);
  }, []);

  const state: CreateState = operation?.owner === credentialGeneration ? operation.state : { kind: 'idle' };
  return { state, start, retry, startOver, reset };
}

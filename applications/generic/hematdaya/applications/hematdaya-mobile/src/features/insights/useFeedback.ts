import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useRef, useState } from 'react';

import { sendFeedback, type FeedbackAction, type FeedbackResult } from '@/api/client';
import { ApiError } from '@/api/errors';
import { useNavigationContext } from '@/features/navigation-context/NavigationContextProvider';
import { isKnownOffline } from '@/features/offline/useConnectivity';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';
import { randomToken } from '@/lib/random';

type Intent = { owner: string; action: FeedbackAction; key: string; attempts: number };

export type FeedbackState =
  | { kind: 'idle' }
  | { kind: 'unsent'; action: FeedbackAction; error: ApiError }
  | { kind: 'pending'; action: FeedbackAction }
  | { kind: 'confirmed'; result: FeedbackResult }
  | { kind: 'failed'; action: FeedbackAction; error: ApiError; canRetry: boolean }
  | { kind: 'unknown'; action: FeedbackAction; error: ApiError; unsent?: boolean };

/** One explicitly dispatched intent per key. Only the active credential can publish its outcome. */
export function useFeedback(insightId: string, revision: number, onConfirmed?: (result: FeedbackResult) => void) {
  const { credential, credentialGeneration } = useWorkspace();
  const queryClient = useQueryClient();
  const { recentlyHidden, setRecentlyHidden } = useNavigationContext();
  const intent = useRef<Intent | null>(null);
  const busy = useRef<{ owner: string } | null>(null);
  const owner = `${credentialGeneration}:${insightId}:${revision}`;
  const [operation, setOperation] = useState<{ owner: string; value: FeedbackState } | null>(null);

  const reportUnsent = useCallback((action: FeedbackAction, error = ApiError.offline()) => {
    setOperation((previous) => ({
      owner, value: previous?.owner === owner && previous.value.kind === 'unknown'
        ? { ...previous.value, unsent: true } : { kind: 'unsent', action, error },
    }));
  }, [owner]);

  const send = useCallback(async (current: Intent) => {
    if (!credential?.current() || busy.current?.owner === owner) return;
    if (isKnownOffline()) {
      reportUnsent(current.action);
      return;
    }
    const request = { owner };
    busy.current = request;
    try {
      const result = await sendFeedback(insightId, revision, current.action, current.key, credential, () => {
        current.attempts += 1;
        intent.current = current;
        setOperation({ owner, value: { kind: 'pending', action: current.action } });
      });
      if (!credential.current() || busy.current !== request) return;
      intent.current = null;
      setOperation({ owner, value: { kind: 'confirmed', result } });
      if (result.action === 'restore' && recentlyHidden?.id === insightId) setRecentlyHidden(null);
      onConfirmed?.(result);
      await Promise.all(
        [['insights'], ['hidden-insights'], ['insight', insightId]].map((queryKey) => queryClient.invalidateQueries({ queryKey })),
      );
    } catch (failure) {
      if (!credential.current() || busy.current !== request) return;
      const error = ApiError.from(failure);
      if (error.code === 'OFFLINE_UNSENT') {
        reportUnsent(current.action, error);
        return;
      }
      const maxAttempts = error.recovery.max_attempts ?? 3;
      const value: FeedbackState = error.code === 'NETWORK_UNREACHABLE'
        ? { kind: 'unknown', action: current.action, error }
        : { kind: 'failed', action: current.action, error, canRetry: error.recovery.retryable === true && current.attempts < maxAttempts };
      setOperation({ owner, value });
    } finally {
      if (busy.current === request) busy.current = null;
    }
  }, [credential, insightId, onConfirmed, owner, queryClient, recentlyHidden, reportUnsent, revision, setRecentlyHidden]);

  const give = useCallback((action: FeedbackAction) => {
    if (!credential?.current()) return;
    if (isKnownOffline()) {
      reportUnsent(action);
      return;
    }
    const existing = intent.current;
    return send(existing?.owner === owner && existing.action === action
      ? existing : { owner, action, key: randomToken(16), attempts: 0 });
  }, [credential, owner, reportUnsent, send]);

  const retry = useCallback(() => {
    if (intent.current?.owner === owner) return send(intent.current);
  }, [owner, send]);

  const state: FeedbackState = operation?.owner === owner ? operation.value : { kind: 'idle' };
  return { state, give, retry };
}

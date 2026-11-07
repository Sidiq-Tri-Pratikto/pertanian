import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useRef, useState } from 'react';

import { sendFeedback, type FeedbackAction, type FeedbackResult } from '@/api/client';
import { ApiError } from '@/api/errors';
import { endsSession } from '@/api/query-client';
import { useNavigationContext } from '@/features/navigation-context/NavigationContextProvider';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';
import { randomToken } from '@/lib/random';

type Intent = { action: FeedbackAction; key: string; attempts: number };

export type FeedbackState =
  | { kind: 'idle' }
  | { kind: 'pending'; action: FeedbackAction }
  | { kind: 'confirmed'; result: FeedbackResult }
  | { kind: 'failed'; action: FeedbackAction; error: ApiError; canRetry: boolean }
  | { kind: 'unknown'; action: FeedbackAction; error: ApiError };

/**
 * Feedback on one evidence revision (spec 023). One idempotency key per intent: a retry or a check after a lost
 * response resends it, so the service replays instead of applying twice. Confirmed only after acknowledgment.
 */
export function useFeedback(insightId: string, revision: number, onConfirmed?: (result: FeedbackResult) => void) {
  const { workspace, end } = useWorkspace();
  const queryClient = useQueryClient();
  const { recentlyHidden, setRecentlyHidden } = useNavigationContext();
  const intent = useRef<Intent | null>(null);
  const [state, setState] = useState<FeedbackState>({ kind: 'idle' });

  const send = useCallback(async () => {
    const current = intent.current;
    if (!current || !workspace) {
      return;
    }
    current.attempts += 1;
    setState({ kind: 'pending', action: current.action });
    try {
      const result = await sendFeedback(insightId, revision, current.action, current.key, workspace.token);
      intent.current = null;
      setState({ kind: 'confirmed', result });
      if (result.action === 'restore' && recentlyHidden?.id === insightId) {
        setRecentlyHidden(null); // Restored from anywhere: the undo offer is done.
      }
      onConfirmed?.(result);
      await Promise.all(
        [['insights'], ['hidden-insights'], ['insight', insightId]].map((queryKey) => queryClient.invalidateQueries({ queryKey })),
      );
    } catch (failure) {
      const error = ApiError.from(failure);
      if (endsSession(error)) {
        await end('expired');
      } else if (error.code === 'NETWORK_UNREACHABLE') {
        // The request may have arrived. Checking resends the same key, so it can never apply twice.
        setState({ kind: 'unknown', action: current.action, error });
      } else {
        const maxAttempts = error.recovery.max_attempts ?? 3;
        setState({ kind: 'failed', action: current.action, error, canRetry: error.recovery.retryable === true && current.attempts < maxAttempts });
      }
    }
  }, [end, insightId, onConfirmed, queryClient, recentlyHidden, revision, setRecentlyHidden, workspace]);

  /** A new action gets a new key; repeating the pending action resends its key. */
  const give = useCallback(
    (action: FeedbackAction) => {
      if (intent.current?.action !== action) {
        intent.current = { action, key: randomToken(16), attempts: 0 };
      }
      return send();
    },
    [send],
  );

  return { state, give, retry: send };
}

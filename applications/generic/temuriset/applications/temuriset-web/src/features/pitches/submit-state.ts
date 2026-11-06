import { ApiError } from '@/api/errors';

/** Where one deliberate send stands. Only `sent`, `duplicate` and `stale` end the use of a key (FR-002). */
export type SubmitState =
  | { kind: 'idle' }
  | { kind: 'sending' }
  | { kind: 'sent'; pitchId: string }
  | { kind: 'lost' }
  | { kind: 'stale'; reason: string }
  | { kind: 'duplicate'; pitchId: string }
  | { kind: 'not_ready'; message: string; requirement: string | null }
  | { kind: 'failed'; message: string; requestId: string | null };

/** Turns a failed send into the state the screen shows. A response that never arrived is `lost`: retrying is safe. */
export function stateOf(error: unknown): SubmitState {
  const failure = ApiError.from(error);
  switch (failure.code) {
    case 'NETWORK_UNREACHABLE':
    case 'UNEXPECTED_RESPONSE':
    case 'INTERNAL_ERROR':
    case 'DATABASE_UNAVAILABLE':
      return { kind: 'lost' };
    case 'PREFLIGHT_STALE':
      return { kind: 'stale', reason: failure.field('reason') ?? failure.message };
    case 'DUPLICATE_PITCH':
      return { kind: 'duplicate', pitchId: failure.field('pitch_id') ?? '' };
    case 'NOT_READY':
      return { kind: 'not_ready', message: failure.message, requirement: failure.field('requirement') };
    default: {
      const reason = failure.field('reason');
      return { kind: 'failed', message: reason ? `${failure.message} ${reason}` : failure.message, requestId: failure.requestId };
    }
  }
}

/** Whether the next attempt must reuse the key: only after a lost response, so the service can replay it. */
export function keepsKey(state: SubmitState): boolean {
  return state.kind === 'lost' || state.kind === 'sending';
}

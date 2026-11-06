import { newIdempotencyKey, send } from '@/api/client';
import type { MatchRun, MatchSourceRef } from '@/features/discovery/model';

type Marked = 'saved-items' | 'discovery-feedback';

export function mark(kind: Marked, subjectType: string, subjectId: string, actingPartyId: string, on: boolean): Promise<unknown> {
  return send(on ? 'PUT' : 'DELETE', `/api/v1/${kind}/${subjectType}/${subjectId}`, { acting_party_id: actingPartyId });
}

export function runMatch(source: MatchSourceRef, actingPartyId: string, key: string = newIdempotencyKey()): Promise<MatchRun> {
  return send('POST', '/api/v1/matches', { acting_party_id: actingPartyId, source_type: source.type, source_id: source.id }, { idempotencyKey: key });
}

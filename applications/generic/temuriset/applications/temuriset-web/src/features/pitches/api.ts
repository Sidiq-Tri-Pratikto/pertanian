import { send } from '@/api/client';
import type { MatchSourceRef } from '@/features/discovery/model';
import type { Preflight } from '@/features/pitches/model';

export function runPreflight(source: MatchSourceRef, targetId: string, actingPartyId: string): Promise<Preflight> {
  return send('POST', '/api/v1/pitches/preflight', { acting_party_id: actingPartyId, source_type: source.type, source_id: source.id, opportunity_id: targetId });
}

export type SubmitBody = { acting_party_id: string; preflight_token: string; brief: string; files: { document_id: string; version: number }[] };

export function submitPitch(body: SubmitBody, key: string): Promise<{ pitch_id: string; status: string }> {
  return send('POST', '/api/v1/pitches', body, { idempotencyKey: key });
}

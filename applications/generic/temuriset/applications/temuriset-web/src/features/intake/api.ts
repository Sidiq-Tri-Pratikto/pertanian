import { send } from '@/api/client';
import { ApiError } from '@/api/errors';
import type { Mandate, PartnerProfile } from '@/features/intake/model';

export type MandateAction = 'activate' | 'pause' | 'close';

export function savePartnerProfile(partyId: string, body: unknown, key: string): Promise<PartnerProfile> {
  return send('PUT', `/api/v1/partners/${partyId}`, body, { idempotencyKey: key });
}

export function createMandate(actingPartyId: string, key: string): Promise<Mandate> {
  return send('POST', '/api/v1/opportunities', { acting_party_id: actingPartyId }, { idempotencyKey: key });
}

export function saveMandate(id: string, body: unknown, key: string): Promise<Mandate> {
  return send('PUT', `/api/v1/opportunities/${id}`, body, { idempotencyKey: key });
}

export function moveMandate(id: string, action: MandateAction, actingPartyId: string, version: number, key: string): Promise<Mandate> {
  return send('POST', `/api/v1/opportunities/${id}/${action}`, { acting_party_id: actingPartyId, expected_version: version }, { idempotencyKey: key });
}

export async function readMandate(id: string): Promise<Mandate> {
  let response: Response;
  try {
    response = await fetch(`/api/v1/opportunities/${id}`, { cache: 'no-store', signal: AbortSignal.timeout(10_000) });
  } catch {
    throw ApiError.unreachable();
  }
  if (!response.ok) throw ApiError.unexpected();
  return (await response.json()) as Mandate;
}

export function recordHandoff(partyId: string, actingPartyId: string, key: string): Promise<unknown> {
  return send('POST', `/api/v1/partners/${partyId}/handoffs`, { acting_party_id: actingPartyId }, { idempotencyKey: key });
}

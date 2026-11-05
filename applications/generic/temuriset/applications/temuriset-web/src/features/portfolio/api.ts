import { newIdempotencyKey, send } from '@/api/client';
import type { Invention } from '@/features/portfolio/model';

export async function createInvention(actingPartyId: string): Promise<Invention> {
  return send<Invention>('POST', '/api/v1/inventions', { acting_party_id: actingPartyId }, { idempotencyKey: newIdempotencyKey() });
}

export async function saveDraft(id: string, body: unknown, key: string): Promise<Invention> {
  return send<Invention>('PUT', `/api/v1/inventions/${id}/draft`, body, { idempotencyKey: key });
}

export async function publishInvention(id: string, actingPartyId: string, version: number, key: string): Promise<{ version: number; status: string }> {
  return send('POST', `/api/v1/inventions/${id}/publish`, { acting_party_id: actingPartyId, expected_version: version }, { idempotencyKey: key });
}

export async function readInvention(id: string): Promise<Invention> {
  const response = await fetch(`/api/v1/inventions/${id}`, { cache: 'no-store', signal: AbortSignal.timeout(10_000) });
  if (!response.ok) throw new Error('reload failed');
  return (await response.json()) as Invention;
}

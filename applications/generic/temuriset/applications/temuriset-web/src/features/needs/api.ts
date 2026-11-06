import { send } from '@/api/client';
import type { FundingRequest, LegalEntity, SupportRequest } from '@/features/needs/model';

export function createSupportRequest(actingPartyId: string, inventionId: string, key: string): Promise<SupportRequest> {
  return send('POST', '/api/v1/support-requests', { acting_party_id: actingPartyId, invention_id: inventionId }, { idempotencyKey: key });
}

export function saveSupportRequest(id: string, body: unknown, key: string): Promise<SupportRequest> {
  return send('PUT', `/api/v1/support-requests/${id}`, body, { idempotencyKey: key });
}

export function moveSupportRequest(id: string, action: 'activate' | 'pause' | 'close', actingPartyId: string, version: number, key: string): Promise<SupportRequest> {
  return send('POST', `/api/v1/support-requests/${id}/${action}`, { acting_party_id: actingPartyId, expected_version: version }, { idempotencyKey: key });
}

export function createFundingRequest(actingPartyId: string, key: string): Promise<FundingRequest> {
  return send('POST', '/api/v1/funding-requests', { acting_party_id: actingPartyId, subject_type: 'PROPOSED_ENTITY' }, { idempotencyKey: key });
}

export function saveFundingRequest(id: string, body: unknown, key: string): Promise<FundingRequest> {
  return send('PUT', `/api/v1/funding-requests/${id}`, body, { idempotencyKey: key });
}

export function declareEntity(actingPartyId: string, name: string, jurisdiction: string, registrationReference: string): Promise<LegalEntity> {
  return send('POST', '/api/v1/legal-entities', {
    acting_party_id: actingPartyId,
    name,
    jurisdiction,
    registration_reference: registrationReference,
  });
}

import type { Me } from '@/api/client';

export const PERSONAL = '00000000-0000-4000-8000-000000000001';
export const ORGANIZATION_PARTY = '00000000-0000-4000-8000-000000000002';
export const ORGANIZATION = '00000000-0000-4000-8000-000000000003';

const ALL = ['confirm_relationship', 'decide_pitch', 'edit_portfolio', 'manage_members', 'review_publication', 'schedule', 'submit_pitch'];

/** A signed-in account as `/me` returns it. */
export function makeMe(overrides: { persona?: 'inovator' | 'mitra'; organization?: boolean; actingAsOrganization?: boolean } = {}): Me {
  const organizations = overrides.organization
    ? [{ organization_id: ORGANIZATION, party_id: ORGANIZATION_PARTY, name: 'Demo Circular Materials Ltd', capabilities: ALL }]
    : [];
  return {
    account: {
      id: '00000000-0000-4000-8000-0000000000aa',
      display_name: 'Rani',
      email: 'rani@example.com',
      email_verified: true,
      locale: 'id',
      time_zone: 'Asia/Jakarta',
      persona: overrides.persona ?? 'inovator',
      kind: 'user',
      version: 1,
    },
    personal_party_id: PERSONAL,
    active_party_id: overrides.actingAsOrganization ? ORGANIZATION_PARTY : PERSONAL,
    capabilities: ALL,
    organizations,
  };
}

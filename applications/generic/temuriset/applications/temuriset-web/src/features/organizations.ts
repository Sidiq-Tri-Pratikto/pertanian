import type { components } from '@/api/schema.generated';

export type Member = components['schemas']['MemberResponse'];
export type Invitation = components['schemas']['InvitationResponse'];
export type InvitationDetail = components['schemas']['InvitationDetailResponse'];

/** What each capability lets a member do, in the handoff's words. */
export const CAPABILITY_LABEL: Record<string, string> = {
  edit_portfolio: 'Mengubah portofolio',
  submit_pitch: 'Mengirim pitching',
  review_publication: 'Meninjau publikasi',
  decide_pitch: 'Memutuskan pitching',
  confirm_relationship: 'Mengonfirmasi kerja sama',
  schedule: 'Mengatur jadwal',
  manage_members: 'Mengelola anggota',
};

export const ORGANIZATION_KINDS = [
  { value: 'company', label: 'Perusahaan' },
  { value: 'nonprofit', label: 'Organisasi nirlaba' },
  { value: 'community', label: 'Komunitas' },
  { value: 'research_group', label: 'Kelompok riset' },
  { value: 'other', label: 'Lainnya' },
];

export const INVITATION_STATUS: Record<string, string> = {
  pending: 'Menunggu',
  accepted: 'Diterima',
  revoked: 'Dicabut',
  expired: 'Kedaluwarsa',
};

export function capabilityList(capabilities: string[]): string {
  return capabilities.map((capability) => CAPABILITY_LABEL[capability] ?? capability).join(', ');
}

/** A date in the account's own time zone. */
export function formatDateTime(value: string, timeZone: string): string {
  return new Intl.DateTimeFormat('id-ID', { dateStyle: 'medium', timeStyle: 'short', timeZone }).format(new Date(value));
}

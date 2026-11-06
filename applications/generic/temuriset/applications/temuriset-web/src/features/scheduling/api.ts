import { send } from '@/api/client';
import type { components } from '@/api/schema.generated';

export type Schedule = components['schemas']['ScheduleResponse'];
export type Proposal = components['schemas']['ProposalResponse'];
export type Meeting = components['schemas']['MeetingResponse'];

export type ProposeBody = {
  acting_party_id: string;
  slots: string[];
  minutes: 30 | 60;
  time_zone: string;
  agenda: string;
  link: string | null;
  replaces_meeting_id: string | null;
};

export function proposeSlots(pitchId: string, body: ProposeBody, key: string): Promise<Proposal> {
  return send('POST', `/api/v1/pitches/${pitchId}/schedule-proposals`, body, { idempotencyKey: key });
}

export function acceptSlot(proposal: Proposal, slotId: string, actingPartyId: string, key: string): Promise<Meeting> {
  return send('POST', `/api/v1/schedule-proposals/${proposal.id}/accept`, { acting_party_id: actingPartyId, slot_id: slotId, expected_version: proposal.version }, { idempotencyKey: key });
}

export function cancelMeeting(meeting: Meeting, actingPartyId: string, key: string): Promise<Meeting> {
  return send('POST', `/api/v1/meetings/${meeting.id}/cancel`, { acting_party_id: actingPartyId, expected_version: meeting.version }, { idempotencyKey: key });
}

export function recordOutcome(meeting: Meeting, actingPartyId: string, result: 'COMPLETED' | 'NO_SHOW', key: string): Promise<Meeting> {
  return send('POST', `/api/v1/meetings/${meeting.id}/outcome`, { acting_party_id: actingPartyId, result }, { idempotencyKey: key });
}

export const EXPIRED_REASON: Record<string, string> = {
  AGE: 'Usulan kedaluwarsa setelah 72 jam tanpa konfirmasi.',
  ALL_PAST: 'Semua waktu yang diusulkan sudah lewat.',
};

export const calendarHref = (meeting: Meeting) => `/api/v1/meetings/${meeting.id}/calendar.ics`;

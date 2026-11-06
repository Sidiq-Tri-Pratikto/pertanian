import { send } from '@/api/client';
import type { components } from '@/api/schema.generated';
import type { Pitch, PitchSummary } from '@/features/pitches/model';

export type RevisionRound = components['schemas']['RevisionRoundResponse'];
export type RevisionItemView = components['schemas']['RevisionItemResponse'];
export type Answer = components['schemas']['AnswerResponse'];
export type ChosenFile = { document_id: string; version: number };
type Moved = components['schemas']['PitchActionResponse'];
export type NextAction = components['schemas']['NextAction'];

export const TABS = [
  { id: 'ringkasan', label: 'Ringkasan' },
  { id: 'revisi', label: 'Revisi' },
  { id: 'dokumen', label: 'Dokumen' },
  { id: 'diskusi', label: 'Diskusi' },
  { id: 'jadwal', label: 'Jadwal' },
  { id: 'riwayat', label: 'Riwayat' },
] as const;
export type TabId = (typeof TABS)[number]['id'];

export function tabOf(value: string | undefined): TabId {
  return TABS.find((tab) => tab.id === value)?.id ?? 'ringkasan';
}

/** Whose turn it is, from the API's projection; the client never re-derives it from the status (FR-002). */
export function turnOf(pitch: Pick<PitchSummary, 'waiting_on_party_id'>, activePartyId: string): 'you' | 'other' | null {
  if (!pitch.waiting_on_party_id) return null;
  return pitch.waiting_on_party_id === activePartyId ? 'you' : 'other';
}

export const TURN_LABEL = { you: 'Menunggu Anda', other: 'Menunggu pihak lain' } as const;

export type ListFilters = { status?: string; giliran?: string };

/** Filters live in the address, so Back from a pitch restores them (UX-12). */
export function filterPitches(pitches: PitchSummary[], filters: ListFilters, activePartyId: string): PitchSummary[] {
  return pitches.filter((pitch) => {
    if (filters.status && pitch.status !== filters.status) return false;
    if (filters.giliran === 'anda' && turnOf(pitch, activePartyId) !== 'you') return false;
    if (filters.giliran === 'lain' && turnOf(pitch, activePartyId) !== 'other') return false;
    return true;
  });
}

function base(pitch: Pitch, actingPartyId: string) {
  return { acting_party_id: actingPartyId, expected_version: pitch.version };
}

export function moveTo(pitch: Pitch, actingPartyId: string, action: 'begin-review' | 'withdraw', key: string): Promise<Moved> {
  return send('POST', `/api/v1/pitches/${pitch.id}/${action}`, base(pitch, actingPartyId), { idempotencyKey: key });
}

export function closeDiscussion(pitch: Pitch, actingPartyId: string, reason: string, key: string): Promise<Moved> {
  return send('POST', `/api/v1/pitches/${pitch.id}/close`, { ...base(pitch, actingPartyId), reason }, { idempotencyKey: key });
}

export function decide(pitch: Pitch, actingPartyId: string, decision: 'APPROVE' | 'REJECT', reason: string | null, key: string): Promise<Moved> {
  const submission = pitch.submissions[pitch.submissions.length - 1]?.number ?? 1;
  return send('POST', `/api/v1/pitches/${pitch.id}/decisions`, { ...base(pitch, actingPartyId), submission, decision, reason }, { idempotencyKey: key });
}

export type ItemDraft = { category: string; question: string; reason: string; required: boolean; due_date: string | null; expected_evidence: string };

export function requestRevision(pitch: Pitch, actingPartyId: string, items: ItemDraft[], key: string): Promise<Moved> {
  const submission = pitch.submissions[pitch.submissions.length - 1]?.number ?? 1;
  return send('POST', `/api/v1/pitches/${pitch.id}/revision-rounds`, { ...base(pitch, actingPartyId), submission, items }, { idempotencyKey: key });
}

export function saveAnswer(
  pitchId: string,
  itemId: string,
  body: { acting_party_id: string; expected_version: number | null; response: string; text: string; files: ChosenFile[] },
): Promise<Answer> {
  return send('PUT', `/api/v1/pitches/${pitchId}/revision-items/${itemId}/answer`, body);
}

export function reviewItem(pitchId: string, item: RevisionItemView, actingPartyId: string, result: 'ACCEPTED' | 'NEEDS_DETAIL'): Promise<unknown> {
  return send('PUT', `/api/v1/pitches/${pitchId}/revision-items/${item.id}/review`, { acting_party_id: actingPartyId, expected_version: item.version, result });
}

export function resubmit(pitch: Pitch, actingPartyId: string, files: ChosenFile[], key: string): Promise<Moved> {
  return send('POST', `/api/v1/pitches/${pitch.id}/resubmit`, { ...base(pitch, actingPartyId), files }, { idempotencyKey: key });
}

export const ITEM_REVIEW: Record<string, string> = { ACCEPTED: 'Diterima', NEEDS_DETAIL: 'Perlu detail' };
export const RESPONSE_LABEL: Record<string, string> = { CAN: 'Dapat dipenuhi', DISCUSS: 'Perlu diskusi', CANNOT: 'Belum dapat dipenuhi' };

import type { components } from '@/api/schema.generated';

export type Preflight = components['schemas']['PreflightResponse'];
export type ShareableFile = components['schemas']['ShareableFile'];
export type PitchSummary = components['schemas']['PitchSummary'];
export type Pitch = components['schemas']['PitchResponse'];

export const PITCH_STATUS: Record<string, string> = {
  DRAFT: 'Draf',
  PENDING_WORKSPACE_REVIEW: 'Menunggu tinjauan organisasi',
  SUBMITTED: 'Terkirim',
  UNDER_REVIEW: 'Sedang ditinjau',
  REVISION_REQUESTED: 'Perlu revisi',
  APPROVED_FOR_DISCUSSION: 'Disetujui untuk diskusi',
  REJECTED: 'Ditolak',
  WITHDRAWN: 'Ditarik',
  CLOSED: 'Ditutup',
};

export const SOURCE_KIND: Record<string, string> = {
  SUPPORT_REQUEST: 'Dukungan Proyek',
  FUNDING_REQUEST: 'Pendanaan Perusahaan',
};

/** Requirements that need a chosen file at submission, by the fact key a file must carry. */
export function requiredFiles(preflight: Preflight): { label: string; key: string }[] {
  return preflight.rows
    .filter((row) => row.mandatory && row.applies_at === 'SUBMISSION' && row.verification_mode === 'DOCUMENT_PRESENT' && row.field.startsWith('document:'))
    .map((row) => ({ label: row.label, key: row.field.slice('document:'.length) }));
}

/** The required files the chosen ones do not cover. */
export function missingFiles(preflight: Preflight, chosen: string[]): { label: string; key: string }[] {
  const keys = new Set(preflight.shareable_files.filter((file) => chosen.includes(file.version_id)).flatMap((file) => file.fact_keys));
  return requiredFiles(preflight).filter((required) => !keys.has(required.key));
}

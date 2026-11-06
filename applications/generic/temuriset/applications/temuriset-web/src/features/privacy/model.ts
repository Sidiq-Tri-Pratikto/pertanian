import type { Recovery } from '@/api/errors';
import type { components } from '@/api/schema.generated';

type Schemas = components['schemas'];
export type Report = Schemas['ReportResponse'];
export type ReportInput = Schemas['CreateReportRequest'];
export type ReportCategory = NonNullable<ReportInput['category']>;
export type SubjectType = NonNullable<ReportInput['subject_type']>;
export type PrivacyRequest = Schemas['PrivacyRequestResponse'];
export type PrivacyInput = Schemas['CreatePrivacyRequest'];

export type ReportSubject = { type: SubjectType; id: string };
export type ActingScope = { id: string; label: string };
export type PrivacyFailure = { message: string; requestId: string | null; code: string; recovery: Recovery };
export type SectionData<Item> = { data: Item[]; failure: PrivacyFailure | null };

export const REPORT_CATEGORIES: Record<ReportCategory, string> = {
  IMPERSONATION: 'Penyamaran',
  UNSUPPORTED_CLAIM: 'Klaim tanpa bukti',
  UNWANTED_CONTACT: 'Kontak yang tidak diinginkan',
  ABUSE: 'Penyalahgunaan',
  OTHER: 'Lainnya',
};

export const REPORT_STATUS: Record<Report['status'], string> = {
  RECEIVED: 'Diterima',
  IN_REVIEW: 'Sedang ditinjau',
  RESOLVED: 'Selesai ditangani',
  DISMISSED: 'Ditutup',
};

export const PRIVACY_STATUS: Record<PrivacyRequest['status'], string> = {
  RECEIVED: 'Diterima',
  PROCESSING: 'Sedang diproses',
  FULFILLED: 'Selesai',
};

export const SUBJECT_LABELS: Record<SubjectType, string> = {
  INVENTION: 'Inovasi',
  OPPORTUNITY: 'Mandat',
  PARTNER_PROFILE: 'Profil mitra',
  FUNDING_REQUEST: 'Permintaan pendanaan',
  SUPPORT_REQUEST: 'Permintaan dukungan',
  PITCH: 'Pitch',
  MESSAGE: 'Pesan',
  OTHER: 'Lainnya',
};

const UUID = /^[\da-f]{8}(?:-[\da-f]{4}){3}-[\da-f]{12}$/i;

export function readReportSubject(type: string | string[] | undefined, id: string | string[] | undefined): ReportSubject | null {
  if (typeof type !== 'string' || !Object.hasOwn(SUBJECT_LABELS, type) || typeof id !== 'string' || !UUID.test(id)) {
    return null;
  }
  return { type: type as SubjectType, id };
}

export function reportHref(type: SubjectType, id: string): string {
  if (!UUID.test(id)) return '/settings#laporkan';
  return `/settings?${new URLSearchParams({ lapor: type, objek: id })}#laporkan`;
}

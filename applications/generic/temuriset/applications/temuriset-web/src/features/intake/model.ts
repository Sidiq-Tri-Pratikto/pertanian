import type { components } from '@/api/schema.generated';
import type { FinancialSubject } from '@/components/tr/FinancialScope';
import { BASES } from '@/features/needs/model';

export type PartnerProfile = components['schemas']['PartnerProfileResponse'];
export type Mandate = components['schemas']['OpportunityResponse'];
export type Requirement = components['schemas']['RequirementResponse'];
export type Financial = components['schemas']['FinancialResponse'];
export type StoredRange = components['schemas']['RangeResponse'];

export const MANDATE_STATUS: Record<string, string> = {
  DRAFT: 'Draf',
  ACTIVE: 'Aktif',
  PAUSED: 'Dijeda',
  CLOSED: 'Ditutup',
  EXPIRED: 'Berakhir',
};

export const AVAILABILITY_REASON: Record<string, string> = {
  SUSPENDED: 'Penerimaan untuk mandat ini ditangguhkan sementara.',
  TARGET_NOT_ACTIVE: 'Mandat ini sedang tidak menerima pitching.',
  EXTERNAL_ROUTE: 'Mitra ini menerima lewat formulirnya sendiri.',
  NO_NEW_APPROACHES: 'Mitra ini sedang tidak menerima pendekatan baru.',
  DIRECT_INTAKE_CLOSED: 'Penerimaan umum mitra ini ditutup.',
  INTAKE_UNCONFIRMED: 'Ketersediaan mitra ini belum dikonfirmasi.',
};

export const RELATIONSHIP_FORMS = [
  { value: 'PROJECT', label: 'Proyek' },
  { value: 'LICENSE', label: 'Lisensi' },
  { value: 'EQUITY', label: 'Ekuitas' },
];

export const FINANCIAL_SUBJECTS = [
  { value: 'partner', label: 'Dukungan mitra' },
  { value: 'investorCheck', label: 'Investasi investor' },
  { value: 'license', label: 'Ketentuan lisensi' },
];

export const FINANCIAL_BASES = [...BASES, { value: 'per_investment', label: 'Per investasi' }];
export const PER_INVESTMENT_PERIOD = 'per investasi';

export const CONTACT_ROUTES = [
  { value: 'IN_APP', label: 'Pitching lewat TemuRiset' },
  { value: 'EXTERNAL', label: 'Formulir di situs lain' },
  { value: 'NONE', label: 'Tidak menerima pendekatan baru' },
];

export const INTAKE_CHOICES = [
  { value: 'OPEN', label: 'Pitching dibuka' },
  { value: 'CLOSED', label: 'Penerimaan ditutup' },
];

export const APPLIES_AT = [
  { value: 'SUBMISSION', label: 'Saat pengajuan' },
  { value: 'DISCUSSION', label: 'Saat diskusi' },
  { value: 'PILOT', label: 'Saat pilot' },
  { value: 'COMMERCIALIZATION', label: 'Saat komersialisasi' },
];

export const VERIFICATION_MODES = [
  { value: 'DECLARATION', label: 'Pernyataan' },
  { value: 'DOCUMENT_PRESENT', label: 'Dokumen tersedia' },
  { value: 'REVIEWER_CONFIRMED', label: 'Diperiksa peninjau' },
];

export const REQUIREMENT_KINDS = [
  { value: 'narrative', label: 'Naratif, ditinjau manual' },
  { value: 'stage', label: 'Tahap inovasi' },
  { value: 'relationship', label: 'Bentuk kerja sama' },
  { value: 'document', label: 'Berkas tersedia' },
  { value: 'feature', label: 'Fitur yang sudah berjalan' },
  { value: 'budget', label: 'Kisaran biaya sebanding' },
  { value: 'contribution', label: 'Kisaran kontribusi sebanding' },
  { value: 'authority', label: 'Wewenang sudah diperiksa' },
  { value: 'entity', label: 'Badan usaha sudah berdiri' },
];

export const DOCUMENT_KINDS = [
  { value: 'function', label: 'Bukti fungsi' },
  { value: 'certificate', label: 'Sertifikat' },
];

/** Comma-separated text as the list the service stores. */
export function splitList(text: string): string[] {
  return text
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

/** Stored money comes back as "20000.0000"; a field shows the digits a person would type. */
export function plainAmount(value: string | null | undefined): string {
  return value ? value.replace(/\.?0+$/, '') : '';
}

/** What `FinancialScope` needs from a stored range or financial basis. */
export function scopeProps(range: (StoredRange | Financial) & { scope?: string; noncash?: string; terms?: string }) {
  const perInvestment = range.basis === 'per_investment';
  return {
    subject: range.subject as FinancialSubject,
    currency: range.currency,
    min: range.min,
    max: range.max,
    // "selama per investasi" would read wrong: a check has a basis, not a duration.
    period: perInvestment ? undefined : range.period || undefined,
    label: perInvestment ? 'Kisaran investasi investor, per investasi' : undefined,
    scope: range.scope || undefined,
    noncash: range.noncash || undefined,
    terms: range.terms || undefined,
  };
}

export type RangeValues = {
  subject: string;
  min: string;
  max: string;
  currency: string;
  basis: string;
  period: string;
  months: string;
  unknown_reason: string;
};

export function rangeValues(range: StoredRange | Financial | null | undefined, subject: string): RangeValues {
  return {
    subject: range?.subject ?? subject,
    min: plainAmount(range?.min),
    max: plainAmount(range?.max),
    currency: range?.currency ?? '',
    basis: range?.basis ?? 'total_period',
    period: range?.period ?? '',
    months: range?.months == null ? '' : String(range.months),
    unknown_reason: range?.unknown_reason ?? '',
  };
}

/** The range as the service reads it. The service decides what is valid; this only shapes what was typed. */
export function rangeBody(values: RangeValues) {
  const hasAmounts = Boolean(values.min.trim() || values.max.trim());
  const perInvestment = values.basis === 'per_investment';
  return {
    subject: values.subject,
    min: values.min.trim() || null,
    max: values.max.trim() || null,
    currency: hasAmounts ? values.currency || null : null,
    basis: hasAmounts ? values.basis || null : null,
    period: hasAmounts ? values.period.trim() || (perInvestment ? PER_INVESTMENT_PERIOD : '') : '',
    months: hasAmounts && /^\d+$/.test(values.months.trim()) ? Number(values.months.trim()) : null,
    unknown_reason: hasAmounts ? null : values.unknown_reason || null,
  };
}

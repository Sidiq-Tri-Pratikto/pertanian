import type { components } from '@/api/schema.generated';
import type { ApiError } from '@/api/errors';

export type SupportRequest = components['schemas']['SupportRequestResponse'];
export type Budget = components['schemas']['BudgetResponse'];
export type FundingRequest = components['schemas']['FundingRequestResponse'];
export type LegalEntity = components['schemas']['LegalEntityResponse'];

export const SUPPORT_FORMS = [
  { value: 'project_funding', label: 'Pendanaan proyek' },
  { value: 'testing_support', label: 'Dukungan pengujian' },
  { value: 'mentoring', label: 'Pendampingan' },
  { value: 'facilities', label: 'Fasilitas' },
  { value: 'distribution', label: 'Distribusi' },
  { value: 'technical_partner', label: 'Mitra teknis' },
  { value: 'other', label: 'Lainnya' },
] as const;

export const CURRENCIES = [
  { value: 'IDR', label: 'IDR (Rupiah)' },
  { value: 'USD', label: 'USD (Dolar AS)' },
];

export const BASES = [
  { value: 'total_period', label: 'Total untuk seluruh periode' },
  { value: 'monthly', label: 'Per bulan' },
  { value: 'yearly', label: 'Per tahun' },
];

export const UNKNOWN_REASONS = [
  { value: 'not_determined', label: 'Belum ditentukan' },
  { value: 'not_disclosed', label: 'Tidak diungkapkan' },
];

export const FINANCING_STAGES = [
  { value: 'pre_seed', label: 'Pre-seed' },
  { value: 'seed', label: 'Seed' },
  { value: 'series_a', label: 'Seri A' },
  { value: 'series_b_plus', label: 'Seri B atau lanjutan' },
  { value: 'bridge', label: 'Pendanaan jembatan' },
];

export const FINANCING_FORMS = [
  { value: 'equity', label: 'Ekuitas' },
  { value: 'convertible_note', label: 'Surat utang konversi' },
  { value: 'safe', label: 'SAFE' },
  { value: 'debt', label: 'Pinjaman' },
  { value: 'revenue_based', label: 'Bagi hasil pendapatan' },
];

export const NEED_STATUS: Record<string, string> = {
  DRAFT: 'Draf',
  ACTIVE: 'Aktif',
  PAUSED: 'Dijeda',
  CLOSED: 'Ditutup',
  EXPIRED: 'Kedaluwarsa',
};

/** A financial need whose range is still open: Beranda asks for it, and nothing treats it as zero. */
export function needsRange(request: SupportRequest): boolean {
  if (request.status === 'CLOSED' || request.status === 'EXPIRED') return false;
  const budget = request.budget;
  return !budget || (budget.financial && budget.min == null && budget.max == null);
}

/** Field errors keyed by form field id, from the service's `details` locations. */
export function fieldErrors(error: ApiError, ids: Record<string, string>): Record<string, string> {
  const found: Record<string, string> = {};
  for (const detail of error.details) {
    const key = detail.loc.filter((part) => part !== 'body').join('.');
    const id = ids[key] ?? ids[key.split('.').slice(0, 2).join('.')];
    if (id && !found[id]) found[id] = detail.msg;
  }
  return found;
}

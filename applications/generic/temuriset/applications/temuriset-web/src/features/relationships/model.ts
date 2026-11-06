import type { components } from '@/api/schema.generated';
import { range } from '@/features/money';

type Schemas = components['schemas'];
export type Partnership = Schemas['PartnershipResponse'];
export type Proposal = Schemas['ProposePartnershipRequest'];
export type PartnershipKind = Proposal['type'];
export type PublicField = Proposal['ceiling'][number];
export type Values = Schemas['PartnershipValues'];
export type Profile = Schemas['PublicProfileResponse'];
export type ProfileSettings = Schemas['ProfileResponse'];
export type ProposalOptions = Schemas['ProposalOptionsResponse'];

export const TYPE_LABEL: Record<PartnershipKind, string> = {
  PROJECT: 'Kerja Sama proyek',
  LICENSE: 'Lisensi',
  EQUITY: 'Ekuitas',
};
export const FIELD_LABEL: Record<PublicField, string> = {
  name: 'Nama Kerja Sama',
  type: 'Jenis Kerja Sama',
  scope: 'Cakupan',
  date: 'Tanggal mulai',
  amount: 'Jumlah dana',
  percent: 'Persentase saham',
};
export const FIELDS = Object.keys(FIELD_LABEL) as PublicField[];

export function text(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

export function valuesOf(values: Record<string, unknown>): Values {
  return {
    name: text(values.name), scope: text(values.scope), start_date: text(values.start_date),
    amount: text(values.amount) || null, currency: text(values.currency) || null,
    percent: text(values.percent) || null, percent_date: text(values.percent_date) || null,
    evidence: text(values.evidence),
  };
}

export function toggleField(fields: PublicField[], field: PublicField, selected: boolean): PublicField[] {
  return selected ? [...fields, field] : fields.filter((item) => item !== field);
}

export function validId(value: string): boolean {
  return /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(value);
}

function fieldValue(field: PublicField, value: unknown): string {
  if (typeof value === 'string') return value;
  if (!value || typeof value !== 'object') return '';
  if (field === 'amount' && 'amount' in value && 'currency' in value && typeof value.amount === 'string') {
    return range(text(value.currency), value.amount, value.amount);
  }
  if (field === 'percent' && 'percent' in value && 'effective_date' in value && typeof value.percent === 'string') {
    return [`${value.percent}%`, text(value.effective_date)].filter(Boolean).join(' · ');
  }
  return '';
}

/** Display only values the API included in the public projection. */
export function publicRows(values: Record<string, unknown>) {
  return FIELDS.flatMap((id) => {
    const value = fieldValue(id, values[id]);
    return value ? [{ id, label: FIELD_LABEL[id], value }] : [];
  });
}

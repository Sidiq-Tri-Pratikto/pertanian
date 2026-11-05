import type { components } from '@/api/schema.generated';

export type Invention = components['schemas']['InventionResponse'];
export type InventionSummary = components['schemas']['InventionSummaryResponse'];
export type InventionVersion = components['schemas']['InventionVersionResponse'];
export type PublicInvention = components['schemas']['PublicInventionResponse'];
export type Fact = components['schemas']['FactInput'];
export type Claim = components['schemas']['ClaimInput'];

export const STAGES = [
  { value: 'IDEA', label: 'Ide' },
  { value: 'PROTOTYPE', label: 'Prototipe' },
  { value: 'PILOT', label: 'Pilot' },
  { value: 'WORKING', label: 'Sudah berfungsi' },
  { value: 'MARKET', label: 'Sudah di pasar' },
];

export const TIMINGS = [
  { value: 'CURRENT', label: 'Saat ini' },
  { value: 'PLANNED', label: 'Direncanakan' },
  { value: 'REQUESTED', label: 'Diminta' },
];

export const PROVENANCES = [
  { value: 'SELF_DECLARED', label: 'Dinyatakan sendiri' },
  { value: 'SOURCE_REPORTED', label: 'Dilaporkan sumber' },
  { value: 'PROVIDED', label: 'Disediakan, belum diperiksa' },
  { value: 'UNKNOWN', label: 'Belum diketahui' },
];

export const CLAIM_KINDS = [
  { value: 'creator', label: 'Pencipta' },
  { value: 'contributor', label: 'Kontributor' },
  { value: 'manager', label: 'Pengelola' },
  { value: 'rights_holder', label: 'Pemegang hak (diklaim)' },
  { value: 'authority', label: 'Kewenangan bertindak' },
];

export const CLAIM_STATUSES = [
  { value: 'asserted', label: 'Dinyatakan' },
  { value: 'not_established', label: 'Belum ditetapkan' },
];

export function labelOf(options: { value: string; label: string }[], value: string | null | undefined): string {
  return options.find((option) => option.value === value)?.label ?? '';
}

export const STATUS_LABEL: Record<string, string> = {
  DRAFT: 'Draf',
  PENDING_REVIEW: 'Menunggu tinjauan',
  PUBLISHED: 'Terbit',
  ARCHIVED: 'Diarsipkan',
};

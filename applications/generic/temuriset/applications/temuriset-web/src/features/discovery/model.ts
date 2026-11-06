import type { components } from '@/api/schema.generated';
import type { Persona } from '@/features/persona';

export type Discovery = components['schemas']['DiscoveryResponse'];
export type DiscoveryItem = components['schemas']['DiscoveryItem'];
export type MatchRun = components['schemas']['MatchRunResponse'];
export type MatchResult = components['schemas']['MatchResultResponse'];
export type ResultType = Discovery['type'];

export const RESULT_TYPES: { value: ResultType; label: string; capability?: string }[] = [
  { value: 'inventions', label: 'Inovasi' },
  { value: 'funding', label: 'Pendanaan Perusahaan', capability: 'company_funding' },
  { value: 'partners', label: 'Investor dan Mitra' },
];

/** Partners start with inventions; inventors start with partners. */
export function defaultType(persona: Persona): ResultType {
  return persona === 'mitra' ? 'inventions' : 'partners';
}

export function readType(value: string | undefined, persona: Persona): ResultType {
  return RESULT_TYPES.some((item) => item.value === value) ? (value as ResultType) : defaultType(persona);
}

/** Filters that live in the address, so Back returns to the same search. */
export const FILTER_NAMES = ['q', 'sector', 'stage', 'saved'] as const;
export type Filters = Partial<Record<(typeof FILTER_NAMES)[number], string>>;

export function readFilters(params: Record<string, string | string[] | undefined>): Filters {
  const filters: Filters = {};
  for (const name of FILTER_NAMES) {
    const value = params[name];
    const text = Array.isArray(value) ? value[0] : value;
    if (text) filters[name] = text;
  }
  return filters;
}

export function discoverHref(type: ResultType, filters: Filters = {}): string {
  const query = new URLSearchParams({ type });
  for (const [name, value] of Object.entries(filters)) if (value) query.set(name, value);
  return `/discover?${query.toString()}`;
}

export const SECTORS = ['Air dan sanitasi', 'Pertanian', 'Perangkat lunak', 'Material', 'Manufaktur', 'Energi'];

export const ELIGIBILITY: Record<MatchResult['eligibility'], string> = {
  ELIGIBLE: 'Memenuhi syarat masuk',
  NEEDS_VERIFICATION: 'Perlu verifikasi',
  INCOMPATIBLE: 'Tidak memenuhi syarat',
};

export const READINESS: Record<MatchResult['readiness'], string> = {
  READY_TO_SUBMIT: 'Siap dikirim',
  NEEDS_INFORMATION: 'Perlu informasi',
  BLOCKED_FOR_THIS_TARGET: 'Terhalang untuk target ini',
};

/** Indonesian decimal comma for a score such as "88.11". */
export function score(value: string): string {
  return value.replace('.', ',');
}

export function percent(coverage: string): string {
  return `${Math.round(Number(coverage) * 100)}%`;
}

/** A source in the address: `SUPPORT_REQUEST:<id>` or `FUNDING_REQUEST:<id>`. */
export type MatchSourceRef = { type: 'SUPPORT_REQUEST' | 'FUNDING_REQUEST'; id: string };

export function readSource(value: string | undefined): MatchSourceRef | null {
  const [type, id] = (value ?? '').split(':');
  if ((type !== 'SUPPORT_REQUEST' && type !== 'FUNDING_REQUEST') || !/^[0-9a-f-]{36}$/.test(id ?? '')) return null;
  return { type, id };
}

export function matchesHref(source: MatchSourceRef): string {
  return `/matches?source=${source.type}:${source.id}`;
}

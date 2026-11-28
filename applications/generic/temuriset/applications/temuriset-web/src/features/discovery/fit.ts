import { getResponse } from '@/api/client';
import { DIMENSION_META, type Dimension } from '@/features/discovery/breakdown';
import { discoverHref, type Filters, type MatchResult } from '@/features/discovery/model';
import { recommendationAction, type Recommendation } from '@/features/discovery/recommendations';
import { t } from '@/features/i18n/t';

export type MyProduct = { id: string; title: string };

export type FitInvention = {
  id: string;
  title: string;
  stage: string | null;
  tkt_level: number | null;
};

export type FitOpportunity = {
  id: string;
  title: string;
  partner_party_id: string;
  partner: string;
};

export type FitSource = {
  type: 'SUPPORT_REQUEST' | 'FUNDING_REQUEST';
  id: string;
  version: number;
  title: string;
};

export type FitItem = {
  invention: FitInvention;
  source: FitSource | null;
  opportunity: FitOpportunity;
  result: MatchResult & { breakdown?: Dimension[]; recommendations?: Recommendation[] };
  preview: boolean;
};

export type PartnerBestFit = {
  label: string;
  eligibility: 'ELIGIBLE' | 'NEEDS_VERIFICATION' | 'INCOMPATIBLE';
  fit: { lower: string; upper: string; coverage: string };
  invention_id: string;
  invention_title: string;
  opportunity_id: string;
  preview?: boolean;
  matching_products?: number;
};

export function finderHref(filters: Filters = {}, produk?: string, selected?: string): string {
  const base = discoverHref('partners', filters, selected);
  if (!produk) return base;
  return `${base}&produk=${encodeURIComponent(produk)}`;
}

export async function fetchPartnerFit(partnerPartyId: string, actingPartyId: string, inventionId?: string): Promise<FitItem[]> {
  const query = new URLSearchParams({ acting_party_id: actingPartyId, partner_party_id: partnerPartyId });
  if (inventionId) query.set('invention_id', inventionId);
  const response = await getResponse(`/api/v1/fit?${query.toString()}`);
  return (await response.json()) as FitItem[];
}

/** Sorts fit rows: compatible & ready first, then lower bound desc, coverage desc, incompatible last. */
export function sortFitItems(items: FitItem[]): FitItem[] {
  return [...items].sort((a, b) => {
    const aIncompat = a.result.eligibility === 'INCOMPATIBLE' ? 1 : 0;
    const bIncompat = b.result.eligibility === 'INCOMPATIBLE' ? 1 : 0;
    if (aIncompat !== bIncompat) return aIncompat - bIncompat;
    const aReady = a.result.readiness === 'READY_TO_SUBMIT' && !a.preview ? 0 : 1;
    const bReady = b.result.readiness === 'READY_TO_SUBMIT' && !b.preview ? 0 : 1;
    if (aReady !== bReady) return aReady - bReady;
    const lowerDiff = Number(b.result.fit.lower) - Number(a.result.fit.lower);
    if (lowerDiff !== 0) return lowerDiff;
    const covDiff = Number(b.result.fit.coverage) - Number(a.result.fit.coverage);
    if (covDiff !== 0) return covDiff;
    return a.invention.title.localeCompare(b.invention.title);
  });
}

/** Picks up to two scored dimensions to summarize a row before expansion. */
export function topDimensions(breakdown: Dimension[], count = 2): { id: Dimension['id']; label: string; score: number }[] {
  return breakdown
    .filter((dim): dim is Dimension & { score: number } => dim.score !== null)
    .sort((a, b) => b.score - a.score)
    .slice(0, count)
    .map((dim) => ({ id: dim.id, label: DIMENSION_META[dim.id].label, score: dim.score }));
}

export type RowAction = { href: string; label: string; primary: boolean };

/** Primary action for one product × mandate row (spec 059 story 1.2). */
export function fitRowAction(item: FitItem, returnTo: string): RowAction {
  if (item.preview || !item.source) {
    return {
      href: `/support-requests?invention=${encodeURIComponent(item.invention.id)}&return=${encodeURIComponent(returnTo)}#baru`,
      label: t('Buat kebutuhan untuk produk ini'),
      primary: false,
    };
  }
  if (item.result.readiness === 'READY_TO_SUBMIT' && item.result.availability.available) {
    return {
      href: `/pitches/new?source=${item.source.type}:${item.source.id}&target=${item.opportunity.id}`,
      label: t('Siapkan pitching'),
      primary: true,
    };
  }
  const recs = item.result.recommendations ?? [];
  for (const rec of recs) {
    const act = recommendationAction(rec, returnTo);
    if (act) return { href: act.href, label: act.label, primary: false };
  }
  return {
    href: `/partners/${item.opportunity.partner_party_id}`,
    label: t('Lihat mandat'),
    primary: false,
  };
}

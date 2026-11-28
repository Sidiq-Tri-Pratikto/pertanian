import { serverGet } from '@/api/server';
import type { FitItem, MyProduct } from '@/features/discovery/fit';
import { matchesHref, readFilters, readType, type Discovery } from '@/features/discovery/model';
import type { FundingRequest, SupportRequest } from '@/features/needs/model';
import { fundingOn } from '@/features/needs/server';
import type { InventionSummary } from '@/features/portfolio/model';
import { personaOf, requireMe } from '@/features/session';
import { DiscoverView } from '@/views/discovery/DiscoverView';
import { titled } from '@/features/i18n/server';

export const generateMetadata = titled('Temukan dan jelajahi');

type Props = { searchParams: Promise<Record<string, string | string[] | undefined>> };

/** The first need or raise to match, for an inventor's shortcut to S10. */
async function firstSource(): Promise<string | null> {
  const [support, funding] = await Promise.all([
    serverGet<SupportRequest[]>('/api/v1/support-requests'),
    serverGet<FundingRequest[]>('/api/v1/funding-requests'),
  ]);
  const need = support.find((item) => item.status === 'ACTIVE');
  if (need) return matchesHref({ type: 'SUPPORT_REQUEST', id: need.id });
  const raise = funding.find((item) => item.status === 'ACTIVE');
  return raise ? matchesHref({ type: 'FUNDING_REQUEST', id: raise.id }) : null;
}

async function myPublishedProducts(): Promise<MyProduct[]> {
  const inventions = await serverGet<InventionSummary[]>('/api/v1/inventions');
  return inventions
    .filter((item) => item.status === 'PUBLISHED')
    .map((item) => ({ id: item.id, title: item.title || 'Inovasi tanpa judul' }));
}

export default async function DiscoverPage({ searchParams }: Props) {
  const params = await searchParams;
  const query = new URLSearchParams();
  for (const [name, value] of Object.entries(params)) if (typeof value === 'string' && value) query.set(name, value);
  const me = await requireMe(`/discover?${query.toString()}`);
  const persona = personaOf(me);
  const type = readType(typeof params.type === 'string' ? params.type : undefined, persona);
  const filters = readFilters(params);
  const selected = typeof params.selected === 'string' ? params.selected : undefined;
  const produk = typeof params.produk === 'string' && params.produk ? params.produk : undefined;
  const isInventorPartners = persona === 'inovator' && type === 'partners';

  query.set('type', type);
  query.delete('selected');
  if (isInventorPartners) {
    query.set('produk', produk ?? 'all');
  } else {
    query.delete('produk');
  }

  const [page, on, matches, products] = await Promise.all([
    serverGet<Discovery>(`/api/v1/discovery?${query.toString()}`),
    fundingOn(),
    persona === 'inovator' ? firstSource() : Promise.resolve(null),
    isInventorPartners ? myPublishedProducts() : Promise.resolve(undefined),
  ]);

  let initialFit: FitItem[] | null = null;
  if (isInventorPartners && products && products.length) {
    const items = page.sections.flatMap((section) => section.items);
    const open = items.find((item) => item.subject_id === selected) ?? items[0];
    if (open) {
      const card = open.card as { opportunities?: unknown[] };
      if (card.opportunities?.length) {
        try {
          initialFit = await serverGet<FitItem[]>(`/api/v1/fit?partner_party_id=${encodeURIComponent(open.subject_id)}`);
        } catch {
          initialFit = null;
        }
      }
    }
  }

  return (
    <DiscoverView
      me={me}
      type={type}
      filters={filters}
      page={page}
      fundingOn={on}
      matchesHref={matches}
      selected={selected}
      products={products}
      selectedProduct={produk}
      initialFit={initialFit}
    />
  );
}

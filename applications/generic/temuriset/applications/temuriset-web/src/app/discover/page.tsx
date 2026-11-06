import type { Metadata } from 'next';

import { serverGet } from '@/api/server';
import { matchesHref, readFilters, readType, type Discovery } from '@/features/discovery/model';
import type { FundingRequest, SupportRequest } from '@/features/needs/model';
import { fundingOn } from '@/features/needs/server';
import { personaOf, requireMe } from '@/features/session';
import { DiscoverView } from '@/views/discovery/DiscoverView';

export const metadata: Metadata = { title: 'Temukan dan jelajahi' };

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

export default async function DiscoverPage({ searchParams }: Props) {
  const params = await searchParams;
  const query = new URLSearchParams();
  for (const [name, value] of Object.entries(params)) if (typeof value === 'string' && value) query.set(name, value);
  const me = await requireMe(`/discover?${query.toString()}`);
  const persona = personaOf(me);
  const type = readType(typeof params.type === 'string' ? params.type : undefined, persona);
  const filters = readFilters(params);
  query.set('type', type);
  const [page, on, matches] = await Promise.all([
    serverGet<Discovery>(`/api/v1/discovery?${query.toString()}`),
    fundingOn(),
    persona === 'inovator' ? firstSource() : Promise.resolve(null),
  ]);
  return <DiscoverView me={me} type={type} filters={filters} page={page} fundingOn={on} matchesHref={matches} />;
}

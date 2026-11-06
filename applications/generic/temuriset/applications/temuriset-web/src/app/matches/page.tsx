import type { Metadata } from 'next';
import NextLink from 'next/link';

import { serverGet } from '@/api/server';
import { EmptyState } from '@/components/tr/EmptyState';
import { Screen } from '@/components/tr/Screen';
import { ContextBar } from '@/features/ContextBar';
import { matchesHref, readSource, type Discovery } from '@/features/discovery/model';
import type { FundingRequest, SupportRequest } from '@/features/needs/model';
import { fundingOn } from '@/features/needs/server';
import { personaOf, requireMe } from '@/features/session';
import { MatchesView, type ExternalPartner } from '@/views/discovery/MatchesView';
import { PROVENANCE } from '@/views/parts';

export const metadata: Metadata = { title: 'Kecocokan' };

type Props = { searchParams: Promise<{ source?: string }> };

/** Partners whose own form is the only route in: shown apart, never as a sent pitch (AC24). */
async function externalPartners(): Promise<ExternalPartner[]> {
  const page = await serverGet<Discovery>('/api/v1/discovery?type=partners&limit=100');
  return page.sections
    .flatMap((section) => section.items)
    .filter((item) => (item.card as { contact_route?: string }).contact_route === 'EXTERNAL')
    .flatMap((item) => {
      const url = (item.card as { external_url?: string }).external_url;
      return url ? [{ id: item.subject_id, name: item.title, url }] : [];
    });
}

export default async function MatchesPage({ searchParams }: Props) {
  const raw = (await searchParams).source;
  const me = await requireMe(raw ? `/matches?source=${encodeURIComponent(raw)}` : '/matches');
  const source = readSource(raw);
  if (source) return <MatchesView me={me} source={source} externals={await externalPartners()} />;
  const [support, funding, on] = await Promise.all([
    serverGet<SupportRequest[]>('/api/v1/support-requests'),
    serverGet<FundingRequest[]>('/api/v1/funding-requests'),
    fundingOn(),
  ]);
  const choices = [
    ...support.map((item) => ({ href: matchesHref({ type: 'SUPPORT_REQUEST', id: item.id }), label: `${item.invention_title}: ${item.outcome || 'Kebutuhan dukungan'}` })),
    ...(on ? funding.map((item) => ({ href: matchesHref({ type: 'FUNDING_REQUEST', id: item.id }), label: `Pendanaan perusahaan: ${item.subject_label}` })) : []),
  ];
  return (
    <Screen persona={personaOf(me)} current="temukan" title="Kecocokan" subtitle="Pilih kebutuhan yang ingin dicocokkan dengan mandat aktif." provenance={PROVENANCE} context={<ContextBar me={me} />}>
      {choices.length ? (
        <ul className="tr-stack">
          {choices.map((choice) => (
            <li key={choice.href} className="tr-panel">
              <NextLink className="tr-link" href={choice.href}>
                {choice.label}
              </NextLink>
            </li>
          ))}
        </ul>
      ) : (
        <EmptyState
          icon="search"
          title="Belum ada kebutuhan untuk dicocokkan"
          action={
            <NextLink className="tr-btn tr-btn--primary" href="/support-requests">
              Nyatakan kebutuhan
            </NextLink>
          }>
          Kecocokan dihitung dari kebutuhan dukungan atau pendanaan perusahaan yang Anda nyatakan.
        </EmptyState>
      )}
    </Screen>
  );
}

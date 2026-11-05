import type { Metadata } from 'next';

import { serverGet } from '@/api/server';
import type { FundingRequest, SupportRequest } from '@/features/needs/model';
import { fundingOn, publishedInventions } from '@/features/needs/server';
import { requireMe } from '@/features/session';
import { NeedsView } from '@/views/needs/NeedsViews';

export const metadata: Metadata = { title: 'Kebutuhan dan pendanaan' };

type Props = { searchParams: Promise<{ invention?: string }> };

export default async function SupportRequestsPage({ searchParams }: Props) {
  const me = await requireMe('/support-requests');
  const [support, funding, published, on] = await Promise.all([
    serverGet<SupportRequest[]>('/api/v1/support-requests'),
    serverGet<FundingRequest[]>('/api/v1/funding-requests'),
    publishedInventions(),
    fundingOn(),
  ]);
  return <NeedsView me={me} support={support} funding={funding} published={published} fundingOn={on} invention={(await searchParams).invention} />;
}

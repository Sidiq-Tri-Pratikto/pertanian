import type { Metadata } from 'next';

import type { FundingRequest } from '@/features/needs/model';
import { fundingOn, ownedOr404 } from '@/features/needs/server';
import { requireMe } from '@/features/session';
import { FundingView } from '@/views/needs/NeedsViews';

export const metadata: Metadata = { title: 'Pendanaan Perusahaan' };

type Props = { params: Promise<{ id: string }> };

export default async function FundingRequestPage({ params }: Props) {
  const { id } = await params;
  const me = await requireMe(`/funding-requests/${id}`);
  const request = await ownedOr404<FundingRequest>(`/api/v1/funding-requests/${encodeURIComponent(id)}`);
  return <FundingView me={me} request={request} fundingOn={await fundingOn()} />;
}

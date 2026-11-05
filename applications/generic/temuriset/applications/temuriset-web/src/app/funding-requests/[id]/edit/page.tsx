import type { Metadata } from 'next';

import { serverGet } from '@/api/server';
import type { FundingRequest, LegalEntity } from '@/features/needs/model';
import { fundingOn, ownedOr404, publishedInventions } from '@/features/needs/server';
import { requireMe } from '@/features/session';
import { FundingEditView } from '@/views/needs/NeedsViews';

export const metadata: Metadata = { title: 'Ubah pendanaan perusahaan' };

type Props = { params: Promise<{ id: string }> };

export default async function EditFundingRequestPage({ params }: Props) {
  const { id } = await params;
  const me = await requireMe(`/funding-requests/${id}/edit`);
  const request = await ownedOr404<FundingRequest>(`/api/v1/funding-requests/${encodeURIComponent(id)}`);
  const [entities, published, on] = await Promise.all([serverGet<LegalEntity[]>('/api/v1/legal-entities'), publishedInventions(), fundingOn()]);
  return <FundingEditView me={me} request={request} entities={entities} published={published} fundingOn={on} />;
}

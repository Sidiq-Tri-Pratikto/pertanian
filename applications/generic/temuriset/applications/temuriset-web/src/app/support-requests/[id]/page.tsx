import type { Metadata } from 'next';

import type { SupportRequest } from '@/features/needs/model';
import { ownedOr404 } from '@/features/needs/server';
import { requireMe, safeReturn } from '@/features/session';
import { SupportView } from '@/views/needs/NeedsViews';

export const metadata: Metadata = { title: 'Kebutuhan dukungan' };

type Props = { params: Promise<{ id: string }>; searchParams: Promise<{ return?: string }> };

export default async function SupportRequestPage({ params, searchParams }: Props) {
  const { id } = await params;
  const me = await requireMe(`/support-requests/${id}`);
  const request = await ownedOr404<SupportRequest>(`/api/v1/support-requests/${encodeURIComponent(id)}`);
  return <SupportView me={me} request={request} returnTo={safeReturn((await searchParams).return)} />;
}

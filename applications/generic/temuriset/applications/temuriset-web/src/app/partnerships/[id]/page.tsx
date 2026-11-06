import type { Metadata } from 'next';

import { ApiError } from '@/api/errors';
import { serverGet } from '@/api/server';
import { validId, type Partnership } from '@/features/relationships/model';
import { requireMe } from '@/features/session';
import { PartnershipView, RelationshipUnavailable } from '@/views/relationships/PartnershipView';

export const metadata: Metadata = { title: 'Kerja Sama' };

export default async function PartnershipPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const me = await requireMe(`/partnerships/${id}`);
  if (!validId(id)) return <RelationshipUnavailable me={me} />;
  let relationship: Partnership;
  try {
    relationship = await serverGet<Partnership>(`/api/v1/partnerships/${id}`);
  } catch (error) {
    if (error instanceof ApiError && error.code === 'NOT_FOUND') return <RelationshipUnavailable me={me} />;
    throw error;
  }
  return <PartnershipView key={me.active_party_id} me={me} initial={relationship} />;
}

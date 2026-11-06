import type { Metadata } from 'next';
import { redirect } from 'next/navigation';

import { ApiError } from '@/api/errors';
import { serverGet } from '@/api/server';
import { validId, type Partnership, type ProposalOptions } from '@/features/relationships/model';
import { requireMe } from '@/features/session';
import { RelationshipUnavailable } from '@/views/relationships/PartnershipView';
import { ProposeView } from '@/views/relationships/ProposeView';

export const metadata: Metadata = { title: 'Usulkan Kerja Sama' };

export default async function ProposePage({ searchParams }: { searchParams: Promise<{ pitch?: string }> }) {
  const { pitch } = await searchParams;
  const me = await requireMe(`/partnerships/new${pitch ? `?pitch=${encodeURIComponent(pitch)}` : ''}`);
  if (!pitch || !validId(pitch)) return <RelationshipUnavailable me={me} />;
  let options: ProposalOptions;
  try {
    const existing = await serverGet<Partnership | null>(`/api/v1/pitches/${pitch}/partnership`);
    if (existing) redirect(`/partnerships/${existing.id}`);
    options = await serverGet<ProposalOptions>(`/api/v1/pitches/${pitch}/partnership-options`);
  } catch (error) {
    if (error instanceof ApiError && ['NOT_FOUND', 'FORBIDDEN', 'MEETING_NOT_COMPLETED', 'INVALID_TRANSITION', 'CONFLICT'].includes(error.code)) {
      return <RelationshipUnavailable me={me} pitchId={error.code === 'NOT_FOUND' ? undefined : pitch} message={error.code === 'NOT_FOUND' ? undefined : error.message} />;
    }
    throw error;
  }
  return <ProposeView key={me.active_party_id} me={me} pitchId={pitch} types={options.types} />;
}

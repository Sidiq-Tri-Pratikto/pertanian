import type { Metadata } from 'next';
import { notFound } from 'next/navigation';

import { ApiError } from '@/api/errors';
import { serverGet } from '@/api/server';
import type { Mandate, PartnerProfile } from '@/features/intake/model';
import { requireMe } from '@/features/session';
import { PartnerView } from '@/views/intake/PartnerView';

export const metadata: Metadata = { title: 'Profil mitra' };

type Props = { params: Promise<{ partyId: string }> };

/** Reads a profile, with `null` when the party has none yet or the address names no party. */
async function profileOf(partyId: string): Promise<PartnerProfile | null> {
  try {
    return await serverGet<PartnerProfile>(`/api/v1/partners/${encodeURIComponent(partyId)}`);
  } catch (error) {
    if (error instanceof ApiError && (error.code === 'NOT_FOUND' || error.code === 'VALIDATION_FAILED')) return null;
    throw error;
  }
}

export default async function PartnerPage({ params }: Props) {
  const { partyId } = await params;
  const me = await requireMe(`/partners/${partyId}`);
  const profile = await profileOf(partyId);
  // Only the party itself is offered a way to create a profile; anyone else learns nothing about a missing one.
  if (!profile && partyId !== me.active_party_id) notFound();
  const mandates = await serverGet<Mandate[]>(`/api/v1/opportunities?partner_party_id=${encodeURIComponent(partyId)}`);
  return <PartnerView me={me} partyId={partyId} profile={profile} mandates={mandates} />;
}

import type { Metadata } from 'next';

import { ApiError } from '@/api/errors';
import { serverGet } from '@/api/server';
import { validId, type Profile } from '@/features/relationships/model';
import { PublicProfileView } from '@/views/relationships/PublicProfileView';

export const metadata: Metadata = { title: 'Profil publik' };

export default async function PublicProfilePage({ params }: { params: Promise<{ partyId: string }> }) {
  const { partyId } = await params;
  if (!validId(partyId)) return <PublicProfileView profile={null} />;
  let profile: Profile;
  try {
    profile = await serverGet<Profile>(`/api/v1/profiles/${partyId}`);
  } catch (error) {
    if (error instanceof ApiError && error.code === 'NOT_FOUND') return <PublicProfileView profile={null} />;
    throw error;
  }
  return <PublicProfileView profile={profile} />;
}

import type { Metadata } from 'next';

import { ApiError } from '@/api/errors';
import { serverGet } from '@/api/server';
import type { InvitationDetail } from '@/features/organizations';
import { requireMe } from '@/features/session';
import { InvitationView } from '@/views/InvitationView';

export const metadata: Metadata = { title: 'Undangan organisasi' };

type Props = { params: Promise<{ token: string }> };

export default async function InvitationPage({ params }: Props) {
  const { token } = await params;
  const me = await requireMe(`/undangan/${token}`);
  let invitation: InvitationDetail | null = null;
  try {
    invitation = await serverGet<InvitationDetail>(`/api/v1/invitations/${encodeURIComponent(token)}`);
  } catch (error) {
    if (!(error instanceof ApiError && error.code === 'NOT_FOUND')) throw error;
  }
  return <InvitationView me={me} token={token} invitation={invitation} />;
}

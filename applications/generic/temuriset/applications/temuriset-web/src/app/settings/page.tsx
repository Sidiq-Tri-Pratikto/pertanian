import type { Metadata } from 'next';

import { serverGet } from '@/api/server';
import { readCapabilities } from '@/features/capabilities';
import type { Invitation, Member } from '@/features/organizations';
import { requireMe } from '@/features/session';
import { SettingsView } from '@/views/SettingsView';

export const metadata: Metadata = { title: 'Profil dan privasi' };

type Props = { searchParams: Promise<{ bergabung?: string }> };

export default async function SettingsPage({ searchParams }: Props) {
  const me = await requireMe('/settings');
  const { bergabung } = await searchParams;
  const acting = me.organizations?.find((organization) => organization.party_id === me.active_party_id);
  const members = acting ? await serverGet<Member[]>(`/api/v1/organizations/${acting.organization_id}/members`) : null;
  const invitations =
    acting && me.capabilities?.includes('manage_members')
      ? await serverGet<Invitation[]>(`/api/v1/organizations/${acting.organization_id}/invitations`)
      : null;
  return (
    <SettingsView
      me={me}
      capabilities={await readCapabilities()}
      members={members}
      invitations={invitations}
      joined={bergabung === '1'}
    />
  );
}

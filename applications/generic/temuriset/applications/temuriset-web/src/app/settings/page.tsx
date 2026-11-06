import type { Metadata } from 'next';

import { ApiError } from '@/api/errors';
import { serverGet } from '@/api/server';
import { readCapabilities } from '@/features/capabilities';
import type { Invitation, Member } from '@/features/organizations';
import { readReportSubject, type PrivacyRequest, type Report, type SectionData } from '@/features/privacy/model';
import { requireMe } from '@/features/session';
import { SettingsView } from '@/views/SettingsView';

export const metadata: Metadata = { title: 'Profil dan privasi' };

type Props = { searchParams: Promise<{ bergabung?: string; lapor?: string | string[]; objek?: string | string[] }> };

async function sectionData<Item>(path: `/${string}`): Promise<SectionData<Item>> {
  try {
    return { data: await serverGet<Item[]>(path), failure: null };
  } catch (cause) {
    const { message, requestId, code, recovery } = ApiError.from(cause);
    return { data: [], failure: { message, requestId, code, recovery } };
  }
}

export default async function SettingsPage({ searchParams }: Props) {
  const me = await requireMe('/settings');
  const { bergabung, lapor, objek } = await searchParams;
  const acting = me.organizations?.find((organization) => organization.party_id === me.active_party_id);
  const members = acting ? await serverGet<Member[]>(`/api/v1/organizations/${acting.organization_id}/members`) : null;
  const invitations =
    acting && me.capabilities?.includes('manage_members')
      ? await serverGet<Invitation[]>(`/api/v1/organizations/${acting.organization_id}/invitations`)
      : null;
  const [reports, privacy] = await Promise.all([
    sectionData<Report>('/api/v1/reports'),
    sectionData<PrivacyRequest>('/api/v1/privacy-requests'),
  ]);
  return (
    <SettingsView
      me={me}
      capabilities={await readCapabilities()}
      members={members}
      invitations={invitations}
      joined={bergabung === '1'}
      reportSubject={readReportSubject(lapor, objek)}
      reports={reports}
      privacy={privacy}
    />
  );
}

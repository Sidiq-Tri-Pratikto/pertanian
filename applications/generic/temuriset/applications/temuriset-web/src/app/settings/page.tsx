import type { Metadata } from 'next';

import { ApiError } from '@/api/errors';
import { serverGet } from '@/api/server';
import { readCapabilities, readCapabilityManifest } from '@/features/capabilities';
import type { Invitation, Member } from '@/features/organizations';
import { readReportSubject, type PrivacyRequest, type Report, type SectionData } from '@/features/privacy/model';
import type { ProfileSettings } from '@/features/relationships/model';
import { requireMe } from '@/features/session';
import type { CalendarConnectionProps, CalendarStatus } from '@/views/settings/CalendarConnection';
import { SettingsView } from '@/views/SettingsView';

export const metadata: Metadata = { title: 'Profil dan privasi' };

type Props = { searchParams: Promise<{ bergabung?: string; lapor?: string | string[]; objek?: string | string[]; kalender?: string; ref?: string }> };

async function sectionData<Item>(path: `/${string}`): Promise<SectionData<Item>> {
  try {
    return { data: await serverGet<Item[]>(path), failure: null };
  } catch (cause) {
    const { message, requestId, code, recovery } = ApiError.from(cause);
    return { data: [], failure: { message, requestId, code, recovery } };
  }
}

async function calendarStatus(): Promise<CalendarConnectionProps> {
  try {
    return { initial: await serverGet<CalendarStatus>('/api/v1/me/calendar') };
  } catch (cause) {
    const { message, requestId } = ApiError.from(cause);
    return { initial: null, initialFailure: { message, requestId } };
  }
}

export default async function SettingsPage({ searchParams }: Props) {
  const me = await requireMe('/settings');
  const { bergabung, lapor, objek, kalender, ref } = await searchParams;
  const acting = me.organizations?.find((organization) => organization.party_id === me.active_party_id);
  const members = acting ? await serverGet<Member[]>(`/api/v1/organizations/${acting.organization_id}/members`) : null;
  const invitations =
    acting && me.capabilities?.includes('manage_members')
      ? await serverGet<Invitation[]>(`/api/v1/organizations/${acting.organization_id}/invitations`)
      : null;
  const [reports, privacy, profile, manifest, calendar] = await Promise.all([
    sectionData<Report>('/api/v1/reports'),
    sectionData<PrivacyRequest>('/api/v1/privacy-requests'),
    me.capabilities?.includes('edit_portfolio') ? serverGet<ProfileSettings>('/api/v1/profiles/me') : null,
    readCapabilityManifest(),
    calendarStatus(),
  ]);
  return (
    <SettingsView
      me={me}
      capabilities={await readCapabilities()}
      emailNotificationsAvailable={manifest?.adapters.some((adapter) => adapter.id === 'email' && adapter.status === 'available') ?? false}
      calendar={{
        ...calendar,
        callbackFailure: kalender === 'gagal'
          ? { message: 'Kalender belum tersambung. Mulai lagi dari pengaturan kalender.', requestId: ref && /^ref_[a-f0-9]{32}$/.test(ref) ? ref : null }
          : null,
      }}
      members={members}
      profile={profile}
      invitations={invitations}
      joined={bergabung === '1'}
      reportSubject={readReportSubject(lapor, objek)}
      reports={reports}
      privacy={privacy}
    />
  );
}

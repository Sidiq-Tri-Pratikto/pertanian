import Link from 'next/link';

import type { Me } from '@/api/client';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import { SummaryList } from '@/components/tr/SummaryList';
import { AccountForm, CreateOrganizationForm, InviteForm, RevokeButton, SignOutButton } from '@/features/AccountForms';
import { ContextBar } from '@/features/ContextBar';
import { capabilityList, formatDateTime, INVITATION_STATUS, type Invitation, type Member } from '@/features/organizations';
import type { PrivacyRequest, Report, ReportSubject, SectionData } from '@/features/privacy/model';
import { PERSONA_LABEL, readPersona } from '@/features/persona';
import type { ProfileSettings } from '@/features/relationships/model';
import { ProfileForm } from '@/features/relationships/ProfileForm';
import { FEATURES, type Capabilities } from '@/features/registry';
import { ServiceStatus } from '@/features/ServiceStatus';
import { LOCALES } from '@/features/signIn';
import { FeatureList, PROVENANCE } from '@/views/parts';
import { CalendarConnection, type CalendarConnectionProps } from '@/views/settings/CalendarConnection';
import { PrivacyRequests } from '@/views/settings/PrivacyRequests';
import { ReportForm } from '@/views/settings/ReportForm';

type SettingsViewProps = {
  me: Me;
  capabilities: Capabilities;
  /** Members of the organization the account acts as; null when it acts as itself. */
  members: Member[] | null;
  /** Its invitations, for members who manage members. */
  invitations: Invitation[] | null;
  joined?: boolean;
  calendar?: CalendarConnectionProps;
  profile?: ProfileSettings | null;
  reports?: SectionData<Report>;
  privacy?: SectionData<PrivacyRequest>;
  reportSubject?: ReportSubject | null;
};

/** S18: the account, its organizations, members and invitations, the service check and every planned feature. */
export function SettingsView({ me, capabilities, members, invitations, joined, calendar, profile, reports, privacy, reportSubject }: SettingsViewProps) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  const organizations = me.organizations ?? [];
  const acting = organizations.find((organization) => organization.party_id === me.active_party_id);
  const scope = { id: me.active_party_id, label: acting?.name ?? 'Diri sendiri' };
  return (
    <Screen
      persona={persona}
      current="profil"
      title="Profil dan privasi"
      subtitle="Akun, organisasi, dan siapa yang bertindak atas nama siapa."
      provenance={PROVENANCE}
      context={<ContextBar me={me} />}>
      {joined ? <Status tone="success" label="Anda sudah bergabung dengan organisasi" live /> : null}
      <section className="tr-panel tr-stack" aria-labelledby="judul-akun">
        <h2 id="judul-akun" className="tr-sys-type-heading-sm">
          Akun
        </h2>
        <SummaryList
          rows={[
            { id: 'akun-nama', label: 'Nama tampilan', value: me.account.display_name },
            { id: 'akun-email', label: 'Email', value: `${me.account.email} · Email terverifikasi` },
            { id: 'akun-tampilan', label: 'Menu yang ditampilkan', value: PERSONA_LABEL[persona] },
            { id: 'akun-bahasa', label: 'Bahasa', value: LOCALES.find((locale) => locale.value === me.account.locale)?.label ?? me.account.locale },
            { id: 'akun-zona', label: 'Zona waktu', value: me.account.time_zone },
          ]}
        />
        <details className="tr-disclosure">
          <summary className="tr-link">Ubah akun</summary>
          <AccountForm me={me} />
        </details>
      </section>
      <section className="tr-panel tr-stack" aria-labelledby="judul-organisasi">
        <h2 id="judul-organisasi" className="tr-sys-type-heading-sm">
          Organisasi
        </h2>
        {organizations.length ? (
          <ul className="tr-stack">
            {organizations.map((organization) => (
              <li key={organization.organization_id}>
                <strong>{organization.name}</strong>
                <p className="tr-muted tr-sys-type-support">Kewenangan Anda: {capabilityList(organization.capabilities)}</p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="tr-muted">Anda bertindak atas nama sendiri. Organisasi tidak wajib.</p>
        )}
        <details className="tr-disclosure">
          <summary className="tr-link">Buat organisasi</summary>
          <CreateOrganizationForm />
        </details>
      </section>
      {acting && members ? (
        <section className="tr-panel tr-stack" aria-labelledby="judul-anggota">
          <h2 id="judul-anggota" className="tr-sys-type-heading-sm">
            Anggota {acting.name}
          </h2>
          <ul className="tr-stack">
            {members.map((member) => (
              <li key={member.account_id}>
                <strong>{member.display_name}</strong>
                <p className="tr-muted tr-sys-type-support">{capabilityList(member.capabilities)}</p>
              </li>
            ))}
          </ul>
          {invitations ? (
            <>
              <h3 className="tr-sys-type-label">Undangan</h3>
              {invitations.length ? (
                <ul className="tr-stack">
                  {invitations.map((invitation) => (
                    <li key={invitation.id} className="tr-stack">
                      <span>
                        <strong>{invitation.email}</strong> · {INVITATION_STATUS[invitation.status]} · berlaku sampai{' '}
                        {formatDateTime(invitation.expires_at, me.account.time_zone)}
                      </span>
                      <span className="tr-muted tr-sys-type-support">{capabilityList(invitation.capabilities)}</span>
                      {invitation.status === 'pending' ? <RevokeButton me={me} invitationId={invitation.id} email={invitation.email} /> : null}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="tr-muted">Belum ada undangan.</p>
              )}
              <details className="tr-disclosure">
                <summary className="tr-link">Undang anggota</summary>
                <InviteForm me={me} organizationId={acting.organization_id} />
              </details>
            </>
          ) : null}
        </section>
      ) : null}
      <section className="tr-panel tr-stack" id="profil-publik" aria-labelledby="judul-profil-publik">
        <h2 id="judul-profil-publik" className="tr-sys-type-heading-sm">Profil publik</h2>
        <Link className="tr-link" href={`/profiles/${me.active_party_id}`}>Lihat profil publik</Link>
        {profile ? <ProfileForm key={profile.party_id} profile={profile} /> : null}
      </section>
      {reports ? <ReportForm key={reportSubject?.id ?? 'blank'} scope={scope} subject={reportSubject ?? null} initial={reports} /> : null}
      {calendar ? <CalendarConnection key={`${calendar.initial?.state ?? 'unavailable'}-${calendar.initial?.version ?? 0}`} {...calendar} /> : null}
      {privacy ? <PrivacyRequests scope={scope} initial={privacy} /> : null}
      <section className="tr-stack" aria-labelledby="judul-layanan">
        <h2 id="judul-layanan" className="tr-sys-type-heading-sm">
          Layanan
        </h2>
        <ServiceStatus />
      </section>
      <div id="rencana">
        <FeatureList ids={FEATURES.map((feature) => feature.id)} capabilities={capabilities} title="Rencana fitur" />
      </div>
      <SignOutButton />
    </Screen>
  );
}

import NextLink from 'next/link';

import type { Me } from '@/api/client';
import { Disclosure } from '@/components/tr/Disclosure';
import { EmptyState } from '@/components/tr/EmptyState';
import { FinancialScope } from '@/components/tr/FinancialScope';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import { ContextBar } from '@/features/ContextBar';
import { ExternalRoute } from '@/features/intake/ExternalRoute';
import { RELATIONSHIP_FORMS, scopeProps, type Mandate, type PartnerProfile } from '@/features/intake/model';
import { NewMandate } from '@/features/intake/NewMandate';
import { ProfileForm } from '@/features/intake/ProfileForm';
import { readPersona } from '@/features/persona';
import { labelOf, STAGES } from '@/features/portfolio/model';
import { MandateCard } from '@/views/intake/MandateCard';
import { PROVENANCE } from '@/views/parts';

const UNKNOWN = 'Belum diketahui';

function listed(items: string[]): string {
  return items.length ? items.join(', ') : UNKNOWN;
}

type Props = { me: Me; partyId: string; profile: PartnerProfile | null; mandates: Mandate[] };

/** S08: what a partner states, with its source and current availability, and its mandates. */
export function PartnerView({ me, partyId, profile, mandates }: Props) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  const own = me.active_party_id === partyId;
  const canEdit = own && (me.capabilities?.includes('edit_portfolio') ?? false);
  const shell = {
    persona,
    current: persona === 'mitra' ? 'mandat' : 'temukan',
    provenance: PROVENANCE,
    context: <ContextBar me={me} />,
    back: (
      <NextLink className="tr-link" href={own ? '/opportunities' : '/discover'}>
        Kembali
      </NextLink>
    ),
  };

  if (!profile) {
    return (
      <Screen {...shell} title="Profil mitra">
        <EmptyState
          icon="partner"
          title="Profil mitra belum ada"
          action={
            canEdit ? (
              <a className="tr-btn tr-btn--primary" href="#profil-mitra">
                Buat profil
              </a>
            ) : undefined
          }>
          Profil menjelaskan minat, tahap yang diterima, bentuk dukungan, dan jalur kontak Anda. Investor individu tidak perlu organisasi.
        </EmptyState>
        {canEdit ? <ProfileForm profile={null} partyId={partyId} actingPartyId={me.active_party_id} /> : null}
      </Screen>
    );
  }

  const availability = profile.availability;
  const open = availability.current_intake_status === 'OPEN';
  return (
    <Screen {...shell} title={profile.party_name || 'Profil mitra'} subtitle={profile.subtype || undefined}>
      <section className="tr-panel tr-stack" aria-labelledby="profil-ringkas">
        <h2 id="profil-ringkas" className="tr-sys-type-heading-sm">
          Profil
        </h2>
        <p className="tr-row">
          <Status tone={open ? 'action' : availability.current_intake_status === 'CLOSED' ? 'neutral' : 'warning'} label={availability.label} />
          <span className="tr-tag tr-sys-type-support">{availability.source_label}</span>
        </p>
        {profile.thesis ? <p>{profile.thesis}</p> : null}
        <p>{`Sektor: ${listed(profile.sectors)}`}</p>
        <p>{`Tahap yang diterima: ${listed(profile.stages.map((stage) => labelOf(STAGES, stage)))}`}</p>
        <p>{`Wilayah: ${listed(profile.regions)}`}</p>
        <p>{`Bentuk dukungan: ${listed(profile.support_forms)}`}</p>
        {profile.relationship_forms.length ? <p>{`Bentuk kerja sama: ${profile.relationship_forms.map((form) => labelOf(RELATIONSHIP_FORMS, form)).join(', ')}`}</p> : null}
        {profile.review_expectations ? <p>{`Ekspektasi peninjauan: ${profile.review_expectations}`}</p> : null}
        {profile.check_range ? <FinancialScope {...scopeProps(profile.check_range)} /> : null}
        {profile.contact_route === 'EXTERNAL' && profile.external_url ? <ExternalRoute partyId={partyId} actingPartyId={me.active_party_id} url={profile.external_url} record={!own} /> : null}
        {profile.contact_route === 'NONE' ? <p className="tr-muted">Mitra ini sedang tidak menerima pendekatan baru.</p> : null}
      </section>
      {canEdit ? (
        <Disclosure label="Ubah profil">
          <ProfileForm key={profile.version} profile={profile} partyId={partyId} actingPartyId={me.active_party_id} />
        </Disclosure>
      ) : null}
      <section className="tr-stack" aria-labelledby="mandat-mitra">
        <h2 id="mandat-mitra" className="tr-sys-type-heading-sm">
          Mandat
        </h2>
        {mandates.length ? (
          <ul className="tr-stack">
            {mandates.map((mandate) => (
              <li key={mandate.id}>
                <MandateCard mandate={mandate} editingAs={canEdit ? me.active_party_id : null} />
              </li>
            ))}
          </ul>
        ) : (
          <p className="tr-muted">Belum ada mandat yang terlihat.</p>
        )}
        {canEdit ? <NewMandate actingPartyId={me.active_party_id} /> : null}
      </section>
    </Screen>
  );
}

import NextLink from 'next/link';

import type { Me } from '@/api/client';
import { EmptyState } from '@/components/tr/EmptyState';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import { ContextBar } from '@/features/ContextBar';
import { destinationFor } from '@/features/destinations';
import type { Mandate } from '@/features/intake/model';
import { NewMandate } from '@/features/intake/NewMandate';
import { readPersona } from '@/features/persona';
import { findFeature, isOffered, type Capabilities } from '@/features/registry';
import { MandateCard } from '@/views/intake/MandateCard';
import { FeatureList, PROVENANCE } from '@/views/parts';

type Props = {
  me: Me;
  mandates: Mandate[];
  capabilities: Capabilities;
  /** The version just activated, from the editor. */
  activated?: string;
};

/** Kebutuhan/Mandat: the acting party's mandates with status and version. */
export function MandatesView({ me, mandates, capabilities, activated }: Props) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  const destination = destinationFor('opportunities', persona);
  const canEdit = me.capabilities?.includes('edit_portfolio') ?? false;
  const planned = destination.features.some((id) => {
    const feature = findFeature(id);
    return feature?.status === 'coming_soon' && isOffered(feature, capabilities);
  });
  return (
    <Screen persona={persona} current="mandat" title={destination.title} subtitle={destination.subtitle} provenance={PROVENANCE} context={<ContextBar me={me} />}>
      {activated ? (
        <Status tone="success" label="Mandat diaktifkan" live>
          <p>{`Mandat aktif sebagai versi ${activated}. Pitching yang sudah terkirim memakai versinya sendiri.`}</p>
        </Status>
      ) : null}
      <p>
        <NextLink className="tr-link" href={`/partners/${me.active_party_id}`}>
          Profil mitra saya
        </NextLink>
      </p>
      {mandates.length ? (
        <section className="tr-stack" aria-labelledby="mandat-anda">
          <h2 id="mandat-anda" className="tr-sys-type-heading-sm">
            Mandat Anda
          </h2>
          <ul className="tr-stack">
            {mandates.map((mandate) => (
              <li key={mandate.id}>
                <MandateCard mandate={mandate} editingAs={canEdit ? me.active_party_id : null} />
              </li>
            ))}
          </ul>
        </section>
      ) : (
        <EmptyState icon="file" title="Belum ada mandat">
          Mandat menjelaskan dukungan yang Anda tawarkan dan syarat yang terlihat oleh pengirim.
        </EmptyState>
      )}
      {canEdit ? <NewMandate actingPartyId={me.active_party_id} /> : null}
      {planned ? <FeatureList ids={destination.features} capabilities={capabilities} /> : null}
    </Screen>
  );
}

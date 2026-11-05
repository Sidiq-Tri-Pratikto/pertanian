import Link from 'next/link';

import { EmptyState } from '@/components/tr/EmptyState';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import { homeFor, type Persona } from '@/features/persona';
import type { Feature } from '@/features/registry';
import { PersonaContext, PROVENANCE } from '@/views/parts';

type ComingSoonViewProps = {
  persona: Persona;
  feature: Feature | undefined;
  /** Engineers see the spec folders in development builds only. */
  showSpecs?: boolean;
};

/** What a planned feature will do. Nothing here creates or stores data. */
export function ComingSoonView({ persona, feature, showSpecs = false }: ComingSoonViewProps) {
  const home = homeFor(persona);
  const back = (
    <Link className="tr-link" href={home}>
      Kembali
    </Link>
  );

  if (!feature) {
    return (
      <Screen persona={persona} title="Fitur tidak dikenal" provenance={PROVENANCE} context={<PersonaContext persona={persona} />}>
        <EmptyState
          icon="question"
          title="Alamat ini tidak menunjuk ke fitur yang direncanakan"
          action={
            <Link className="tr-link" href="/settings#rencana">
              Lihat semua rencana fitur
            </Link>
          }>
          Periksa alamatnya, atau buka daftar rencana fitur.
        </EmptyState>
      </Screen>
    );
  }

  return (
    <Screen
      persona={persona}
      title={feature.title}
      subtitle={feature.summary}
      back={back}
      provenance={PROVENANCE}
      context={<PersonaContext persona={persona} />}>
      <Status tone="neutral" label="Segera hadir">
        <p>Fitur ini belum tersedia pada versi ini. Tidak ada data yang dibuat atau disimpan.</p>
      </Status>
      <section className="tr-panel tr-stack" aria-labelledby="yang-direncanakan">
        <h2 id="yang-direncanakan" className="tr-sys-type-heading-sm">
          Yang direncanakan
        </h2>
        <ul className="tr-reasons">
          {feature.points.map((point) => (
            <li key={point}>{point}</li>
          ))}
        </ul>
      </section>
      {showSpecs ? <p className="tr-muted tr-sys-type-support">Spesifikasi: {feature.specs.join(', ')}</p> : null}
    </Screen>
  );
}

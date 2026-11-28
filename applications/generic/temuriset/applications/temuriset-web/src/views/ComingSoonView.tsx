import Link from 'next/link';

import { EmptyState } from '@/components/tr/EmptyState';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import type { Me } from '@/api/client';
import { ContextBar } from '@/features/ContextBar';
import { homeFor, readPersona } from '@/features/persona';
import type { Feature } from '@/features/registry';
import { PROVENANCE } from '@/views/parts';
import { t } from '@/features/i18n/t';

type ComingSoonViewProps = {
  me: Me;
  feature: Feature | undefined;
  /** Engineers see the spec folders in development builds only. */
  showSpecs?: boolean;
};

/** What a planned feature will do. Nothing here creates or stores data. */
export function ComingSoonView({ me, feature, showSpecs = false }: ComingSoonViewProps) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  const home = homeFor(persona);
  const back = (
    <Link className="tr-link" href={home}>
      {t('Kembali')}
    </Link>
  );

  if (!feature) {
    return (
      <Screen persona={persona} title={t('Fitur tidak dikenal')} provenance={PROVENANCE} context={<ContextBar me={me} />}>
        <EmptyState
          icon="question"
          title={t('Alamat ini tidak menunjuk ke fitur yang direncanakan')}
          action={
            <Link className="tr-link" href="/settings#rencana">
              {t('Lihat semua rencana fitur')}
            </Link>
          }>
          {t('Periksa alamatnya, atau buka daftar rencana fitur.')}
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
      context={<ContextBar me={me} />}>
      <Status tone="neutral" label="Segera hadir">
        <p>{t('Fitur ini belum tersedia pada versi ini. Tidak ada data yang dibuat atau disimpan.')}</p>
      </Status>
      <section className="tr-panel tr-stack" aria-labelledby="yang-direncanakan">
        <h2 id="yang-direncanakan" className="tr-sys-type-heading-sm">
          {t('Yang direncanakan')}
        </h2>
        <ul className="tr-reasons">
          {feature.points.map((point) => (
            <li key={point}>{t(point)}</li>
          ))}
        </ul>
      </section>
      {showSpecs ? <p className="tr-muted tr-sys-type-support">{t('Spesifikasi')}: {feature.specs.join(', ')}</p> : null}
    </Screen>
  );
}

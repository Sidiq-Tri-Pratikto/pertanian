import Link from 'next/link';

import { findFeature, isOffered, type Capabilities, type Feature } from '@/features/registry';
import { t } from '@/features/i18n/t';

export const PROVENANCE = 'Versi awal';

/** Planned features for one destination. Each row opens its "Segera hadir" screen. */
export function FeatureList({
  ids,
  capabilities,
  title = 'Segera hadir',
}: {
  ids: string[];
  capabilities: Capabilities;
  title?: string;
}) {
  const features = ids
    .map(findFeature)
    .filter((feature): feature is Feature => feature !== undefined && feature.status === 'coming_soon' && isOffered(feature, capabilities));
  if (!features.length) return null;
  return (
    <section className="tr-stack" aria-labelledby="fitur-segera">
      <h2 id="fitur-segera" className="tr-sys-type-heading-sm">
        {t(title)}
      </h2>
      <ul className="tr-stack">
        {features.map((feature) => (
          <li key={feature.id} className="tr-panel tr-stack">
            <h3 className="tr-sys-type-label">{t(feature.title)}</h3>
            <p className="tr-muted">{t(feature.summary)}</p>
            <p>
              <Link className="tr-link" href={`/segera-hadir/${feature.id}`}>
                {t('Lihat rencana')} <span className="tr-sr">{t(feature.title)}</span>
              </Link>
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}

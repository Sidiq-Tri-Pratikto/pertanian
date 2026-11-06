import Link from 'next/link';

import { findFeature, isOffered, type Capabilities, type Feature } from '@/features/registry';

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
  return (
    <section className="tr-stack" aria-labelledby="fitur-segera">
      <h2 id="fitur-segera" className="tr-sys-type-heading-sm">
        {title}
      </h2>
      <ul className="tr-stack">
        {features.map((feature) => (
          <li key={feature.id} className="tr-panel tr-stack">
            <h3 className="tr-sys-type-label">{feature.title}</h3>
            <p className="tr-muted">{feature.summary}</p>
            <p>
              <Link className="tr-link" href={`/segera-hadir/${feature.id}`}>
                Lihat rencana <span className="tr-sr">{feature.title}</span>
              </Link>
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}

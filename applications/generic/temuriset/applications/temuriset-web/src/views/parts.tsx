import Link from 'next/link';

import { Icon } from '@/components/tr/Icon';
import { PERSONA_LABEL, type Persona } from '@/features/persona';
import { findFeature, isOffered, type Capabilities, type Feature } from '@/features/registry';

export const PROVENANCE = 'Versi awal';

/** The persona shown in the bar, with a way to change it. A persona is a view, not an account. */
export function PersonaContext({ persona }: { persona: Persona }) {
  return (
    <p className="tr-context">
      <Icon name="user" />
      <span>
        Tampilan: <strong>{PERSONA_LABEL[persona]}</strong> ·{' '}
        <Link className="tr-link" href="/settings#tampilan">
          Ubah
        </Link>
      </span>
    </p>
  );
}

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
    .filter((feature): feature is Feature => feature !== undefined && isOffered(feature, capabilities));
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

import NextLink from 'next/link';

import { Disclosure } from '@/components/tr/Disclosure';
import { Status } from '@/components/tr/Status';
import {
  estimateText,
  recommendationAction,
  recommendationCopy,
  type Recommendation,
} from '@/features/discovery/recommendations';
import { t } from '@/features/i18n/t';

type Props = {
  recommendations: Recommendation[];
  returnTo?: string;
  limit?: number;
};

function Item({ rec, returnTo }: { rec: Recommendation; returnTo?: string }) {
  const copy = recommendationCopy(rec);
  const action = recommendationAction(rec, returnTo);
  return (
    <li className="tr-panel tr-stack">
      <div className="tr-row">
        <strong className="tr-sys-type-support-strong">{copy.title}</strong>
        {rec.blocking ? <Status tone="danger" icon={null} label={t('Menghalangi')} /> : null}
      </div>
      <p className="tr-sys-type-support">{copy.body}</p>
      {rec.estimate ? (
        <p className="tr-tag tr-sys-type-support">{estimateText(rec.estimate)}</p>
      ) : null}
      {action ? (
        <div className="tr-row">
          <NextLink className="tr-btn tr-btn--secondary" href={action.href}>
            {action.label}
          </NextLink>
        </div>
      ) : null}
    </li>
  );
}

/** Applicant-only improvement recommendations, blocking first, capped at five with "Lihat semua (n)" (spec 058). */
export function ImprovementList({ recommendations, returnTo, limit = 5 }: Props) {
  if (!recommendations.length) return null;
  const visible = recommendations.slice(0, limit);
  const rest = recommendations.slice(limit);
  return (
    <section className="tr-stack" aria-label={t('Cara meningkatkan kecocokan')}>
      <h4 className="tr-sys-type-label">{t('Cara meningkatkan kecocokan')}</h4>
      <ul className="tr-stack">
        {visible.map((rec, index) => (
          <Item key={`${rec.kind}-${index}`} rec={rec} returnTo={returnTo} />
        ))}
      </ul>
      {rest.length ? (
        <Disclosure label={t('Lihat semua ({n})', { n: recommendations.length })}>
          <ul className="tr-stack">
            {rest.map((rec, index) => (
              <Item key={`${rec.kind}-more-${index}`} rec={rec} returnTo={returnTo} />
            ))}
          </ul>
        </Disclosure>
      ) : null}
    </section>
  );
}

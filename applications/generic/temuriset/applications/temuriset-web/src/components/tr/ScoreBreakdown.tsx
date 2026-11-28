import { Button } from '@/components/tr/Button';
import { Status } from '@/components/tr/Status';
import { Toggletip } from '@/components/tr/Toggletip';
import {
  DIMENSION_META,
  DIMENSION_STATUS_LABEL,
  dimensionSentence,
  dimensionTone,
  orderedDimensions,
  type Dimension,
} from '@/features/discovery/breakdown';
import { t } from '@/features/i18n/t';

export type ScoreDelta = { before: number | null; after: number | null };

type Props = {
  dimensions: Dimension[];
  heading?: string;
  deltas?: Partial<Record<Dimension['id'], ScoreDelta>>;
  onRecalculate?: () => void;
};

function fillClass(status: Dimension['status']): string {
  if (status === 'MATCH') return 'tr-meter__fill tr-meter__fill--match';
  if (status === 'PARTIAL') return 'tr-meter__fill tr-meter__fill--partial';
  return 'tr-meter__fill tr-meter__fill--mismatch';
}

/** Eight-dimension match breakdown with accessible meters, status badges, toggletips, and raw-value sentences (spec 057). */
export function ScoreBreakdown({ dimensions, heading = 'Rincian kecocokan', deltas, onRecalculate }: Props) {
  const ordered = orderedDimensions(dimensions);
  if (!ordered.length) {
    return (
      <section className="tr-stack" aria-label={t(heading)}>
        <h4 className="tr-sys-type-label">{t(heading)}</h4>
        <p className="tr-muted">{t('Hitung ulang untuk melihat rincian')}</p>
        {onRecalculate ? (
          <div className="tr-row">
            <Button onClick={onRecalculate}>{t('Hitung ulang')}</Button>
          </div>
        ) : null}
      </section>
    );
  }

  return (
    <section className="tr-stack" aria-label={t(heading)}>
      <h4 className="tr-sys-type-label">{t(heading)}</h4>
      <ul className="tr-breakdown">
        {ordered.map((dimension) => {
          const meta = DIMENSION_META[dimension.id];
          const delta = deltas?.[dimension.id];
          const scoreLabel =
            dimension.score !== null
              ? `${dimension.score}%`
              : dimension.status === 'NOT_APPLICABLE'
                ? t('Tidak berlaku')
                : t('Belum diketahui');
          const changed = delta && delta.before !== delta.after && delta.before !== null && delta.after !== null;
          return (
            <li key={dimension.id} className="tr-breakdown__row">
              <div className="tr-breakdown__head">
                <span className="tr-breakdown__label tr-sys-type-support-strong">
                  <span>{t(meta.label)}</span>
                  <Toggletip label={meta.label}>{t(meta.help)}</Toggletip>
                </span>
                <span className="tr-breakdown__meta">
                  <span className="tr-sys-type-support-strong">{scoreLabel}</span>
                  {changed ? (
                    <span className="tr-tag tr-sys-type-support">
                      {t('{label} {before} → {after}', { label: t(meta.label), before: delta.before!, after: delta.after! })}
                    </span>
                  ) : null}
                  <Status tone={dimensionTone(dimension.status)} icon={null} label={t(DIMENSION_STATUS_LABEL[dimension.status])} />
                </span>
              </div>
              {dimension.score !== null ? (
                <div
                  className="tr-meter"
                  role="progressbar"
                  aria-label={t(meta.label)}
                  aria-valuenow={dimension.score}
                  aria-valuemin={0}
                  aria-valuemax={100}>
                  <div className={fillClass(dimension.status)} style={{ width: `${dimension.score}%` }} />
                </div>
              ) : (
                <div className="tr-meter tr-meter--unknown" aria-hidden="true" />
              )}
              <p className="tr-muted tr-sys-type-support">{dimensionSentence(dimension)}</p>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

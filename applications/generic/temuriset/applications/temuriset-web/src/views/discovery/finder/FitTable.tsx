'use client';

import NextLink from 'next/link';
import { useEffect, useRef, useState } from 'react';

import { ImprovementList } from '@/components/tr/ImprovementList';
import { ScoreBreakdown } from '@/components/tr/ScoreBreakdown';
import { Status } from '@/components/tr/Status';
import { Toggletip } from '@/components/tr/Toggletip';
import { DIMENSION_META, type Dimension } from '@/features/discovery/breakdown';
import { fitRowAction, sortFitItems, topDimensions, type FitItem } from '@/features/discovery/fit';
import { matchesHref, score } from '@/features/discovery/model';
import {
  deltasFor,
  readSavedScores,
  scoresOf,
  writeSavedScores,
  type Recommendation,
  type SavedScores,
} from '@/features/discovery/recommendations';
import { t } from '@/features/i18n/t';
import { labelTone } from '@/views/discovery/MatchCard';

type Props = {
  items: FitItem[];
  returnTo: string;
};

/** Product × mandate matrix with native keyboard-accessible `<details>` expansion for breakdown & recommendations (spec 059). */
const SAVED_KEY = 'tr_fit_prev';

function rowKey(item: FitItem): string {
  return `${item.invention.id}:${item.opportunity.id}`;
}

export function FitTable({ items, returnTo }: Props) {
  const ordered = sortFitItems(items);
  // Read after mount: the server render has no sessionStorage, and reading it during render would break hydration.
  const [previous, setPrevious] = useState<SavedScores | null>(null);
  const compared = useRef<string | null>(null);
  const rows = items.map(rowKey).join(',');
  useEffect(() => {
    // Compare once per set of rows; a re-render must not overwrite the saved scores and hide the change.
    if (compared.current === rows) return;
    compared.current = rows;
    const saved = readSavedScores(SAVED_KEY);
    setPrevious(saved);
    const current = scoresOf(
      items.map((item) => ({ opportunity_id: rowKey(item), breakdown: (item.result.breakdown ?? []) as Dimension[] })),
    );
    writeSavedScores(SAVED_KEY, { ...saved, ...current });
  }, [items, rows]);
  return (
    <div className="tr-stack">
      <h4 className="tr-sys-type-heading-sm">{t('Kecocokan dengan produk Anda')}</h4>
      <ul className="tr-stack">
        {ordered.map((item) => {
          const breakdown = (item.result.breakdown ?? []) as Dimension[];
          const recommendations = (item.result.recommendations ?? []) as Recommendation[];
          const top = topDimensions(breakdown, 2);
          const action = fitRowAction(item, returnTo);
          const lower = score(item.result.fit.lower, 'lower');
          const upper = score(item.result.fit.upper, 'upper');
          const key = `${item.invention.id}-${item.opportunity.id}`;
          const deltas = deltasFor(previous, rowKey(item), breakdown);
          const changed = Object.entries(deltas) as [Dimension['id'], { before: number | null; after: number | null }][];
          return (
            <li key={key} className="tr-panel tr-stack">
              {item.preview ? (
                <div className="tr-row">
                  <Status tone="warning" icon={null} label={t('Pratinjau tanpa kebutuhan')} />
                  <Toggletip label="Pratinjau tanpa kebutuhan">
                    {t(
                      'Skor dihitung dari profil produk yang terbit saja, sehingga dana dan bentuk kerja sama belum diketahui. Buat kebutuhan dukungan untuk penilaian penuh dan pitching.',
                    )}
                  </Toggletip>
                </div>
              ) : null}
              <details className="tr-disclosure">
                <summary className="tr-disclosure__toggle">
                  <div className="tr-stack">
                    <div className="tr-row">
                      <strong className="tr-sys-type-body-strong">{item.invention.title}</strong>
                      {item.invention.tkt_level ? (
                        <span className="tr-tag tr-sys-type-support">{t('TKT {n}', { n: item.invention.tkt_level })}</span>
                      ) : null}
                      <span className="tr-muted tr-sys-type-support">{item.opportunity.title}</span>
                    </div>
                    <div className="tr-row">
                      <Status tone={labelTone(item.result)} icon={null} label={t(item.result.label)} />
                      <span className="tr-sys-type-support-strong">{`${lower}–${upper}`}</span>
                    </div>
                    {top.length ? (
                      <div className="tr-row">
                        {top.map((dim) => (
                          <span key={dim.id} className="tr-tag tr-sys-type-support">
                            {`${t(dim.label)} ${dim.score}%`}
                          </span>
                        ))}
                      </div>
                    ) : null}
                    {changed.length ? (
                      <div className="tr-row" role="status">
                        {changed.map(([id, delta]) => (
                          <span key={id} className="tr-tag tr-sys-type-support-strong">
                            {t('{label} {before} → {after}', {
                              label: t(DIMENSION_META[id].label),
                              before: delta.before!,
                              after: delta.after!,
                            })}
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </div>
                </summary>
                <div className="tr-disclosure__body tr-stack">
                  <ScoreBreakdown dimensions={breakdown} deltas={deltas} />
                  <ImprovementList recommendations={recommendations} returnTo={returnTo} />
                  <div className="tr-row">
                    <NextLink
                      className={`tr-btn ${action.primary ? 'tr-btn--primary' : 'tr-btn--secondary'}`}
                      href={action.href}>
                      {action.label}
                    </NextLink>
                    {item.source ? (
                      <NextLink className="tr-link" href={matchesHref({ type: item.source.type, id: item.source.id })}>
                        {t('Lihat semua investor untuk kebutuhan ini')}
                      </NextLink>
                    ) : null}
                  </div>
                </div>
              </details>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

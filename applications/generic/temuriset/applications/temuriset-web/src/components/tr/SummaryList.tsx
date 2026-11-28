import type { ReactNode } from 'react';
import { tx } from '@/features/i18n/t';

export type SummaryRow = { id: string; label: string; value: ReactNode; changeHref?: string };

/** Port of TR.SummaryList: check-your-answers rows, each with a contextual change link. */
export function SummaryList({ rows }: { rows: SummaryRow[] }) {
  return (
    <dl className="tr-summary">
      {rows.map((row) => (
        <div key={row.id} className="tr-summary__row">
          <dt className="tr-sys-type-label">{tx(row.label)}</dt>
          <dd className="tr-summary__value">{row.value}</dd>
          {row.changeHref ? (
            <dd className="tr-summary__change">
              <a className="tr-link" href={row.changeHref}>
                Ubah<span className="tr-sr"> {row.label.toLowerCase()}</span>
              </a>
            </dd>
          ) : null}
        </div>
      ))}
    </dl>
  );
}

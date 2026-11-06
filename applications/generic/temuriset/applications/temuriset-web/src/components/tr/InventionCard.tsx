import type { ReactNode } from 'react';

import { Icon } from '@/components/tr/Icon';

type InventionCardProps = {
  title: string;
  category?: string;
  manager?: string;
  problem?: string;
  solution?: string;
  maturity?: string;
  support?: string;
  facts?: ReactNode;
  reasons?: string[];
  action?: ReactNode;
  headingLevel?: 2 | 3;
};

/** Port of TR.InventionCard. Pass an authorized projection only: nothing private belongs on a card. */
export function InventionCard({ title, category, manager, problem, solution, maturity, support, facts, reasons, action, headingLevel = 3 }: InventionCardProps) {
  const rows = [
    ['Masalah', problem],
    ['Solusi saat ini', solution],
    ['Tahap', maturity],
    ['Dukungan dicari', support],
  ].filter((row): row is [string, string] => Boolean(row[1]));
  const Heading = headingLevel === 2 ? 'h2' : 'h3';
  return (
    <article className="tr-card">
      <div className="tr-art">
        <Icon name="bulb" />
        <span className="tr-sys-type-support-strong">{category || 'Inovasi'}</span>
      </div>
      <div className="tr-card__body">
        <Heading className="tr-sys-type-heading-sm">{title}</Heading>
        {manager ? <p className="tr-muted tr-sys-type-support">{manager}</p> : null}
        {rows.length ? (
          <dl className="tr-facts">
            {rows.map(([label, value]) => (
              <div key={label}>
                <dt className="tr-sys-type-support-strong">{label}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        ) : null}
        {facts}
        {reasons?.length ? (
          <ul className="tr-reasons">
            {reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        ) : null}
        {action ? <div className="tr-row">{action}</div> : null}
      </div>
    </article>
  );
}

import type { ReactNode } from 'react';

import { FinancialScope } from '@/components/tr/FinancialScope';
import { Icon } from '@/components/tr/Icon';

type FundingRequestCardProps = {
  company: string;
  proposedEntity?: boolean;
  stage?: string;
  form?: string;
  purpose?: string;
  currency?: string | null;
  target?: string | null;
  desiredMin?: string | null;
  desiredMax?: string | null;
  partialAccepted?: boolean;
  /** Linked invention titles, or links to them. */
  inventions?: ReactNode[];
  reasons?: string[];
  gap?: ReactNode;
  action?: ReactNode;
  headingLevel?: 2 | 3;
};

/** Port of TR.FundingRequestCard: one company raise, even when several inventions support it (UX-06). */
export function FundingRequestCard(props: FundingRequestCardProps) {
  const linked = props.inventions ?? [];
  const Heading = props.headingLevel === 2 ? 'h2' : 'h3';
  const rows = [
    ['Tahap pendanaan', props.stage],
    ['Bentuk', props.form],
    ['Tujuan', props.purpose],
  ].filter((row): row is [string, string] => Boolean(row[1]));
  return (
    <article className="tr-card">
      <div className="tr-art">
        <Icon name="building" />
        <span className="tr-sys-type-support-strong">Pendanaan Perusahaan</span>
      </div>
      <div className="tr-card__body">
        <Heading className="tr-sys-type-heading-sm">{props.company}</Heading>
        <p className="tr-muted tr-sys-type-support">
          {props.proposedEntity ? 'Perusahaan belum didirikan' : 'Badan usaha telah disebutkan, status pemeriksaan ditampilkan terpisah'}
        </p>
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
        <FinancialScope compact subject="companyTarget" currency={props.currency} min={props.target} max={props.target} />
        <FinancialScope compact subject="contribution" currency={props.currency} min={props.desiredMin} max={props.desiredMax} />
        {props.partialAccepted ? <p className="tr-sys-type-support">Menerima pendanaan sebagian dan bersama investor lain.</p> : null}
        <p className="tr-sys-type-label">{`${linked.length} inovasi terkait`}</p>
        {linked.length ? (
          <ul className="tr-reasons tr-reasons--plain">
            {linked.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        ) : null}
        {props.reasons?.length ? (
          <ul className="tr-reasons">
            {props.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        ) : null}
        {props.gap}
        {props.action ? <div className="tr-row">{props.action}</div> : null}
      </div>
    </article>
  );
}

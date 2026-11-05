import type { ReactNode } from 'react';

import { range } from '@/features/money';

export type FinancialSubject = 'project' | 'companyTarget' | 'contribution' | 'investorCheck' | 'partner' | 'license';

const SUBJECT: Record<FinancialSubject, string> = {
  project: 'Dukungan Proyek',
  companyTarget: 'Target Pendanaan',
  contribution: 'Kisaran kontribusi per investor',
  investorCheck: 'Kisaran investasi investor',
  partner: 'Kisaran dukungan mitra',
  license: 'Ketentuan lisensi',
};

type FinancialScopeProps = {
  subject: FinancialSubject;
  currency?: string | null;
  /** Decimal strings from the service; `null` means unknown, never zero. */
  min?: string | null;
  max?: string | null;
  period?: string;
  scope?: string;
  /** ISO date. */
  estimateDate?: string | null;
  assumptions?: string;
  noncash?: string;
  terms?: string;
  compact?: boolean;
  edit?: ReactNode;
  label?: string;
};

function longDate(iso: string): string {
  return new Intl.DateTimeFormat('id-ID', { timeZone: 'Asia/Jakarta', day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(iso));
}

/** Port of TR.FinancialScope: an amount that always says what it is an amount of (UX-05). */
export function FinancialScope({ subject, currency, min, max, period, scope, estimateDate, assumptions, noncash, terms, compact, edit, label }: FinancialScopeProps) {
  const main = noncash || terms || range(currency, min, max);
  return (
    <div className={compact ? 'tr-fin tr-fin--compact' : 'tr-fin'}>
      <p className="tr-fin__subject tr-sys-type-support-strong">{label || SUBJECT[subject]}</p>
      <p className="tr-fin__line">
        <span className="tr-fin__amount tr-sys-type-amount">{main}</span>
        {period ? <span className="tr-fin__period">{` selama ${period}`}</span> : null}
      </p>
      {scope ? <p className="tr-muted tr-sys-type-support">{`Cakupan: ${scope}`}</p> : null}
      {estimateDate ? <p className="tr-muted tr-sys-type-support">{`Perkiraan per ${longDate(estimateDate)}`}</p> : null}
      {assumptions ? <p className="tr-muted tr-sys-type-support">{`Asumsi: ${assumptions}`}</p> : null}
      {edit ? <div className="tr-fin__edit">{edit}</div> : null}
    </div>
  );
}

import { useId, type ReactNode } from 'react';

import { Status } from '@/components/tr/Status';
import { tx } from '@/features/i18n/t';

type NextStepProps = { who: 'you' | 'other'; title: string; children?: ReactNode; action?: ReactNode };

/** Port of TR.NextStep: whose turn it is, one sentence and one action. */
export function NextStep({ who, title, children, action }: NextStepProps) {
  const mine = who === 'you';
  const headingId = useId();
  return (
    <section className={mine ? 'tr-next tr-next--you' : 'tr-next'} aria-labelledby={headingId}>
      <Status tone={mine ? 'action' : 'neutral'} label={mine ? 'Menunggu Anda' : 'Menunggu pihak lain'} />
      <h2 id={headingId} className="tr-sys-type-heading-sm">
        {tx(title)}
      </h2>
      {children ? <p>{tx(children)}</p> : null}
      {action ? <div className="tr-row">{action}</div> : null}
    </section>
  );
}

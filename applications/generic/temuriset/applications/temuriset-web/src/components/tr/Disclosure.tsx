import type { ReactNode } from 'react';

import { Icon } from '@/components/tr/Icon';
import { tx } from '@/features/i18n/t';

type DisclosureProps = { label: ReactNode; children: ReactNode; defaultOpen?: boolean };

/** Port of TR.Disclosure: native details, so it works before hydration and with the keyboard. */
export function Disclosure({ label, children, defaultOpen }: DisclosureProps) {
  return (
    <details className="tr-disclosure" open={defaultOpen}>
      <summary className="tr-disclosure__toggle tr-sys-type-label">
        <Icon name="right" className="tr-disclosure__chev" />
        <span>{tx(label)}</span>
      </summary>
      <div className="tr-disclosure__body">{children}</div>
    </details>
  );
}

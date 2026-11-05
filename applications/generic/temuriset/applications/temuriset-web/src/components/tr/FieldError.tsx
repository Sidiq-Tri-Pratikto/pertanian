import type { ReactNode } from 'react';

import { Icon } from '@/components/tr/Icon';

/** Port of TR.FieldError: one plain correction tied to a field. The same words appear in the ErrorSummary. */
export function FieldError({ id, code, children }: { id: string; code?: string; children: ReactNode }) {
  return (
    <p id={id} className="tr-field-error tr-sys-type-label" data-code={code}>
      <Icon name="alert" size="small" />
      <span>
        <span className="tr-sr">Kesalahan: </span>
        {children}
      </span>
    </p>
  );
}

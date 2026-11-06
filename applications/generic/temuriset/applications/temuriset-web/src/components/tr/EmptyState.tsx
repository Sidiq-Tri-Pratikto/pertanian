import type { ReactNode } from 'react';

import { Icon, type IconName } from '@/components/tr/Icon';

type EmptyStateProps = { title: string; icon: IconName; children: ReactNode; action?: ReactNode };

/** Port of TR.EmptyState: says what is missing and offers the next useful step, never empty analytics. */
export function EmptyState({ title, icon, children, action }: EmptyStateProps) {
  return (
    <div className="tr-empty">
      <Icon name={icon} />
      <h2 className="tr-sys-type-heading-sm">{title}</h2>
      <p>{children}</p>
      {action ? <div className="tr-row tr-row--center">{action}</div> : null}
    </div>
  );
}

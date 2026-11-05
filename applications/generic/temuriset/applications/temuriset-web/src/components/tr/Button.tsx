'use client';

import { useId, type MouseEvent, type ReactNode } from 'react';

import { Icon, type IconName } from '@/components/tr/Icon';

type ButtonProps = {
  children: ReactNode;
  intent?: 'primary' | 'secondary' | 'danger';
  type?: 'button' | 'submit';
  icon?: IconName;
  /** Shows the busy label; repeat clicks are ignored. Never announces success. */
  busy?: boolean;
  busyLabel?: string;
  /** Non-empty means disabled. The control stays focusable and the reason stays visible and linked. */
  disabledReason?: string | null;
  onClick?: (event: MouseEvent<HTMLButtonElement>) => void;
};

/** Port of TR.Button: one primary action per task region. */
export function Button({ children, intent = 'secondary', type = 'button', icon, busy, busyLabel, disabledReason, onClick }: ButtonProps) {
  const reasonId = `${useId()}-reason`;
  const blocked = Boolean(disabledReason);
  const button = (
    <button
      type={type}
      className={`tr-btn tr-btn--${intent}`}
      aria-disabled={blocked || undefined}
      aria-busy={busy || undefined}
      aria-describedby={blocked ? reasonId : undefined}
      onClick={(event) => {
        if (blocked || busy) {
          event.preventDefault();
          return;
        }
        onClick?.(event);
      }}>
      {busy ? <span className="tr-spinner" aria-hidden="true" /> : icon ? <Icon name={icon} /> : null}
      <span>{busy ? (busyLabel ?? 'Memproses…') : children}</span>
    </button>
  );
  if (!blocked) return button;
  return (
    <span className="tr-btn-wrap">
      {button}
      <span id={reasonId} className="tr-reason tr-sys-type-support">
        {disabledReason}
      </span>
    </span>
  );
}

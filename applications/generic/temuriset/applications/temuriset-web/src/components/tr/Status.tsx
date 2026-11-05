import type { ReactNode } from 'react';

import { Icon, type IconName } from '@/components/tr/Icon';

export type Tone = 'neutral' | 'success' | 'danger' | 'warning' | 'action';

const TONE_ICON: Record<Tone, IconName> = { neutral: 'clock', success: 'check', danger: 'cross', warning: 'question', action: 'arrow' };

type StatusProps = {
  label: string;
  tone?: Tone;
  /** `null` drops the icon; the label alone still carries the meaning. */
  icon?: IconName | null;
  /** Adds a notice body under the label. */
  children?: ReactNode;
  live?: boolean | 'alert';
};

/** Port of TR.Status: a state label that never relies on colour alone. */
export function Status({ label, tone = 'neutral', icon, children, live }: StatusProps) {
  const shown = icon === null ? null : (icon ?? TONE_ICON[tone]);
  const role = live === 'alert' ? 'alert' : live ? 'status' : undefined;
  const tag = (
    <span className={`tr-status tr-status--${tone}`}>
      {shown ? <Icon name={shown} size="small" /> : null}
      <span>{label}</span>
    </span>
  );
  if (!children) {
    return (
      <span className="tr-status-wrap" role={role}>
        {tag}
      </span>
    );
  }
  return (
    <div className={`tr-notice tr-notice--${tone}`} role={role}>
      {tag}
      <div className="tr-notice__body">{children}</div>
    </div>
  );
}

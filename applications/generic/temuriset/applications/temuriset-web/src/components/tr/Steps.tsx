'use client';

import { Icon } from '@/components/tr/Icon';
import { t } from '@/features/i18n/t';

export type Step = { id: string; label: string; done?: boolean };

type StepsProps = { steps: Step[]; current: string; onSelect?: (id: string) => void; label?: string };

/** Port of TR.Steps: where the person is in a task, with done steps marked in words as well as a check. */
export function Steps({ steps, current, onSelect, label }: StepsProps) {
  const index = steps.findIndex((step) => step.id === current);
  return (
    <nav className="tr-steps" aria-label={t(label ?? 'Langkah pengisian')}>
      <p className="tr-sys-type-label">{t('Langkah {n} dari {total}: {label}', { n: index + 1, total: steps.length, label: t(steps[index]?.label ?? '') })}</p>
      <ol className="tr-steps__list">
        {steps.map((step, position) => {
          const done = position < index || Boolean(step.done);
          const on = position === index;
          const inner = (
            <>
              <span className="tr-steps__mark">{done && !on ? <Icon name="check" size="small" /> : position + 1}</span>
              <span className="tr-steps__text tr-sys-type-support">
                {t(step.label)}
                {done && !on ? <span className="tr-sr">{` (${t('selesai')})`}</span> : null}
              </span>
            </>
          );
          return (
            <li key={step.id} className={['tr-steps__item', on ? 'is-current' : '', done ? 'is-done' : ''].filter(Boolean).join(' ')}>
              {onSelect && !on ? (
                <button type="button" className="tr-steps__btn" onClick={() => onSelect(step.id)}>
                  {inner}
                </button>
              ) : (
                <span className="tr-steps__btn" aria-current={on ? 'step' : undefined}>
                  {inner}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

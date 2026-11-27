'use client';

import type { ReactNode } from 'react';

import { FieldError } from '@/components/tr/FieldError';
import { useMessages } from '@/features/i18n/LocaleProvider';
import { tx } from '@/features/i18n/t';

type Choice = { value: string; label: string; hint?: string };

type ChoiceGroupProps = {
  legend: ReactNode;
  /** Form field name; option ids derive from it. */
  name: string;
  options: Choice[];
  defaultValue?: string;
  hint?: string;
  required?: boolean;
  error?: string;
  /** Controlled mode: the chosen value and its change handler. */
  value?: string;
  onChange?: (value: string) => void;
};

/**
 * Port of TR.ChoiceGroup. Uncontrolled by default, so a server action receives the value without JavaScript; pass
 * `value` and `onChange` to control it.
 * Selection styling comes from `:has(:checked)` in `src/design/app.css`, which mirrors `.is-selected`.
 */
export function ChoiceGroup({ legend, name, options, defaultValue, hint, required, error, value, onChange }: ChoiceGroupProps) {
  const words = useMessages().components;
  const hintId = `${name}-hint`;
  const errorId = `${name}-error`;
  const describedBy = [hint ? hintId : null, error ? errorId : null].filter(Boolean).join(' ') || undefined;
  return (
    <fieldset className={error ? 'tr-fieldset tr-fieldset--error' : 'tr-fieldset'} aria-describedby={describedBy} aria-invalid={error ? true : undefined}>
      <legend className="tr-field__label tr-sys-type-label">
        {tx(legend)}
        {required ? <span className="tr-field__req tr-sys-type-support">{words.required}</span> : null}
      </legend>
      {hint ? (
        <p id={hintId} className="tr-field__hint tr-sys-type-support">
          {tx(hint)}
        </p>
      ) : null}
      {error ? <FieldError id={errorId}>{tx(error)}</FieldError> : null}
      <div className="tr-choices">
        {options.map((option) => {
          const id = `${name}-${option.value}`;
          return (
            <label key={option.value} htmlFor={id} className="tr-choice">
              <input
                type="radio"
                id={id}
                name={name}
                value={option.value}
                required={required}
                {...(onChange ? { checked: option.value === value, onChange: () => onChange(option.value) } : { defaultChecked: option.value === defaultValue })}
              />
              <span className="tr-choice__body">
                <span className="tr-sys-type-label">{tx(option.label)}</span>
                {option.hint ? <span className="tr-choice__hint tr-sys-type-support">{option.hint}</span> : null}
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

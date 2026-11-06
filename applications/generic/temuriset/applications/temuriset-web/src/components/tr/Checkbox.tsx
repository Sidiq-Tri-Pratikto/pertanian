'use client';

import { useId, type ReactNode } from 'react';

import { FieldError } from '@/components/tr/FieldError';

type CheckboxProps = {
  label: ReactNode;
  checked: boolean;
  onChange: (checked: boolean) => void;
  hint?: ReactNode;
  disabledReason?: string;
  error?: string;
  id?: string;
  name?: string;
};

/** Port of TR.Checkbox: one independent yes or no; consent stays unchecked until really given. */
export function Checkbox({ label, checked, onChange, hint, disabledReason, error, id, name }: CheckboxProps) {
  const auto = useId();
  const inputId = id ?? auto;
  const blocked = Boolean(disabledReason);
  return (
    <label htmlFor={inputId} className={['tr-choice', checked && 'is-selected', blocked && 'is-disabled'].filter(Boolean).join(' ')}>
      <input
        type="checkbox"
        id={inputId}
        name={name}
        checked={checked}
        disabled={blocked}
        aria-invalid={error ? true : undefined}
        onChange={(event) => onChange(event.target.checked)}
      />
      <span className="tr-choice__body">
        <span className="tr-sys-type-label">{label}</span>
        {hint ? <span className="tr-choice__hint tr-sys-type-support">{hint}</span> : null}
        {blocked ? <span className="tr-choice__hint tr-sys-type-support">{disabledReason}</span> : null}
        {error ? <FieldError id={`${inputId}-error`}>{error}</FieldError> : null}
      </span>
    </label>
  );
}

/** `Checkbox.Group`: a fieldset and legend around related checkboxes. */
export function CheckboxGroup({ legend, hint, error, id, children }: { legend: ReactNode; hint?: ReactNode; error?: string; id?: string; children: ReactNode }) {
  const auto = useId();
  const errorId = `${id ?? auto}-error`;
  return (
    <fieldset id={id} tabIndex={id ? -1 : undefined} className={error ? 'tr-fieldset tr-fieldset--error' : 'tr-fieldset'} aria-invalid={error ? true : undefined} aria-describedby={error ? errorId : undefined}>
      <legend className="tr-field__label tr-sys-type-label">{legend}</legend>
      {hint ? <p className="tr-field__hint tr-sys-type-support">{hint}</p> : null}
      {error ? <FieldError id={errorId}>{error}</FieldError> : null}
      <div className="tr-choices">{children}</div>
    </fieldset>
  );
}

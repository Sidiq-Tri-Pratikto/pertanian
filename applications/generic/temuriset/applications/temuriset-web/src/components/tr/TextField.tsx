'use client';

import { useId, type ReactNode } from 'react';

import { Field, fieldIds } from '@/components/tr/Field';

type TextFieldProps = {
  label: ReactNode;
  value: string;
  onChange: (value: string) => void;
  hint?: ReactNode;
  required?: boolean;
  error?: ReactNode;
  errorCode?: string;
  type?: 'text' | 'email' | 'decimal' | 'date';
  id?: string;
  name?: string;
  autoComplete?: string;
  inputMode?: 'numeric' | 'text';
};

/** Port of TR.TextField: a labelled input that keeps its value on error. Decimal stays text, so empty never becomes 0. */
export function TextField({ label, value, onChange, hint, required, error, errorCode, type = 'text', id, name, autoComplete, inputMode }: TextFieldProps) {
  const auto = useId();
  const ids = fieldIds(id ?? auto, hint, error);
  const decimal = type === 'decimal';
  return (
    <Field ids={ids} label={label} hint={hint} error={error} errorCode={errorCode} required={required}>
      <input
        id={ids.id}
        name={name}
        value={value}
        className="tr-input"
        type={decimal ? 'text' : type}
        inputMode={decimal ? 'decimal' : inputMode}
        autoComplete={autoComplete ?? 'off'}
        required={required || undefined}
        aria-invalid={error ? true : undefined}
        aria-describedby={ids.describedBy}
        onChange={(event) => onChange(event.target.value)}
      />
    </Field>
  );
}

'use client';

import { useId, type ReactNode } from 'react';

import { Field, fieldIds } from '@/components/tr/Field';

export type SelectOption = { value: string; label: string; disabledReason?: string };

type SelectProps = {
  label: ReactNode;
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  /** `null` removes the empty choice. */
  emptyLabel?: string | null;
  hint?: ReactNode;
  required?: boolean;
  error?: ReactNode;
  id?: string;
  name?: string;
};

/** Port of TR.Select: native selection with a visible empty choice unless the caller removes it. */
export function Select({ label, value, onChange, options, emptyLabel, hint, required, error, id, name }: SelectProps) {
  const auto = useId();
  const ids = fieldIds(id ?? auto, hint, error);
  return (
    <Field ids={ids} label={label} hint={hint} error={error} required={required}>
      <select
        id={ids.id}
        name={name}
        value={value}
        className="tr-input tr-select"
        required={required || undefined}
        aria-invalid={error ? true : undefined}
        aria-describedby={ids.describedBy}
        onChange={(event) => onChange(event.target.value)}>
        {emptyLabel !== null ? <option value="">{emptyLabel ?? 'Pilih salah satu'}</option> : null}
        {options.map((option) => (
          <option key={option.value} value={option.value} disabled={Boolean(option.disabledReason)}>
            {option.label + (option.disabledReason ? ` — ${option.disabledReason}` : '')}
          </option>
        ))}
      </select>
    </Field>
  );
}

'use client';

import { useId, type ReactNode } from 'react';

import { Field, fieldIds } from '@/components/tr/Field';

type TextAreaProps = {
  label: ReactNode;
  value: string;
  onChange: (value: string) => void;
  hint?: ReactNode;
  required?: boolean;
  error?: ReactNode;
  rows?: number;
  /** Shows a live count; going over is stated in words, not colour alone. */
  limit?: number;
  id?: string;
};

/** Port of TR.TextArea. */
export function TextArea({ label, value, onChange, hint, required, error, rows = 5, limit, id }: TextAreaProps) {
  const auto = useId();
  const ids = fieldIds(id ?? auto, hint, error);
  const countId = `${ids.id}-count`;
  const over = limit !== undefined && value.length > limit;
  return (
    <Field ids={ids} label={label} hint={hint} error={error} required={required}>
      <textarea
        id={ids.id}
        value={value}
        rows={rows}
        className="tr-input tr-textarea"
        required={required || undefined}
        aria-invalid={error ? true : undefined}
        aria-describedby={[ids.describedBy, limit ? countId : null].filter(Boolean).join(' ') || undefined}
        onChange={(event) => onChange(event.target.value)}
      />
      {limit ? (
        <p id={countId} className={over ? 'tr-count tr-sys-type-support is-over' : 'tr-count tr-sys-type-support'}>
          {over ? `Lebih ${value.length - limit} karakter dari batas ${limit}` : `${value.length} dari ${limit} karakter`}
        </p>
      ) : null}
    </Field>
  );
}

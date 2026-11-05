import type { ReactNode } from 'react';

import { FieldError } from '@/components/tr/FieldError';

export type FieldIds = { id: string; hintId: string; errorId: string; describedBy: string | undefined };

/** Port of the bundle's `useField`: the ids that tie a label, hint and error to one control. */
export function fieldIds(id: string, hint?: ReactNode, error?: ReactNode): FieldIds {
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;
  const describedBy = [hint ? hintId : null, error ? errorId : null].filter(Boolean).join(' ') || undefined;
  return { id, hintId, errorId, describedBy };
}

type FieldProps = {
  ids: FieldIds;
  label: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
  errorCode?: string;
  required?: boolean;
  children: ReactNode;
};

/** Port of the bundle's `Field`: visible label, requiredness, hint and inline error around one control. */
export function Field({ ids, label, hint, error, errorCode, required, children }: FieldProps) {
  return (
    <div className={error ? 'tr-field tr-field--error' : 'tr-field'}>
      <label className="tr-field__label tr-sys-type-label" htmlFor={ids.id}>
        {label}
        {required ? <span className="tr-field__req tr-sys-type-support"> (wajib)</span> : null}
      </label>
      {hint ? (
        <p id={ids.hintId} className="tr-field__hint tr-sys-type-support">
          {hint}
        </p>
      ) : null}
      {error ? (
        <FieldError id={ids.errorId} code={errorCode}>
          {error}
        </FieldError>
      ) : null}
      {children}
    </div>
  );
}

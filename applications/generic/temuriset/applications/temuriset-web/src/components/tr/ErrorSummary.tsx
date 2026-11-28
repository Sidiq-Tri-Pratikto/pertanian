'use client';

import { useEffect, useRef, type ReactNode } from 'react';

import { Button } from '@/components/tr/Button';
import { useMessages } from '@/features/i18n/LocaleProvider';
import { t } from '@/features/i18n/t';

type ErrorSummaryProps = {
  errors?: { fieldId: string; message: string }[];
  /** Change it on each failed attempt; focus moves only then, so a background save never steals it. */
  focusKey?: number | string;
  title?: string;
  children?: ReactNode;
  retry?: { label: string; onClick: () => void };
  id?: string;
};

/** Port of TR.ErrorSummary: what stopped a submission, each item linked to its field. */
export function ErrorSummary({ errors = [], focusKey, title, children, retry, id = 'tr-errors' }: ErrorSummaryProps) {
  const words = useMessages().components;
  const region = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (focusKey) region.current?.focus();
  }, [focusKey]);
  return (
    <div ref={region} tabIndex={-1} className="tr-error-summary" role="group" aria-labelledby={`${id}-t`} id={id}>
      <h2 id={`${id}-t`} className="tr-sys-type-heading-sm">
        {title ? t(title) : words.errorSummary}
      </h2>
      {errors.length ? (
        <ul className="tr-error-summary__list">
          {errors.map((error) => (
            <li key={error.fieldId}>
              <a
                className="tr-link"
                href={`#${error.fieldId}`}
                onClick={(event) => {
                  event.preventDefault();
                  const field = document.getElementById(error.fieldId);
                  field?.focus();
                  field?.scrollIntoView({ block: 'center' });
                }}>
                {t(error.message)}
              </a>
            </li>
          ))}
        </ul>
      ) : null}
      {children ? <p>{children}</p> : null}
      {retry ? (
        <div className="tr-row">
          <Button intent="secondary" icon="refresh" onClick={retry.onClick}>
            {retry.label}
          </Button>
        </div>
      ) : null}
    </div>
  );
}

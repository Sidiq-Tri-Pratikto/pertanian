'use client';

import type { ApiError } from '@/api/errors';
import { ErrorSummary } from '@/components/tr/ErrorSummary';

export function RelationshipError({ error, prefix }: { error: { failure: ApiError; attempt: number }; prefix: string }) {
  const { failure, attempt } = error;
  return (
    <ErrorSummary
      id={`${prefix}-error`}
      focusKey={attempt}
      title={failure.message}
      errors={failure.details.flatMap(({ loc, msg }) => {
        const field = loc.at(-1);
        return typeof field === 'string' ? [{ fieldId: `${prefix}-${field}`, message: msg }] : [];
      })}>
      {failure.requestId ? `ID referensi: ${failure.requestId}` : null}
    </ErrorSummary>
  );
}

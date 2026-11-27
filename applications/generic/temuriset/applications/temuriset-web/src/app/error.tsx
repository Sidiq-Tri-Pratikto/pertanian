'use client';

import { Button } from '@/components/tr/Button';
import { EmptyState } from '@/components/tr/EmptyState';
import { useMessages } from '@/features/i18n/LocaleProvider';

/** Shown when a page could not reach the service; nothing the visitor typed is lost by retrying. */
export default function ErrorPage({ reset }: { reset: () => void }) {
  const words = useMessages().errorPage;
  return (
    <main id="isi" className="tr-root tr-page tr-section">
      <h1 className="tr-sys-type-display">{words.title}</h1>
      <EmptyState icon="alert" title={words.heading} action={<Button icon="refresh" onClick={reset}>{words.retry}</Button>}>
        {words.body}
      </EmptyState>
    </main>
  );
}

import Link from 'next/link';

import { EmptyState } from '@/components/tr/EmptyState';
import { localHref } from '@/features/i18n/locale';
import { messagesFor } from '@/features/i18n/messages';
import { serverLocale } from '@/features/i18n/server';

export default async function NotFound() {
  const locale = await serverLocale();
  const words = messagesFor(locale).notFound;
  return (
    <main id="isi" className="tr-root tr-page tr-section">
      <h1 className="tr-sys-type-display">{words.title}</h1>
      <EmptyState
        icon="question"
        title={words.heading}
        action={
          <Link className="tr-link" href={localHref(locale, '/')}>
            {words.home}
          </Link>
        }>
        {words.body}
      </EmptyState>
    </main>
  );
}

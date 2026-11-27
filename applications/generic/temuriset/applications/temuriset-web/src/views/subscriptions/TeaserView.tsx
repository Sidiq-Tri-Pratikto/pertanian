import Link from 'next/link';

import { EmptyState } from '@/components/tr/EmptyState';
import type { Teaser } from '@/features/subscriptions/api';
import { AuthShell } from '@/views/AuthShell';
import type { Locale } from '@/features/i18n/locale';
import { localHref } from '@/features/i18n/locale';
import { messagesFor, sectorLabel, stageLabel } from '@/features/i18n/messages';

/**
 * The brief public summary an investor opens from an email. Anything more needs a normal signup. Inventor content is
 * shown as written; on an English page it carries `lang="id"` and a "Written in Indonesian" label (spec 050).
 */
export function TeaserView({ teaser, locale = 'id' }: { teaser: Teaser | null; locale?: Locale }) {
  const messages = messagesFor(locale);
  const words = messages.teaser;
  if (!teaser) {
    return (
      <AuthShell title={words.unavailableTitle}>
        <EmptyState
          icon="question"
          title={words.unavailableHeading}
          action={
            <Link className="tr-link" href={localHref(locale, '/langganan')}>
              {words.unavailableAction}
            </Link>
          }>
          {words.unavailableBody}
        </EmptyState>
      </AuthShell>
    );
  }
  const detail = `/inventions/${teaser.id}`;
  const content = locale === 'en' ? 'id' : undefined;
  return (
    <AuthShell title={teaser.title} subtitle={words.inventor(teaser.inventor_name)}>
      <section className="tr-panel tr-stack" aria-labelledby="ringkasan">
        <h2 id="ringkasan" className="tr-sys-type-heading-sm">
          {words.summary}
        </h2>
        {content ? <p className="tr-muted tr-sys-type-support">{words.writtenIn}</p> : null}
        <p lang={content}>{teaser.summary}</p>
        <p className="tr-muted">{[sectorLabel(messages, teaser.sector), stageLabel(messages, teaser.stage)].filter(Boolean).join(' · ')}</p>
        {teaser.keywords.length ? (
          <p className="tr-muted tr-sys-type-support">
            {words.keywords('')}
            <span lang={content}>{teaser.keywords.join(', ')}</span>
          </p>
        ) : null}
      </section>
      <section className="tr-panel tr-stack" aria-labelledby="detail">
        <h2 id="detail" className="tr-sys-type-heading-sm">
          {words.moreTitle}
        </h2>
        <p>{words.moreBody}</p>
        <div className="tr-row">
          <Link className="tr-btn tr-btn--primary" href={localHref(locale, `/start?kembali=${encodeURIComponent(detail)}`)}>
            {words.signUp}
          </Link>
          <Link className="tr-link" href={localHref(locale, `/start?masuk=1&kembali=${encodeURIComponent(detail)}`)}>
            {words.signIn}
          </Link>
        </div>
      </section>
    </AuthShell>
  );
}

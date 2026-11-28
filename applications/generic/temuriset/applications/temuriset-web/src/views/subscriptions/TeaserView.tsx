import Link from 'next/link';

import { EmptyState } from '@/components/tr/EmptyState';
import { TktBadge } from '@/components/tr/TktBadge';
import { FollowForm } from '@/features/subscriptions/FollowForm';
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
  // Inventor content is in the language the owner wrote; mark it when the page speaks the other one.
  const written = teaser.content_locale ?? 'id';
  const content = written !== locale ? written : undefined;
  return (
    <AuthShell title={teaser.title} subtitle={words.inventor(teaser.inventor_name)}>
      <div className="tr-showcase">
        <section className="tr-panel tr-stack" aria-labelledby="ringkasan">
          <h2 id="ringkasan" className="tr-sys-type-heading-sm">
            {words.summary}
          </h2>
          <p className="tr-muted">{[sectorLabel(messages, teaser.sector), stageLabel(messages, teaser.stage)].filter(Boolean).join(' · ')}</p>
          {teaser.tkt_level ? (
            <TktBadge level={teaser.tkt_level} stageLabel={stageLabel(messages, teaser.stage)} showMeta locale={locale} />
          ) : null}
          {content ? <p className="tr-muted tr-sys-type-support">{words.writtenIn}</p> : null}
          <p lang={content}>{teaser.summary}</p>
          {teaser.keywords.length ? (
            <p className="tr-muted tr-sys-type-support">
              {words.keywords('')}
              <span lang={content}>{teaser.keywords.join(', ')}</span>
            </p>
          ) : null}
          {teaser.field_test_summary ? (
            <>
              <h3 className="tr-sys-type-label">{words.fieldTest}</h3>
              <p lang={content}>{teaser.field_test_summary}</p>
            </>
          ) : null}
        </section>
        {teaser.photo ? <PublicPhoto photo={teaser.photo} /> : null}
      </div>
      {teaser.follow_enabled ? <FollowForm inventionId={teaser.id} /> : null}
      {teaser.latest_updates?.length ? (
        <section className="tr-panel tr-stack" aria-labelledby="kabar-terbaru">
          <h2 id="kabar-terbaru" className="tr-sys-type-heading-sm">
            {words.updates}
          </h2>
          <ul className="tr-list">
            {teaser.latest_updates.map((update) => {
              const lang = update.content_locale !== locale ? update.content_locale : undefined;
              return (
                <li key={update.id} className="tr-listrow tr-stack">
                  <h3 className="tr-sys-type-label" lang={lang}>
                    {update.title}
                  </h3>
                  <p className="tr-muted tr-sys-type-support">
                    <time dateTime={update.published_at}>{publishedOn(update.published_at, locale)}</time>
                    {lang ? ` · ${words.writtenIn}` : null}
                  </p>
                  <p lang={lang}>{update.body}</p>
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}
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

/** A calendar date in Jakarta time, in the page's language. */
function publishedOn(iso: string, locale: Locale): string {
  return new Intl.DateTimeFormat(locale === 'en' ? 'en-GB' : 'id-ID', { dateStyle: 'long', timeZone: 'Asia/Jakarta' }).format(new Date(iso));
}

type Photo = NonNullable<Teaser['photo']>;

/**
 * The published photo at its real size, so the page never shifts while it loads. Metadata was removed on the server,
 * rotation with it, so the recorded orientation is applied here: turned photos swap their frame and rotate inside it.
 */
function PublicPhoto({ photo }: { photo: Photo }) {
  const orientation = photo.orientation ?? 1;
  const turned = orientation >= 5;
  const degrees = orientation === 3 || orientation === 4 ? 180 : orientation === 6 || orientation === 5 ? 90 : orientation === 8 || orientation === 7 ? -90 : 0;
  const frame = turned ? `${photo.height} / ${photo.width}` : `${photo.width} / ${photo.height}`;
  const style = turned
    ? { width: `${(100 * photo.width) / photo.height}%`, height: `${(100 * photo.height) / photo.width}%`, transform: `translate(-50%, -50%) rotate(${degrees}deg)` }
    : degrees
      ? { transform: `rotate(${degrees}deg)` }
      : undefined;
  return (
    <div className="tr-showcase__media" style={{ aspectRatio: frame }}>
      {/* eslint-disable-next-line @next/next/no-img-element -- the service already serves a cleaned, sized file; next/image would re-encode it through another route. */}
      <img className={turned ? 'is-turned' : undefined} src={photo.url} alt={photo.alt} width={photo.width} height={photo.height} fetchPriority="high" style={style} />
    </div>
  );
}

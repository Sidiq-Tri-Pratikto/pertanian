'use client';

import { useSyncExternalStore, type MouseEvent, type ReactNode } from 'react';

import { Logo } from '@/components/tr/Logo';
import { rememberEmail, subscribeNever } from '@/features/i18n/carry';
import { useLocale, useMessages } from '@/features/i18n/LocaleProvider';
import { localHref, rememberLocale, switchHref } from '@/features/i18n/locale';

function currentAddress(): string {
  return `${window.location.pathname}${window.location.search}`;
}

/**
 * The signed-out frame: logo, the ID/EN switch, one heading, one task. The switch opens the same page and step in the
 * other language; an email typed on the page comes along in this tab's storage, never in the address (spec 050).
 */
export function AuthShell({ title, subtitle, children }: { title: string; subtitle?: ReactNode; children: ReactNode }) {
  const locale = useLocale();
  const words = useMessages().shell;
  // The address as the visitor sees it, read in the browser; before that, the other language's start page.
  const here = useSyncExternalStore(subscribeNever, currentAddress, () => null);
  const target = here ? switchHref(locale, here) : switchHref(locale, localHref(locale, '/start'));

  function change(event: MouseEvent<HTMLAnchorElement>) {
    event.preventDefault();
    const typed = document.querySelector<HTMLInputElement>('input[type="email"]')?.value;
    if (typed) rememberEmail(typed);
    rememberLocale(locale === 'en' ? 'id' : 'en');
    window.location.assign(switchHref(locale, currentAddress()));
  }

  return (
    <div className="tr-root tr-screen">
      <header className="tr-bar">
        <div className="tr-bar__in">
          <Logo href={localHref(locale, '/')} />
          <a className="tr-langswitch tr-link" href={target} hrefLang={locale === 'en' ? 'id' : 'en'} onClick={change}>
            {words.switchTo}
            <span className="tr-sr">{` ${words.switchName}`}</span>
          </a>
        </div>
      </header>
      <div className="tr-page">
        <main id="isi" tabIndex={-1} className="tr-page__main tr-section">
          <div className="tr-page__head">
            <h1 className="tr-sys-type-display">{title}</h1>
            {subtitle ? <p className="tr-muted">{subtitle}</p> : null}
          </div>
          {children}
        </main>
      </div>
    </div>
  );
}

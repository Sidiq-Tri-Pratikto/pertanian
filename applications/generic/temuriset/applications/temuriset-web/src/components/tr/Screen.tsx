'use client';

import Link from 'next/link';
import { useEffect, useRef, useState, type ReactNode } from 'react';

import { Icon } from '@/components/tr/Icon';
import { Logo } from '@/components/tr/Logo';
import { useLocale, useMessages } from '@/features/i18n/LocaleProvider';
import { rememberLocale } from '@/features/i18n/locale';
import { t, tx } from '@/features/i18n/t';
import { NAV, type NavItem, type Persona } from '@/features/persona';

type ScreenProps = {
  persona: Persona;
  /** Navigation item id to mark as the current page. */
  current?: string;
  title: string;
  subtitle?: ReactNode;
  back?: ReactNode;
  context?: ReactNode;
  provenance?: string;
  children?: ReactNode;
};

/**
 * Port of TR.Screen with real links instead of `onNavigate`: top navigation on wide screens, a tab bar with four
 * destinations plus Lainnya on narrow screens, and a skip link to the main region.
 */
export function Screen({ persona, current, title, subtitle, back, context, provenance, children }: ScreenProps) {
  const items = NAV[persona];
  const locale = useLocale();
  const words = useMessages().shell;
  const [moreOpen, setMoreOpen] = useState(false);
  const [fixedBar, setFixedBar] = useState(true);
  const bar = useRef<HTMLElement>(null);
  const main = useRef<HTMLElement>(null);

  // A tab bar that grows with large text must not cover the focused control.
  useEffect(() => {
    function fit() {
      if (bar.current) setFixedBar(bar.current.offsetHeight < window.innerHeight * 0.25);
    }
    fit();
    window.addEventListener('resize', fit);
    return () => window.removeEventListener('resize', fit);
  }, []);

  // Browsers do not scroll a control that is already partly visible, so a tall field can take focus under the sticky
  // tab bar. Scrolling it into view honours the design system's scroll-padding, which clears the bar (UX-21).
  useEffect(() => {
    function reveal(event: FocusEvent) {
      const target = event.target as HTMLElement | null;
      const tabbar = bar.current;
      if (!target || !tabbar || tabbar.contains(target) || getComputedStyle(tabbar).display === 'none') return;
      if (target.getBoundingClientRect().bottom > tabbar.getBoundingClientRect().top) target.scrollIntoView({ block: 'nearest' });
    }
    document.addEventListener('focusin', reveal);
    return () => document.removeEventListener('focusin', reveal);
  }, []);

  function item(entry: NavItem, className: string, short: boolean) {
    return (
      <Link
        key={entry.id}
        href={entry.href}
        className={className}
        aria-current={current === entry.id ? 'page' : undefined}
        onClick={() => setMoreOpen(false)}>
        {short ? <Icon name={entry.icon} /> : null}
        <span>{t(short ? (entry.short ?? entry.label) : entry.label)}</span>
      </Link>
    );
  }

  return (
    <div className="tr-root tr-screen">
      <a
        className="tr-skip tr-link"
        href="#isi"
        onClick={(event) => {
          event.preventDefault();
          main.current?.focus();
        }}>
        {t('Langsung ke isi utama')}
      </a>
      <header className="tr-bar">
        <div className="tr-bar__in">
          <Logo href="/" />
          {provenance ? <span className="tr-provenance tr-sys-type-support">{t(provenance)}</span> : null}
          <nav className="tr-topnav" aria-label={t('Navigasi utama')}>
            {items.map((entry) => item(entry, 'tr-topnav__item tr-sys-type-label', false))}
          </nav>
          {context ? <div className="tr-bar__context">{context}</div> : null}
          <button
            type="button"
            className="tr-langswitch tr-link"
            onClick={() => {
              rememberLocale(locale === 'en' ? 'id' : 'en');
              window.location.reload();
            }}>
            {words.switchTo}
            <span className="tr-sr">{` ${words.switchName}`}</span>
          </button>
        </div>
      </header>
      <div className="tr-page">
        <main id="isi" ref={main} tabIndex={-1} className="tr-page__main tr-section">
          <div className="tr-page__head">
            {back ? <div>{back}</div> : null}
            <h1 className="tr-sys-type-display">{t(title)}</h1>
            {subtitle ? <p className="tr-muted">{tx(subtitle)}</p> : null}
          </div>
          {children}
        </main>
      </div>
      <nav ref={bar} className={fixedBar ? 'tr-tabbar' : 'tr-tabbar is-static'} aria-label={t('Navigasi utama')}>
        {moreOpen ? (
          <ul className="tr-tabbar__more">
            {items.slice(4).map((entry) => (
              <li key={entry.id}>{item(entry, 'tr-tabbar__moreItem tr-sys-type-label', false)}</li>
            ))}
          </ul>
        ) : null}
        <div className="tr-tabbar__row">
          {items.slice(0, 4).map((entry) => item(entry, 'tr-tabbar__item tr-sys-type-support', true))}
          <button
            type="button"
            className="tr-tabbar__item tr-sys-type-support"
            aria-expanded={moreOpen}
            onClick={() => setMoreOpen((open) => !open)}>
            <Icon name="more" />
            <span>{t('Lainnya')}</span>
          </button>
        </div>
      </nav>
    </div>
  );
}

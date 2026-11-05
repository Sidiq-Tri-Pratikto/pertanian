'use client';

import Link from 'next/link';
import { useEffect, useRef, useState, type ReactNode } from 'react';

import { Icon } from '@/components/tr/Icon';
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

  function item(entry: NavItem, className: string, short: boolean) {
    return (
      <Link
        key={entry.id}
        href={entry.href}
        className={className}
        aria-current={current === entry.id ? 'page' : undefined}
        onClick={() => setMoreOpen(false)}>
        {short ? <Icon name={entry.icon} /> : null}
        <span>{short ? (entry.short ?? entry.label) : entry.label}</span>
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
        Langsung ke isi utama
      </a>
      <header className="tr-bar">
        <div className="tr-bar__in">
          <span className="tr-wordmark tr-sys-type-body-strong">TemuRiset</span>
          {provenance ? <span className="tr-provenance tr-sys-type-support">{provenance}</span> : null}
          <nav className="tr-topnav" aria-label="Navigasi utama">
            {items.map((entry) => item(entry, 'tr-topnav__item tr-sys-type-label', false))}
          </nav>
          {context ? <div className="tr-bar__context">{context}</div> : null}
        </div>
      </header>
      <div className="tr-page">
        <main id="isi" ref={main} tabIndex={-1} className="tr-page__main tr-section">
          <div className="tr-page__head">
            {back ? <div>{back}</div> : null}
            <h1 className="tr-sys-type-heading-lg">{title}</h1>
            {subtitle ? <p className="tr-muted">{subtitle}</p> : null}
          </div>
          {children}
        </main>
      </div>
      <nav ref={bar} className={fixedBar ? 'tr-tabbar' : 'tr-tabbar is-static'} aria-label="Navigasi utama">
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
            <span>Lainnya</span>
          </button>
        </div>
      </nav>
    </div>
  );
}

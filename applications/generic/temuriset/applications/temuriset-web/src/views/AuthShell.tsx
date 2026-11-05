import type { ReactNode } from 'react';

/** The signed-out frame: wordmark, one heading, one task. */
export function AuthShell({ title, subtitle, children }: { title: string; subtitle?: ReactNode; children: ReactNode }) {
  return (
    <div className="tr-root tr-screen">
      <header className="tr-bar">
        <div className="tr-bar__in">
          <span className="tr-wordmark tr-sys-type-body-strong">TemuRiset</span>
        </div>
      </header>
      <div className="tr-page">
        <main id="isi" tabIndex={-1} className="tr-page__main tr-section">
          <div className="tr-page__head">
            <h1 className="tr-sys-type-heading-lg">{title}</h1>
            {subtitle ? <p className="tr-muted">{subtitle}</p> : null}
          </div>
          {children}
        </main>
      </div>
    </div>
  );
}

'use client';

import type { ReactNode } from 'react';

import { Button } from '@/components/tr/Button';
import { Status } from '@/components/tr/Status';
import { t, tx } from '@/features/i18n/t';

type VersionConflictProps = {
  what: ReactNode;
  currentVersion?: string;
  draft?: ReactNode;
  onRefresh?: () => void;
  refreshLabel?: string;
};

/** Port of TR.VersionConflict: someone else saved first; the person's own text stays visible and safe. */
export function VersionConflict({ what, currentVersion, draft, onRefresh, refreshLabel }: VersionConflictProps) {
  return (
    <div className="tr-conflict" role="group" aria-label={t('Versi berubah')}>
      <Status tone="warning" icon="alert" label={t('Versi sudah berubah')}>
        <p>{tx(what)}</p>
      </Status>
      {currentVersion ? <p>{t('Versi terbaru: {n}', { n: currentVersion })}</p> : null}
      {draft ? (
        <div>
          <p className="tr-sys-type-label">{t('Draf Anda masih aman:')}</p>
          <blockquote className="tr-quote">{draft}</blockquote>
        </div>
      ) : null}
      <div className="tr-row">
        {onRefresh ? (
          <Button intent="primary" icon="refresh" onClick={onRefresh}>
            {t(refreshLabel ?? 'Muat versi terbaru')}
          </Button>
        ) : null}
      </div>
    </div>
  );
}

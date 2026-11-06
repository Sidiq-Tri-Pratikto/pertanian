'use client';

import { Button } from '@/components/tr/Button';
import { Icon } from '@/components/tr/Icon';

export type SaveStatus = 'local' | 'saving' | 'saved' | 'failed' | 'conflict';

const VIEW: Record<SaveStatus, { icon: 'edit' | 'check' | 'alert' | null; label: string }> = {
  local: { icon: 'edit', label: 'Belum tersimpan' },
  saving: { icon: null, label: 'Menyimpan…' },
  saved: { icon: 'check', label: 'Tersimpan' },
  failed: { icon: 'alert', label: 'Gagal menyimpan' },
  conflict: { icon: 'alert', label: 'Versi sudah berubah' },
};

/** Port of TR.SaveState with `location="server"`: whether the work is saved, and a retry that keeps every value. */
export function SaveState({ state, onRetry }: { state: SaveStatus; onRetry?: () => void }) {
  const view = VIEW[state];
  return (
    <div className={`tr-save tr-save--${state}`}>
      <span role="status" className="tr-save__label tr-sys-type-support-strong">
        {view.icon ? <Icon name={view.icon} size="small" /> : <span className="tr-spinner" aria-hidden />}
        {view.label}
      </span>
      {state === 'failed' ? <span className="tr-sys-type-support">Isian Anda masih ada di halaman ini.</span> : null}
      {state === 'failed' && onRetry ? (
        <Button icon="refresh" onClick={onRetry}>
          Coba lagi
        </Button>
      ) : null}
    </div>
  );
}

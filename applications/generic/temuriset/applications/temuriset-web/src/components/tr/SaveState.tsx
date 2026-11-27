'use client';

import { Button } from '@/components/tr/Button';
import { Icon } from '@/components/tr/Icon';
import { useMessages } from '@/features/i18n/LocaleProvider';

export type SaveStatus = 'local' | 'saving' | 'saved' | 'failed' | 'conflict';

const ICON: Record<SaveStatus, 'edit' | 'check' | 'alert' | null> = {
  local: 'edit',
  saving: null,
  saved: 'check',
  failed: 'alert',
  conflict: 'alert',
};

/** Port of TR.SaveState with `location="server"`: whether the work is saved, and a retry that keeps every value. */
export function SaveState({ state, onRetry }: { state: SaveStatus; onRetry?: () => void }) {
  const words = useMessages().components.save;
  const view = { icon: ICON[state], label: words[state] };
  return (
    <div className={`tr-save tr-save--${state}`}>
      <span role="status" className="tr-save__label tr-sys-type-support-strong">
        {view.icon ? <Icon name={view.icon} size="small" /> : <span className="tr-spinner" aria-hidden />}
        {view.label}
      </span>
      {state === 'failed' ? <span className="tr-sys-type-support">{words.kept}</span> : null}
      {state === 'failed' && onRetry ? (
        <Button icon="refresh" onClick={onRetry}>
          {words.retry}
        </Button>
      ) : null}
    </div>
  );
}

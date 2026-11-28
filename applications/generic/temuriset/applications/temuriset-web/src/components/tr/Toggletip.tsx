'use client';

import { useEffect, useId, useRef, useState, type ReactNode } from 'react';

import { Icon } from '@/components/tr/Icon';
import { t } from '@/features/i18n/t';

type ToggletipProps = {
  label: string;
  children: ReactNode;
  id?: string;
};

/**
 * Port of TR.Toggletip (spec 055): a 24 px info trigger that opens a short explanation on click or Enter,
 * closes on Escape or outside click, and announces its content via a live `role="status"` region.
 */
export function Toggletip({ label, children, id }: ToggletipProps) {
  const generated = useId();
  const panelId = `${id ?? generated}-panel`;
  const rootRef = useRef<HTMLSpanElement>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') setOpen(false);
    }
    function onPointerDown(event: MouseEvent | PointerEvent) {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener('keydown', onKeyDown);
    document.addEventListener('mousedown', onPointerDown);
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.removeEventListener('mousedown', onPointerDown);
    };
  }, [open]);

  return (
    <span ref={rootRef} className="tr-tip">
      <button
        id={id}
        type="button"
        className="tr-tip__button"
        aria-expanded={open}
        aria-controls={panelId}
        aria-label={t('Penjelasan: {label}', { label })}
        onClick={() => setOpen((current) => !current)}>
        <Icon name="question" size="small" />
      </button>
      <span id={panelId} role="status" className="tr-tip__status">
        {open ? <span className="tr-tip__panel tr-sys-type-support">{children}</span> : null}
      </span>
    </span>
  );
}

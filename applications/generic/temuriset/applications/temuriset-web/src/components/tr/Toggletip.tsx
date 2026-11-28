'use client';

import { useEffect, useId, useRef, useState, type ReactNode } from 'react';

import { t } from '@/features/i18n/t';

type Props = {
  /** Short term being explained; used in the button's accessible name. */
  label: string;
  children: ReactNode;
  id?: string;
};

/**
 * Accessible click/keyboard toggletip: opens on click or Enter, closes on Escape or outside click,
 * and announces its content via a status region (spec 055 FR-005).
 */
export function Toggletip({ label, children, id }: Props) {
  const [open, setOpen] = useState(false);
  const autoId = useId();
  const panelId = id ?? `tip-${autoId}`;
  const rootRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!open) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') setOpen(false);
    }
    function onPointerDown(event: MouseEvent) {
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
        type="button"
        className="tr-tip__btn"
        aria-expanded={open}
        aria-controls={panelId}
        aria-label={t('Penjelasan: {label}', { label: t(label) })}
        onClick={() => setOpen((current) => !current)}>
        <span aria-hidden="true">i</span>
      </button>
      <span id={panelId} role="status" className="tr-tip__panel" hidden={!open}>
        {open ? children : null}
      </span>
    </span>
  );
}

'use client';

import { useEffect, useId, useRef, type KeyboardEvent, type ReactNode } from 'react';

import { Button } from '@/components/tr/Button';
import { Icon } from '@/components/tr/Icon';

const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), summary, [tabindex="0"]';

type DialogProps = {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  primary?: { label: string; onClick: () => void; busy?: boolean; busyLabel?: string; intent?: 'primary' | 'danger' };
  secondary?: { label: string; onClick: () => void };
  /** Where focus returns when the dialog closes; defaults to whatever opened it. */
  returnFocusId?: string;
};

/** Port of TR.Dialog: a native modal, labelled by its title. Escape closes without committing; focus returns. */
export function Dialog({ open, onClose, title, children, primary, secondary, returnFocusId }: DialogProps) {
  const dialog = useRef<HTMLDialogElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const opener = useRef<Element | null>(null);
  const titleId = useId();

  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    if (open && !element.open) {
      opener.current = document.activeElement;
      element.showModal();
      heading.current?.focus();
    } else if (!open && element.open) {
      element.close();
      const back = (returnFocusId && document.getElementById(returnFocusId)) || opener.current;
      if (back instanceof HTMLElement) back.focus();
    }
  }, [open, returnFocusId]);

  // Native modality keeps the page inert; this keeps Tab from leaving through the browser chrome.
  function trap(event: KeyboardEvent<HTMLDialogElement>) {
    if (event.key !== 'Tab' || !dialog.current) return;
    const list = dialog.current.querySelectorAll<HTMLElement>(FOCUSABLE);
    const first = list[0];
    const last = list[list.length - 1];
    const at = document.activeElement;
    if (event.shiftKey && (at === first || at === heading.current)) {
      event.preventDefault();
      last?.focus();
    } else if (!event.shiftKey && at === last) {
      event.preventDefault();
      first?.focus();
    }
  }

  return (
    <dialog
      ref={dialog}
      className="tr-root tr-dialog"
      aria-labelledby={titleId}
      onKeyDown={trap}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}>
      {open ? (
        <>
          <div className="tr-dialog__head">
            <h2 id={titleId} ref={heading} tabIndex={-1} className="tr-sys-type-heading-md">
              {title}
            </h2>
            <button type="button" className="tr-icon-btn" aria-label="Tutup" onClick={onClose}>
              <Icon name="close" />
            </button>
          </div>
          <div className="tr-dialog__body tr-stack">{children}</div>
          <div className="tr-dialog__foot">
            {primary ? (
              <Button intent={primary.intent ?? 'primary'} busy={primary.busy} busyLabel={primary.busyLabel} onClick={primary.onClick}>
                {primary.label}
              </Button>
            ) : null}
            <Button onClick={secondary?.onClick ?? onClose}>{secondary?.label ?? 'Batal'}</Button>
          </div>
        </>
      ) : null}
    </dialog>
  );
}

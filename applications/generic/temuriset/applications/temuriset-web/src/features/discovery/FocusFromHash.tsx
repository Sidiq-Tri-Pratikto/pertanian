'use client';

import { useEffect } from 'react';

/**
 * Moves focus to the element the address points at (`#detail` after opening a result, `#hasil-<id>` after "Kembali
 * ke hasil"), so keyboard and screen reader users land where the page scrolled. Remount it to run again.
 */
export function FocusFromHash() {
  useEffect(() => {
    const id = decodeURIComponent(window.location.hash.slice(1));
    if (id) document.getElementById(id)?.focus({ preventScroll: false });
  }, []);
  return null;
}

import { cache } from 'react';

import { APP_EN } from '@/features/i18n/app-en';
import type { Locale } from '@/features/i18n/locale';

/**
 * Interface copy for the signed-in app (revamp R7): `t('Simpan inovasi')` returns the Indonesian source, or its English
 * entry in `app-en.ts` when the page language is English. A missing entry falls back to the Indonesian text, and a
 * test lists every `t('...')` without one.
 *
 * Server components read the language from a per-request store (`requireMe` sets it); client components read it from
 * `LocaleProvider`, which sets it while rendering.
 */
const requestStore = cache((): { locale: Locale } => ({ locale: 'id' }));
// ponytail: one value per server process for client components rendered on the server; two requests in different
// languages rendering at the same moment can swap words until hydration. Use a context-only `useT()` if that shows.
let shared: Locale = 'id';

export function setAppLocale(locale: Locale): void {
  requestStore().locale = locale;
  shared = locale;
}

export function appLocale(): Locale {
  const store = requestStore();
  // React memoizes `cache` only while rendering server components; elsewhere each call returns a fresh store.
  return store === requestStore() ? store.locale : shared;
}

export function t(source: string, values?: Record<string, string | number>): string {
  const text = appLocale() === 'en' ? (APP_EN[source] ?? source) : source;
  return values ? text.replace(/\{(\w+)\}/g, (match, key: string) => (key in values ? String(values[key]) : match)) : text;
}

/** Translate text passed to a shared component; anything that is not plain text passes through unchanged. */
export function tx<T>(node: T): T | string {
  return typeof node === 'string' ? t(node) : node;
}

/** The `Intl` locale for dates and numbers in the page language. */
export function intlLocale(): string {
  return appLocale() === 'en' ? 'en-GB' : 'id-ID';
}

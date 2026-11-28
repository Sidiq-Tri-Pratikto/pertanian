import { cookies, headers } from 'next/headers';

import { asLocale, LOCALE_COOKIE, LOCALE_HEADER, type Locale } from '@/features/i18n/locale';
import { setAppLocale, t } from '@/features/i18n/t';

/** The page language: English for an `/en/...` address, otherwise the visitor's last choice from the ID/EN switch. */
export async function serverLocale(): Promise<Locale> {
  const header = (await headers()).get(LOCALE_HEADER);
  if (header) return asLocale(header);
  return asLocale((await cookies()).get(LOCALE_COOKIE)?.value);
}

/** Resolve the language for this request's server components, then return it. */
export async function resolveRequestLocale(): Promise<Locale> {
  const locale = await serverLocale();
  setAppLocale(locale);
  return locale;
}

/** `generateMetadata` for a page whose title is fixed copy. */
export function titled(source: string): () => Promise<{ title: string }> {
  return async () => {
    await resolveRequestLocale();
    return { title: t(source) };
  };
}

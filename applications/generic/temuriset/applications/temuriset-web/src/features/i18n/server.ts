import { headers } from 'next/headers';

import { asLocale, LOCALE_HEADER, type Locale } from '@/features/i18n/locale';

/** The page language for this request: English when the proxy served an `/en/...` address. */
export async function serverLocale(): Promise<Locale> {
  return asLocale((await headers()).get(LOCALE_HEADER));
}

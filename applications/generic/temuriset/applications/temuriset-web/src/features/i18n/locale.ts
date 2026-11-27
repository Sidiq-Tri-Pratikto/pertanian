/** The two interface languages, the request header that carries one, and the English public paths (spec 050). */
export type Locale = 'id' | 'en';

/** Set by `src/proxy.ts` on every `/en/...` request; read by the layout and by server reads. */
export const LOCALE_HEADER = 'x-tr-locale';
/** Sent to the service so its messages and emails use the same language. */
export const API_LOCALE_HEADER = 'X-TemuRiset-Locale';

export function asLocale(value: string | null | undefined): Locale {
  return value === 'en' ? 'en' : 'id';
}

/** English path segment to the Indonesian route that serves it; other segments are the same in both. */
export const EN_TO_ID: Record<string, string> = {
  inventions: 'temuan',
  subscribe: 'langganan',
  confirm: 'konfirmasi',
  manage: 'atur',
  code: 'kode',
};
const ID_TO_EN = Object.fromEntries(Object.entries(EN_TO_ID).map(([en, id]) => [id, en]));

function mapPath(path: string, table: Record<string, string>): string {
  const [pathname, ...rest] = path.split(/(?=[?#])/);
  const mapped = pathname
    .split('/')
    .map((segment) => table[segment] ?? segment)
    .join('/');
  return mapped + rest.join('');
}

/** The Indonesian route behind an English path: `/en/subscribe/manage?token=x` → `/langganan/atur?token=x`. */
export function toIndonesianPath(path: string): string {
  const rest = path === '/en' ? '/' : path.replace(/^\/en(?=\/|\?|#|$)/, '');
  return mapPath(rest || '/', EN_TO_ID);
}

/** The address of an Indonesian route in a language: `/langganan` in English is `/en/subscribe`. */
export function localHref(locale: Locale, path: string): string {
  if (locale === 'id') return path;
  const mapped = mapPath(path, ID_TO_EN);
  return mapped === '/' ? '/en' : `/en${mapped}`;
}

/** The same page in the other language, for the ID/EN switch. */
export function switchHref(current: Locale, path: string): string {
  return current === 'en' ? toIndonesianPath(path) : localHref('en', path);
}

/** BCP 47 tag for `Intl`. */
export function intlTag(locale: Locale): string {
  return locale === 'en' ? 'en-GB' : 'id-ID';
}

/** What the start screen hands to the code screen, kept in this tab only and never in the address bar. */
export type PendingSignIn = {
  email: string;
  purpose: 'sign_up' | 'sign_in';
  display_name?: string;
  locale?: string;
  time_zone?: string;
  persona?: string;
  returnTo: string | null;
};

const KEY = 'tr_masuk';

export function savePending(pending: PendingSignIn): void {
  sessionStorage.setItem(KEY, JSON.stringify(pending));
}

/** The raw stored value, stable between renders so it can feed `useSyncExternalStore`. */
export function readPendingRaw(): string | null {
  return sessionStorage.getItem(KEY);
}

export function parsePending(raw: string | null): PendingSignIn | null {
  try {
    const value: unknown = JSON.parse(raw ?? 'null');
    const pending = value as Partial<PendingSignIn> | null;
    return typeof pending?.email === 'string' && (pending.purpose === 'sign_up' || pending.purpose === 'sign_in') ? (pending as PendingSignIn) : null;
  } catch {
    return null;
  }
}

export function readPending(): PendingSignIn | null {
  return parsePending(readPendingRaw());
}

export function clearPending(): void {
  sessionStorage.removeItem(KEY);
}

/** The code request body: the profile is applied only when the code is verified. */
export function codeRequest(pending: PendingSignIn) {
  const { email, purpose, display_name, locale, time_zone, persona } = pending;
  return { email, purpose, display_name, locale, time_zone, persona };
}

export const TIME_ZONES = [
  { value: 'Asia/Jakarta', label: 'WIB · Asia/Jakarta' },
  { value: 'Asia/Makassar', label: 'WITA · Asia/Makassar' },
  { value: 'Asia/Jayapura', label: 'WIT · Asia/Jayapura' },
  { value: 'Asia/Singapore', label: 'Asia/Singapore' },
  { value: 'Europe/London', label: 'Europe/London' },
  { value: 'UTC', label: 'UTC' },
];

export const LOCALES = [
  { value: 'id', label: 'Bahasa Indonesia' },
  { value: 'en', label: 'English' },
];

export const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

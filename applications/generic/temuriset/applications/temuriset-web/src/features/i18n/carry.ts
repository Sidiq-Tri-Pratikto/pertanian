/**
 * An email typed before switching language, kept only in this tab's sessionStorage for the next page and never in
 * the address. Forms read it as their starting value and forget it once sent.
 */
const KEY = 'tr-carried-email';

export function rememberEmail(email: string): void {
  try {
    sessionStorage.setItem(KEY, email);
  } catch {
    // Storage can be off; the visitor types the email again.
  }
}

export function carriedEmail(): string {
  try {
    return sessionStorage.getItem(KEY) ?? '';
  } catch {
    return '';
  }
}

export function forgetEmail(): void {
  try {
    sessionStorage.removeItem(KEY);
  } catch {
    // Nothing to forget.
  }
}

export function subscribeNever(): () => void {
  return () => undefined;
}

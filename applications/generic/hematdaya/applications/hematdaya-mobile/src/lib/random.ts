import { getRandomBytes } from 'expo-crypto';

/** A base64url token from the platform's secure random source: `bytes` × 8 bits of entropy. */
export function randomToken(bytes: number): string {
  const base64 = btoa(String.fromCharCode(...getRandomBytes(bytes)));
  return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

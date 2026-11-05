import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { cache } from 'react';

import type { Me } from '@/api/client';
import { ApiError } from '@/api/errors';
import { serverGet } from '@/api/server';
import { PERSONA_COOKIE, readPersona, type Persona } from '@/features/persona';

/** Reads `/me` once per server render with the visitor's cookies; `null` when nobody is signed in. */
export const getMe = cache(async (): Promise<Me | null> => {
  try {
    return await serverGet<Me>('/api/v1/me');
  } catch (error) {
    if (error instanceof ApiError && error.code === 'UNAUTHENTICATED') return null;
    throw error;
  }
});

/** Only a path on this site may be a return address, so a crafted link cannot send someone elsewhere. */
export function safeReturn(value: string | null | undefined): string | null {
  return value && value.startsWith('/') && !value.startsWith('//') && !value.startsWith('/\\') ? value : null;
}

/** Sends a visitor who is not signed in to the start screen, then back here after signing in. */
export async function requireMe(returnTo: string): Promise<Me> {
  const me = await getMe();
  if (!me) redirect(`/start?kembali=${encodeURIComponent(returnTo)}`);
  return me;
}

export function personaOf(me: Me): Persona {
  return readPersona(me.account.persona) ?? 'inovator';
}

/** The persona chosen before accounts existed (spec 002) pre-selects the sign-up choice once. */
export async function seededPersona(): Promise<Persona | null> {
  return readPersona((await cookies()).get(PERSONA_COOKIE)?.value);
}

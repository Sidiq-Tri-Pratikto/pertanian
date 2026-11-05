'use server';

import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

import { PERSONA_COOKIE, homeFor, readPersona } from '@/features/persona';

const ONE_YEAR_SECONDS = 60 * 60 * 24 * 365;

/** Saves the persona from the start or settings form. Works without JavaScript. */
export async function choosePersona(formData: FormData): Promise<void> {
  const persona = readPersona(formData.get('persona')?.toString());
  const origin = formData.get('origin')?.toString() === 'settings' ? '/settings' : '/start';
  if (!persona) redirect(`${origin}?galat=peran`);
  (await cookies()).set(PERSONA_COOKIE, persona, {
    httpOnly: true,
    sameSite: 'lax',
    path: '/',
    maxAge: ONE_YEAR_SECONDS,
  });
  redirect(origin === '/settings' ? '/settings?tersimpan=1' : homeFor(persona));
}

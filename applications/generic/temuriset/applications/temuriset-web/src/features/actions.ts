'use server';

import { cookies } from 'next/headers';

import { PERSONA_COOKIE } from '@/features/persona';

/** Removes the pre-account persona cookie once the account carries the persona. Calls no API. */
export async function forgetPersona(): Promise<void> {
  (await cookies()).delete(PERSONA_COOKIE);
}

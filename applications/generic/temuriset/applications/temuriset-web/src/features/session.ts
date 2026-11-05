import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

import { PERSONA_COOKIE, readPersona, type Persona } from '@/features/persona';

/** Reads the chosen persona on the server, so navigation renders without a flash. */
export async function getPersona(): Promise<Persona | null> {
  return readPersona((await cookies()).get(PERSONA_COOKIE)?.value);
}

/** Sends a visitor with no persona to the start screen. */
export async function requirePersona(): Promise<Persona> {
  const persona = await getPersona();
  if (!persona) redirect('/start');
  return persona;
}

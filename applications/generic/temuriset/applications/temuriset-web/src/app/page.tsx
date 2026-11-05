import { redirect } from 'next/navigation';

import { homeFor } from '@/features/persona';
import { getPersona } from '@/features/session';

/** Sends a returning visitor to their persona's first destination, and everyone else to the start screen. */
export default async function RootPage() {
  const persona = await getPersona();
  redirect(persona ? homeFor(persona) : '/start');
}

import { redirect } from 'next/navigation';

import { homeFor } from '@/features/persona';
import { getMe, personaOf } from '@/features/session';

/** Sends a signed-in account to its persona's first destination, and everyone else to the start screen. */
export default async function RootPage() {
  const me = await getMe();
  redirect(me ? homeFor(personaOf(me)) : '/start');
}

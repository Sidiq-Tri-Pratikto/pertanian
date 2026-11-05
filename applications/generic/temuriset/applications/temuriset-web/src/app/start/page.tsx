import type { Metadata } from 'next';
import { redirect } from 'next/navigation';

import { homeFor } from '@/features/persona';
import { getMe, personaOf, safeReturn, seededPersona } from '@/features/session';
import { StartView } from '@/views/StartView';

export const metadata: Metadata = { title: 'Mulai' };

type Props = { searchParams: Promise<{ masuk?: string; kembali?: string }> };

export default async function StartPage({ searchParams }: Props) {
  const { masuk, kembali } = await searchParams;
  const returnTo = safeReturn(kembali);
  const me = await getMe();
  if (me) redirect(returnTo ?? homeFor(personaOf(me)));
  return <StartView persona={await seededPersona()} mode={masuk ? 'sign_in' : 'sign_up'} returnTo={returnTo} />;
}

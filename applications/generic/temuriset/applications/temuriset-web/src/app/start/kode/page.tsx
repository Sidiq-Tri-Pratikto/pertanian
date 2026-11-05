import type { Metadata } from 'next';
import { redirect } from 'next/navigation';

import { homeFor } from '@/features/persona';
import { getMe, personaOf } from '@/features/session';
import { CodeView } from '@/views/CodeView';

export const metadata: Metadata = { title: 'Kode verifikasi' };

export default async function CodePage() {
  const me = await getMe();
  if (me) redirect(homeFor(personaOf(me)));
  return <CodeView />;
}

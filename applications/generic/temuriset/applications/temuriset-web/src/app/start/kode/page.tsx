import type { Metadata } from 'next';
import { redirect } from 'next/navigation';

import { homeFor } from '@/features/persona';
import { getMe, personaOf } from '@/features/session';
import { CodeView } from '@/views/CodeView';
import { messagesFor } from '@/features/i18n/messages';
import { serverLocale } from '@/features/i18n/server';

export async function generateMetadata(): Promise<Metadata> {
  return { title: messagesFor(await serverLocale()).meta.code };
}

export default async function CodePage() {
  const me = await getMe();
  if (me) redirect(homeFor(personaOf(me)));
  return <CodeView />;
}

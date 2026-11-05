import type { Metadata } from 'next';

import { choosePersona } from '@/features/actions';
import { getPersona } from '@/features/session';
import { StartView } from '@/views/StartView';

export const metadata: Metadata = { title: 'Mulai' };

type Props = { searchParams: Promise<{ galat?: string }> };

export default async function StartPage({ searchParams }: Props) {
  const { galat } = await searchParams;
  return <StartView action={choosePersona} persona={await getPersona()} invalid={galat === 'peran'} />;
}

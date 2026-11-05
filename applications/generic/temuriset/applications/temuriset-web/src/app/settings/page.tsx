import type { Metadata } from 'next';

import { choosePersona } from '@/features/actions';
import { requirePersona } from '@/features/session';
import { SettingsView } from '@/views/SettingsView';

export const metadata: Metadata = { title: 'Profil dan privasi' };

type Props = { searchParams: Promise<{ tersimpan?: string; galat?: string }> };

export default async function SettingsPage({ searchParams }: Props) {
  const persona = await requirePersona();
  const { tersimpan, galat } = await searchParams;
  return <SettingsView action={choosePersona} persona={persona} saved={tersimpan === '1'} invalid={galat === 'peran'} />;
}

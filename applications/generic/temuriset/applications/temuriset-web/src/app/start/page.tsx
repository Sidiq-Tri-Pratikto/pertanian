import type { Metadata } from 'next';
import { redirect } from 'next/navigation';

import type { CapabilityManifest } from '@/api/client';
import { serverGet } from '@/api/server';
import { DemoPanel, type DemoAccount } from '@/features/demo/DemoPanel';
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
  const demo = await demoAccounts();
  return <StartView persona={await seededPersona()} mode={masuk ? 'sign_in' : 'sign_up'} returnTo={returnTo} demo={demo ? <DemoPanel accounts={demo} /> : undefined} />;
}

/** Demo accounts when the manifest says this deployment runs the labelled demo; otherwise nothing. */
async function demoAccounts(): Promise<DemoAccount[] | null> {
  try {
    const manifest = await serverGet<CapabilityManifest>('/api/v1/capabilities');
    return manifest.demo ? await serverGet<DemoAccount[]>('/api/v1/demo/accounts') : null;
  } catch {
    return null;
  }
}

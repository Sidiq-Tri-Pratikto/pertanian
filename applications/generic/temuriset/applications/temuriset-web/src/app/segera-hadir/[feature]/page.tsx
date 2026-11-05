import type { Metadata } from 'next';
import { redirect } from 'next/navigation';

import { readCapabilities } from '@/features/capabilities';
import { findFeature, isOffered } from '@/features/registry';
import { requireMe } from '@/features/session';
import { ComingSoonView } from '@/views/ComingSoonView';

type Props = { params: Promise<{ feature: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  return { title: findFeature((await params).feature)?.title ?? 'Fitur tidak dikenal' };
}

export default async function ComingSoonPage({ params }: Props) {
  const { feature: id } = await params;
  const me = await requireMe(`/segera-hadir/${id}`);
  const found = findFeature(id);
  // A feature that has shipped lives on its own screen; accounts and contexts live in Profil.
  if (found?.status === 'available') redirect('/settings');
  // A feature the deployment does not run reads as unknown, so its plan is never advertised.
  const feature = found && isOffered(found, await readCapabilities()) ? found : undefined;
  return <ComingSoonView me={me} feature={feature} showSpecs={process.env.NODE_ENV === 'development'} />;
}

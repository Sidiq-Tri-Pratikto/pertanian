import type { Metadata } from 'next';

import { readCapabilities } from '@/features/capabilities';
import { findFeature, isOffered } from '@/features/registry';
import { requirePersona } from '@/features/session';
import { ComingSoonView } from '@/views/ComingSoonView';

type Props = { params: Promise<{ feature: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  return { title: findFeature((await params).feature)?.title ?? 'Fitur tidak dikenal' };
}

export default async function ComingSoonPage({ params }: Props) {
  const persona = await requirePersona();
  const found = findFeature((await params).feature);
  // A feature the deployment does not run reads as unknown, so its plan is never advertised.
  const feature = found && isOffered(found, await readCapabilities()) ? found : undefined;
  return <ComingSoonView persona={persona} feature={feature} showSpecs={process.env.NODE_ENV === 'development'} />;
}

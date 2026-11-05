import type { Metadata } from 'next';

import { findFeature } from '@/features/registry';
import { requirePersona } from '@/features/session';
import { ComingSoonView } from '@/views/ComingSoonView';

type Props = { params: Promise<{ feature: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  return { title: findFeature((await params).feature)?.title ?? 'Fitur tidak dikenal' };
}

export default async function ComingSoonPage({ params }: Props) {
  const persona = await requirePersona();
  const feature = findFeature((await params).feature);
  return <ComingSoonView persona={persona} feature={feature} showSpecs={process.env.NODE_ENV === 'development'} />;
}

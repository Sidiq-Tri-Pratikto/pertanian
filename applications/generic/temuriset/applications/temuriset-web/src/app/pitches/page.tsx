import type { Metadata } from 'next';

import { readCapabilities } from '@/features/capabilities';
import { destinationFor } from '@/features/destinations';
import { requirePersona } from '@/features/session';
import { DestinationView } from '@/views/DestinationView';

export const metadata: Metadata = { title: 'Pitching' };

type Props = { searchParams: Promise<{ box?: string }> };

export default async function PitchesPage({ searchParams }: Props) {
  const persona = await requirePersona();
  const { box } = await searchParams;
  return <DestinationView persona={persona} destination={destinationFor('pitches', persona, box)} capabilities={await readCapabilities()} />;
}

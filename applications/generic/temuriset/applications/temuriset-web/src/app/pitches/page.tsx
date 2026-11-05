import type { Metadata } from 'next';

import { readCapabilities } from '@/features/capabilities';
import { destinationFor } from '@/features/destinations';
import { personaOf, requireMe } from '@/features/session';
import { DestinationView } from '@/views/DestinationView';

export const metadata: Metadata = { title: 'Pitching' };

type Props = { searchParams: Promise<{ box?: string }> };

export default async function PitchesPage({ searchParams }: Props) {
  const me = await requireMe('/pitches');
  const persona = personaOf(me);
  const { box } = await searchParams;
  return <DestinationView me={me} destination={destinationFor('pitches', persona, box)} capabilities={await readCapabilities()} />;
}

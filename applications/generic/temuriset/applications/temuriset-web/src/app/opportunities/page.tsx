import type { Metadata } from 'next';

import { readCapabilities } from '@/features/capabilities';
import { destinationFor } from '@/features/destinations';
import { personaOf, requireMe } from '@/features/session';
import { DestinationView } from '@/views/DestinationView';

export const metadata: Metadata = { title: 'Kebutuhan/Mandat' };

export default async function Page() {
  const me = await requireMe('/opportunities');
  const persona = personaOf(me);
  return <DestinationView me={me} destination={destinationFor('opportunities', persona)} capabilities={await readCapabilities()} />;
}

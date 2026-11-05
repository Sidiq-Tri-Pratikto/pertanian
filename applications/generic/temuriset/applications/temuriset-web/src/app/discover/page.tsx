import type { Metadata } from 'next';

import { readCapabilities } from '@/features/capabilities';
import { destinationFor } from '@/features/destinations';
import { personaOf, requireMe } from '@/features/session';
import { DestinationView } from '@/views/DestinationView';

export const metadata: Metadata = { title: 'Temukan dan jelajahi' };

export default async function DiscoverPage() {
  const me = await requireMe('/discover');
  const persona = personaOf(me);
  return <DestinationView me={me} destination={destinationFor('discover', persona)} capabilities={await readCapabilities()} />;
}

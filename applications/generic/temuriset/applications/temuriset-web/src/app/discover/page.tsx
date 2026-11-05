import type { Metadata } from 'next';

import { readCapabilities } from '@/features/capabilities';
import { destinationFor } from '@/features/destinations';
import { requirePersona } from '@/features/session';
import { DestinationView } from '@/views/DestinationView';

export const metadata: Metadata = { title: 'Temukan dan jelajahi' };

export default async function DiscoverPage() {
  const persona = await requirePersona();
  return <DestinationView persona={persona} destination={destinationFor('discover', persona)} capabilities={await readCapabilities()} />;
}

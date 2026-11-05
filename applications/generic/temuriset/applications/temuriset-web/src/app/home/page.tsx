import type { Metadata } from 'next';

import { readCapabilities } from '@/features/capabilities';
import { destinationFor } from '@/features/destinations';
import { requirePersona } from '@/features/session';
import { DestinationView } from '@/views/DestinationView';

export const metadata: Metadata = { title: 'Beranda' };

export default async function Page() {
  const persona = await requirePersona();
  return <DestinationView persona={persona} destination={destinationFor('home', persona)} capabilities={await readCapabilities()} />;
}

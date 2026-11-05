import type { Metadata } from 'next';

import { readCapabilities } from '@/features/capabilities';
import { destinationFor } from '@/features/destinations';
import { personaOf, requireMe } from '@/features/session';
import { DestinationView } from '@/views/DestinationView';

export const metadata: Metadata = { title: 'Beranda' };

export default async function Page() {
  const me = await requireMe('/home');
  const persona = personaOf(me);
  return <DestinationView me={me} destination={destinationFor('home', persona)} capabilities={await readCapabilities()} />;
}

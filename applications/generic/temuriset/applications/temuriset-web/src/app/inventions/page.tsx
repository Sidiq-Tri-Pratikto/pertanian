import type { Metadata } from 'next';

import { readCapabilities } from '@/features/capabilities';
import { destinationFor } from '@/features/destinations';
import { personaOf, requireMe } from '@/features/session';
import { DestinationView } from '@/views/DestinationView';

export const metadata: Metadata = { title: 'Inovasi Saya' };

export default async function Page() {
  const me = await requireMe('/inventions');
  const persona = personaOf(me);
  return <DestinationView me={me} destination={destinationFor('inventions', persona)} capabilities={await readCapabilities()} />;
}

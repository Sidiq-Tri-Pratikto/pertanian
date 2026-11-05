import type { Metadata } from 'next';

import { serverGet } from '@/api/server';
import { readCapabilities } from '@/features/capabilities';
import { destinationFor } from '@/features/destinations';
import { needsRange, type SupportRequest } from '@/features/needs/model';
import { personaOf, requireMe } from '@/features/session';
import { DestinationView } from '@/views/DestinationView';

export const metadata: Metadata = { title: 'Beranda' };

export default async function Page() {
  const me = await requireMe('/home');
  const persona = personaOf(me);
  const support = persona === 'inovator' ? await serverGet<SupportRequest[]>('/api/v1/support-requests') : [];
  // Work that waits on this person: a need whose cost range is still open.
  const queue = support.filter(needsRange).map((request) => ({
    href: `/support-requests/${request.id}`,
    label: 'Lengkapi kisaran biaya pilot untuk kebutuhan ini',
    context: `${request.outcome || 'Kebutuhan tanpa judul'} · ${request.invention_title}`,
  }));
  return <DestinationView me={me} destination={destinationFor('home', persona)} capabilities={await readCapabilities()} queue={queue} />;
}

import type { Metadata } from 'next';

import { serverGet } from '@/api/server';
import { readCapabilities } from '@/features/capabilities';
import type { components } from '@/api/schema.generated';
import { destinationFor } from '@/features/destinations';
import type { Notice } from '@/features/discussion/NotificationList';
import { needsRange, type SupportRequest } from '@/features/needs/model';
import { personaOf, requireMe } from '@/features/session';
import { DestinationView, type QueueItem } from '@/views/DestinationView';

export const metadata: Metadata = { title: 'Beranda' };

export default async function Page() {
  const me = await requireMe('/home');
  const persona = personaOf(me);
  const [support, pitches, notifications] = await Promise.all([
    persona === 'inovator' ? serverGet<SupportRequest[]>('/api/v1/support-requests') : Promise.resolve([]),
    serverGet<components['schemas']['QueueItem'][]>('/api/v1/me/queue'),
    serverGet<Notice[]>('/api/v1/notifications?limit=5'),
  ]);
  // Work that waits on this person: pitches from the server's whose-turn projection, then needs whose range is open.
  const fromPitches: QueueItem[] = pitches.map((item) => ({
    href: `/pitches/${item.pitch_id}?tab=${item.tab}`,
    label: item.title,
    context: `${item.subject_title} → ${item.opportunity_title}`,
    who: item.who ?? undefined,
    text: item.text,
  }));
  const needs: QueueItem[] = support.filter(needsRange).map((request) => ({
    href: `/support-requests/${request.id}`,
    label: 'Lengkapi kisaran biaya pilot untuk kebutuhan ini',
    context: `${request.outcome || 'Kebutuhan tanpa judul'} · ${request.invention_title}`,
    who: 'you',
  }));
  const queue = [...fromPitches, ...needs].sort((a, b) => Number(a.who === 'other') - Number(b.who === 'other'));
  return <DestinationView me={me} destination={destinationFor('home', persona)} capabilities={await readCapabilities()} queue={queue} notifications={notifications} />;
}

import type { Metadata } from 'next';

import { serverGet } from '@/api/server';
import { readCapabilities } from '@/features/capabilities';
import type { components } from '@/api/schema.generated';
import { destinationFor } from '@/features/destinations';
import type { Notice } from '@/features/discussion/NotificationList';
import { matchesHref } from '@/features/discovery/model';
import type { Invention, InventionSummary } from '@/features/portfolio/model';
import { resumeStep } from '@/features/portfolio/editor-state';
import { needsRange, type SupportRequest } from '@/features/needs/model';
import { personaOf, requireMe } from '@/features/session';
import { DestinationView, type QueueItem } from '@/views/DestinationView';

export const metadata: Metadata = { title: 'Beranda' };

export default async function Page() {
  const me = await requireMe('/home');
  const persona = personaOf(me);
  const [support, inventions, pitches, notifications] = await Promise.all([
    persona === 'inovator' ? serverGet<SupportRequest[]>('/api/v1/support-requests') : Promise.resolve([]),
    persona === 'inovator' ? serverGet<InventionSummary[]>('/api/v1/inventions') : Promise.resolve([]),
    serverGet<components['schemas']['QueueItem'][]>('/api/v1/me/queue'),
    serverGet<Notice[]>('/api/v1/notifications?limit=5'),
  ]);
  // Work that waits on this person: pitches from the server's whose-turn projection, then needs whose range is open.
  const fromPitches: QueueItem[] = pitches.map((item) => ({
    href: `/pitches/${item.pitch_id}?tab=${item.tab}`,
    label: item.title,
    context: `${item.subject_title} untuk ${item.opportunity_title}`,
    who: item.who ?? undefined,
    text: item.text,
  }));
  const needs: QueueItem[] = support.filter(needsRange).map((request) => ({
    href: `/support-requests/${request.id}`,
    label: 'Lengkapi kisaran biaya pilot untuk kebutuhan ini',
    context: `${request.outcome || 'Kebutuhan tanpa judul'} · ${request.invention_title}`,
    who: 'you',
  }));
  const queue = [...fromPitches, ...needs];
  // Nothing waits on this person: an unfinished first draft comes first, then an open need's matches.
  const draft = inventions.find((invention) => invention.status === 'DRAFT' && invention.has_draft);
  if (queue.every((item) => item.who !== 'you') && draft) {
    const step = resumeStep((await serverGet<Invention>(`/api/v1/inventions/${encodeURIComponent(draft.id)}`)).draft);
    queue.push({
      href: `/inventions/${draft.id}/edit?step=${step}`,
      label: 'Lanjutkan draf inovasi Anda',
      context: draft.title || 'Inovasi tanpa judul',
      who: 'you',
      text: step === 4 ? 'Semua bagian sudah terisi. Periksa pratinjau publik, lalu terbitkan.' : `Lanjutkan dari langkah ${step} dari 4.`,
      action: 'Lanjutkan draf',
    });
  }
  const open = support.find((request) => request.status === 'ACTIVE');
  if (queue.every((item) => item.who !== 'you') && open) {
    queue.push({
      href: matchesHref({ type: 'SUPPORT_REQUEST', id: open.id }),
      label: 'Temukan investor atau mitra untuk kebutuhan Anda',
      context: `${open.outcome || 'Kebutuhan tanpa judul'} · ${open.invention_title}`,
      who: 'you',
      text: 'Lihat siapa yang cocok dan alasannya, lalu siapkan pitching.',
      action: 'Lihat kecocokan',
    });
  }
  queue.sort((a, b) => Number(a.who === 'other') - Number(b.who === 'other'));
  return <DestinationView me={me} destination={destinationFor('home', persona)} capabilities={await readCapabilities()} queue={queue} notifications={notifications} />;
}

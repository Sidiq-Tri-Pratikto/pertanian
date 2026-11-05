import type { Metadata } from 'next';

import { serverGet } from '@/api/server';
import type { InventionSummary } from '@/features/portfolio/model';
import { requireMe } from '@/features/session';
import { InventionsView } from '@/views/portfolio/InventionViews';

export const metadata: Metadata = { title: 'Inovasi Saya' };

export default async function InventionsPage() {
  const me = await requireMe('/inventions');
  return <InventionsView me={me} inventions={await serverGet<InventionSummary[]>('/api/v1/inventions')} />;
}

import type { Metadata } from 'next';

import { serverGet } from '@/api/server';
import type { InventionSummary } from '@/features/portfolio/model';
import { requireMe } from '@/features/session';
import { PortabilityView } from '@/views/PortabilityView';

export const metadata: Metadata = { title: 'Impor dan ekspor data' };

export default async function PortabilityPage() {
  const me = await requireMe('/inventions/import');
  const inventions = await serverGet<InventionSummary[]>('/api/v1/inventions');
  return <PortabilityView key={me.active_party_id} me={me} inventions={inventions} />;
}

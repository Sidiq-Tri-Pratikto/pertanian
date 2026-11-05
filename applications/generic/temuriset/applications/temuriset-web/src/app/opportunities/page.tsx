import type { Metadata } from 'next';

import { serverGet } from '@/api/server';
import { readCapabilities } from '@/features/capabilities';
import type { Mandate } from '@/features/intake/model';
import { requireMe } from '@/features/session';
import { MandatesView } from '@/views/intake/MandatesView';

export const metadata: Metadata = { title: 'Kebutuhan/Mandat' };

type Props = { searchParams?: Promise<{ aktif?: string }> };

export default async function Page({ searchParams }: Props = {}) {
  const me = await requireMe('/opportunities');
  const [mandates, capabilities] = await Promise.all([serverGet<Mandate[]>('/api/v1/opportunities'), readCapabilities()]);
  const activated = (await searchParams)?.aktif;
  return <MandatesView me={me} mandates={mandates} capabilities={capabilities} activated={activated && /^\d+$/.test(activated) ? activated : undefined} />;
}

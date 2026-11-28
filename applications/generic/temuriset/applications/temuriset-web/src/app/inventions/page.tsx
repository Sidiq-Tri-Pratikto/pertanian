import { serverGet } from '@/api/server';
import type { InventionSummary } from '@/features/portfolio/model';
import { requireMe } from '@/features/session';
import { InventionsView } from '@/views/portfolio/InventionViews';
import { titled } from '@/features/i18n/server';

export const generateMetadata = titled('Inovasi Saya');

export default async function InventionsPage() {
  const me = await requireMe('/inventions');
  return <InventionsView me={me} inventions={await serverGet<InventionSummary[]>('/api/v1/inventions')} />;
}

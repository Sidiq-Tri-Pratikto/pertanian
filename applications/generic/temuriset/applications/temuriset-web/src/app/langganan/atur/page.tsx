import type { Metadata } from 'next';

import { ManageView } from '@/views/subscriptions/ManageView';

export const metadata: Metadata = { title: 'Langganan kabar inovasi' };

export default async function ManagePage({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  return <ManageView token={(await searchParams).token ?? ''} />;
}

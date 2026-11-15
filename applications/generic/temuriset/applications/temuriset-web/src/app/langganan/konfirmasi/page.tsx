import type { Metadata } from 'next';

import { ConfirmView } from '@/views/subscriptions/ConfirmView';

export const metadata: Metadata = { title: 'Konfirmasi langganan' };

export default async function ConfirmPage({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  return <ConfirmView token={(await searchParams).token ?? ''} />;
}

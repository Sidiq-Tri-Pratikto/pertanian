import type { Metadata } from 'next';

import { ConfirmView } from '@/views/subscriptions/ConfirmView';
import { messagesFor } from '@/features/i18n/messages';
import { serverLocale } from '@/features/i18n/server';

export async function generateMetadata(): Promise<Metadata> {
  return { title: messagesFor(await serverLocale()).meta.confirm };
}

export default async function ConfirmPage({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  return <ConfirmView token={(await searchParams).token ?? ''} />;
}

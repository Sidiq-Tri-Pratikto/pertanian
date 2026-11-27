import type { Metadata } from 'next';

import { ManageView } from '@/views/subscriptions/ManageView';
import { messagesFor } from '@/features/i18n/messages';
import { serverLocale } from '@/features/i18n/server';

export async function generateMetadata(): Promise<Metadata> {
  return { title: messagesFor(await serverLocale()).meta.manage };
}

export default async function ManagePage({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  return <ManageView token={(await searchParams).token ?? ''} />;
}

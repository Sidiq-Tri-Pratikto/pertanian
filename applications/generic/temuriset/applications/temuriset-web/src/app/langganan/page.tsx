import type { Metadata } from 'next';

import { SubscribeView } from '@/views/subscriptions/SubscribeView';
import { messagesFor } from '@/features/i18n/messages';
import { serverLocale } from '@/features/i18n/server';

export async function generateMetadata(): Promise<Metadata> {
  return { title: messagesFor(await serverLocale()).meta.subscribe };
}

export default function SubscribePage() {
  return <SubscribeView />;
}

import type { Metadata } from 'next';

import { SubscribeView } from '@/views/subscriptions/SubscribeView';

export const metadata: Metadata = { title: 'Kabar inovasi untuk investor' };

export default function SubscribePage() {
  return <SubscribeView />;
}

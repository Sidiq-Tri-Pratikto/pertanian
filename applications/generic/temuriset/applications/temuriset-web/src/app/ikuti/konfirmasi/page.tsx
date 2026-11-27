import type { Metadata } from 'next';

import { messagesFor } from '@/features/i18n/messages';
import { serverLocale } from '@/features/i18n/server';
import { FollowConfirmView } from '@/views/subscriptions/FollowConfirmView';

/** The token stays out of any Referer header sent from this page (053). */
export async function generateMetadata(): Promise<Metadata> {
  return { title: messagesFor(await serverLocale()).meta.followConfirm, referrer: 'no-referrer', robots: { index: false } };
}

export default async function FollowConfirmPage({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  return <FollowConfirmView token={(await searchParams).token ?? ''} />;
}

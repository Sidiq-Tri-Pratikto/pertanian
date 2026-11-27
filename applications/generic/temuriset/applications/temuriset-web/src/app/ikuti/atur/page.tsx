import type { Metadata } from 'next';

import { messagesFor } from '@/features/i18n/messages';
import { serverLocale } from '@/features/i18n/server';
import { FollowManageView } from '@/views/subscriptions/FollowManageView';

/** The token stays out of any Referer header sent from this page (053). */
export async function generateMetadata(): Promise<Metadata> {
  return { title: messagesFor(await serverLocale()).meta.followManage, referrer: 'no-referrer', robots: { index: false } };
}

export default async function FollowManagePage({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  return <FollowManageView token={(await searchParams).token ?? ''} />;
}

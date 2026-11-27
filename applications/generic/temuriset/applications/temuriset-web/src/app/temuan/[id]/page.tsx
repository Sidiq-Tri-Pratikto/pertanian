import type { Metadata } from 'next';

import { ApiError } from '@/api/errors';
import { serverGet } from '@/api/server';
import { messagesFor } from '@/features/i18n/messages';
import { serverLocale } from '@/features/i18n/server';
import { validId } from '@/features/relationships/model';
import type { Teaser } from '@/features/subscriptions/api';
import { TeaserView } from '@/views/subscriptions/TeaserView';

export async function generateMetadata(): Promise<Metadata> {
  return { title: messagesFor(await serverLocale()).teaser.pageTitle };
}

/** Readable signed out: only what the managing party included for investors. `/en/inventions/{id}` is the same page. */
export default async function TeaserPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const locale = await serverLocale();
  if (!validId(id)) return <TeaserView teaser={null} locale={locale} />;
  let teaser: Teaser | null = null;
  try {
    teaser = await serverGet<Teaser>(`/api/v1/teasers/inventions/${id}`);
  } catch (error) {
    if (!(error instanceof ApiError && error.code === 'NOT_FOUND')) throw error;
  }
  return <TeaserView teaser={teaser} locale={locale} />;
}

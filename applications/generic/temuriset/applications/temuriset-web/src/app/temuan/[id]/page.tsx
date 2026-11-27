import type { Metadata } from 'next';
import { notFound } from 'next/navigation';

import { ApiError } from '@/api/errors';
import { serverGet } from '@/api/server';
import { localHref } from '@/features/i18n/locale';
import { messagesFor } from '@/features/i18n/messages';
import { serverLocale } from '@/features/i18n/server';
import { validId } from '@/features/relationships/model';
import type { Teaser } from '@/features/subscriptions/api';
import { TeaserView } from '@/views/subscriptions/TeaserView';

type Props = { params: Promise<{ id: string }> };

/** The summary, or null when the invention is not public: unknown, unpublished, archived, suspended or switched off. */
async function readTeaser(id: string): Promise<Teaser | null> {
  if (!validId(id)) return null;
  try {
    return await serverGet<Teaser>(`/api/v1/teasers/inventions/${id}`);
  } catch (error) {
    if (error instanceof ApiError && error.code === 'NOT_FOUND') return null;
    throw error;
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const [locale, teaser] = await Promise.all([serverLocale(), readTeaser(id)]);
  if (!teaser) return { title: messagesFor(locale).teaser.unavailableTitle, robots: { index: false } };
  return {
    title: teaser.title,
    description: teaser.summary,
    // Search engines may list only pages the owner published; a summary shown only to investor emails stays out.
    robots: { index: Boolean(teaser.follow_enabled) },
    alternates: { languages: { id: `/temuan/${teaser.id}`, en: localHref('en', `/temuan/${teaser.id}`) } },
  };
}

/** The public invention page (051): readable signed out. `/en/inventions/{id}` is the same page in English. */
export default async function PublicInventionPage({ params }: Props) {
  const { id } = await params;
  const [locale, teaser] = await Promise.all([serverLocale(), readTeaser(id)]);
  if (!teaser) notFound();
  return <TeaserView teaser={teaser} locale={locale} />;
}

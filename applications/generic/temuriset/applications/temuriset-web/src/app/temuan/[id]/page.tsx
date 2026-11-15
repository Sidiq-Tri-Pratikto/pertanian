import type { Metadata } from 'next';

import { ApiError } from '@/api/errors';
import { serverGet } from '@/api/server';
import { validId } from '@/features/relationships/model';
import type { Teaser } from '@/features/subscriptions/api';
import { TeaserView } from '@/views/subscriptions/TeaserView';

export const metadata: Metadata = { title: 'Ringkasan inovasi' };

/** Readable signed out: only what the managing party included for investors. */
export default async function TeaserPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (!validId(id)) return <TeaserView teaser={null} />;
  let teaser: Teaser | null = null;
  try {
    teaser = await serverGet<Teaser>(`/api/v1/teasers/inventions/${id}`);
  } catch (error) {
    if (!(error instanceof ApiError && error.code === 'NOT_FOUND')) throw error;
  }
  return <TeaserView teaser={teaser} />;
}

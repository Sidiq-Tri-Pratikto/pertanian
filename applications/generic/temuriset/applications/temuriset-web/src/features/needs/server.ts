import { notFound } from 'next/navigation';

import { ApiError } from '@/api/errors';
import { serverGet } from '@/api/server';
import { readCapabilities } from '@/features/capabilities';
import type { InventionSummary } from '@/features/portfolio/model';

/** Published, unarchived inventions the acting party manages: the only ones a need or a raise may reference. */
export async function publishedInventions(): Promise<{ id: string; title: string }[]> {
  const inventions = await serverGet<InventionSummary[]>('/api/v1/inventions');
  return inventions.filter((item) => item.published_number && item.status !== 'ARCHIVED').map((item) => ({ id: item.id, title: item.title || 'Inovasi tanpa judul' }));
}

export async function fundingOn(): Promise<boolean> {
  return (await readCapabilities())?.includes('company_funding') ?? false;
}

/** Reads one owned record, or shows the not-found page. */
export async function ownedOr404<T>(path: `/${string}`): Promise<T> {
  try {
    return await serverGet<T>(path);
  } catch (error) {
    if (error instanceof ApiError && error.code === 'NOT_FOUND') notFound();
    throw error;
  }
}

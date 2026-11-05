import type { Metadata } from 'next';

import { ApiError } from '@/api/errors';
import { serverGet } from '@/api/server';
import type { Invention, PublicInvention } from '@/features/portfolio/model';
import { requireMe } from '@/features/session';
import { InventionView } from '@/views/portfolio/InventionViews';

export const metadata: Metadata = { title: 'Inovasi' };

type Props = { params: Promise<{ id: string }>; searchParams: Promise<{ terbit?: string }> };

async function orNull<T>(read: Promise<T>): Promise<T | null> {
  try {
    return await read;
  } catch (error) {
    if (error instanceof ApiError && error.code === 'NOT_FOUND') return null;
    throw error;
  }
}

/** The owner sees draft and history; everyone else sees only the published version. */
export default async function InventionPage({ params, searchParams }: Props) {
  const { id } = await params;
  const me = await requireMe(`/inventions/${id}`);
  const path = `/api/v1/inventions/${encodeURIComponent(id)}` as const;
  const invention = await orNull(serverGet<Invention>(path));
  const publicView = invention ? null : await orNull(serverGet<PublicInvention>(`${path}/public`));
  const terbit = Number((await searchParams).terbit);
  return (
    <InventionView
      me={me}
      invention={invention ?? undefined}
      publicView={publicView ?? undefined}
      justPublished={Number.isInteger(terbit) && terbit > 0 ? terbit : undefined}
    />
  );
}

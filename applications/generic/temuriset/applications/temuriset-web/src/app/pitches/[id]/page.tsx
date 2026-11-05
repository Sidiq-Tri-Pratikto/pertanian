import type { Metadata } from 'next';

import { ownedOr404 } from '@/features/needs/server';
import type { Pitch } from '@/features/pitches/model';
import { requireMe } from '@/features/session';
import { PitchView } from '@/views/pitches/PitchView';

export const metadata: Metadata = { title: 'Pitching' };

type Props = { params: Promise<{ id: string }>; searchParams: Promise<{ terkirim?: string }> };

export default async function PitchPage({ params, searchParams }: Props) {
  const { id } = await params;
  const me = await requireMe(`/pitches/${id}`);
  const pitch = await ownedOr404<Pitch>(`/api/v1/pitches/${encodeURIComponent(id)}`);
  return <PitchView me={me} pitch={pitch} justSent={(await searchParams).terkirim === '1'} />;
}

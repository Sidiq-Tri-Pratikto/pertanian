import type { Metadata } from 'next';
import { notFound } from 'next/navigation';

import { readSource } from '@/features/discovery/model';
import { requireMe } from '@/features/session';
import { PreflightView } from '@/views/pitches/PreflightView';

export const metadata: Metadata = { title: 'Periksa sebelum mengirim' };

type Props = { searchParams: Promise<{ source?: string; target?: string }> };

export default async function NewPitchPage({ searchParams }: Props) {
  const { source: raw, target } = await searchParams;
  const me = await requireMe(`/pitches/new?source=${encodeURIComponent(raw ?? '')}&target=${encodeURIComponent(target ?? '')}`);
  const source = readSource(raw);
  if (!source || !target || !/^[0-9a-f-]{36}$/.test(target)) notFound();
  return <PreflightView me={me} source={source} targetId={target} />;
}

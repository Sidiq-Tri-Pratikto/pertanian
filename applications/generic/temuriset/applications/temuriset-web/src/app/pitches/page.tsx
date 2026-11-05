import type { Metadata } from 'next';

import { serverGet } from '@/api/server';
import { readCapabilities } from '@/features/capabilities';
import type { PitchSummary } from '@/features/pitches/model';
import { personaOf, requireMe } from '@/features/session';
import { PitchesView } from '@/views/pitches/PitchesView';

export const metadata: Metadata = { title: 'Pitching' };

type Props = { searchParams: Promise<{ box?: string }> };

export default async function PitchesPage({ searchParams }: Props) {
  const me = await requireMe('/pitches');
  const persona = personaOf(me);
  const { box } = await searchParams;
  const view = persona === 'mitra' ? (box === 'diskusi' ? 'diskusi' : 'masuk') : 'outgoing';
  const pitches = await serverGet<PitchSummary[]>(`/api/v1/pitches?box=${view === 'outgoing' ? 'outgoing' : 'incoming'}`);
  const shown = view === 'diskusi' ? pitches.filter((pitch) => pitch.status === 'APPROVED_FOR_DISCUSSION') : pitches;
  return <PitchesView me={me} box={view} pitches={shown} capabilities={await readCapabilities()} />;
}

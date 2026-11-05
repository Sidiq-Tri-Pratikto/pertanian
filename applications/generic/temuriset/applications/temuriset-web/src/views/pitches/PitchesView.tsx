import NextLink from 'next/link';

import type { Me } from '@/api/client';
import { EmptyState } from '@/components/tr/EmptyState';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import { ContextBar } from '@/features/ContextBar';
import { readPersona } from '@/features/persona';
import { PITCH_STATUS, SOURCE_KIND, type PitchSummary } from '@/features/pitches/model';
import { FeatureList, PROVENANCE } from '@/views/parts';
import type { Capabilities } from '@/features/registry';

type Box = 'outgoing' | 'masuk' | 'diskusi';

const COPY: Record<Box, { title: string; subtitle: string; nav: string; empty: string; body: string; features: string[] }> = {
  outgoing: {
    title: 'Pitching dan Diskusi',
    subtitle: 'Pitching yang Anda kirim dan statusnya.',
    nav: 'pitching',
    empty: 'Belum ada pitching',
    body: 'Pitching dikirim dari halaman kecocokan, setelah Anda memeriksa semuanya.',
    features: ['keputusan-revisi', 'diskusi', 'jadwal', 'kerja-sama'],
  },
  masuk: {
    title: 'Pitching Masuk',
    subtitle: 'Pitching yang dikirim kepada Anda.',
    nav: 'masuk',
    empty: 'Belum ada pitching masuk',
    body: 'Pitching muncul di sini setelah inovator mengirimnya ke mandat Anda.',
    features: ['keputusan-revisi'],
  },
  diskusi: {
    title: 'Diskusi dan Jadwal',
    subtitle: 'Pitching yang sudah disetujui untuk diskusi.',
    nav: 'diskusi',
    empty: 'Belum ada diskusi',
    body: 'Diskusi dimulai setelah Anda menyetujui sebuah pitching untuk diskusi.',
    features: ['diskusi', 'jadwal', 'kerja-sama', 'kalender'],
  },
};

type Props = { me: Me; box: Box; pitches: PitchSummary[]; capabilities: Capabilities };

/** S12 lists: sent pitches for inventors, incoming and discussion boxes for partners. */
export function PitchesView({ me, box, pitches, capabilities }: Props) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  const copy = COPY[box];
  const incoming = box !== 'outgoing';
  return (
    <Screen persona={persona} current={copy.nav} title={copy.title} subtitle={copy.subtitle} provenance={PROVENANCE} context={<ContextBar me={me} />}>
      {pitches.length ? (
        <ul className="tr-stack">
          {pitches.map((pitch) => (
            <li key={pitch.id} className="tr-panel tr-stack">
              <p className="tr-muted tr-sys-type-support">{`${SOURCE_KIND[pitch.subject_type]} · ${incoming ? `dari ${pitch.requester_name}` : `kepada ${pitch.recipient_name}`}`}</p>
              <h2 className="tr-sys-type-heading-sm">
                <NextLink className="tr-link" href={`/pitches/${pitch.id}`}>
                  {`${pitch.subject_title} → ${pitch.opportunity_title}`}
                </NextLink>
              </h2>
              <p>
                <Status tone="neutral" label={PITCH_STATUS[pitch.status] ?? pitch.status} />
              </p>
            </li>
          ))}
        </ul>
      ) : (
        <EmptyState icon={incoming ? 'inbox' : 'chat'} title={copy.empty}>
          {copy.body}
        </EmptyState>
      )}
      <FeatureList ids={copy.features} capabilities={capabilities} />
    </Screen>
  );
}

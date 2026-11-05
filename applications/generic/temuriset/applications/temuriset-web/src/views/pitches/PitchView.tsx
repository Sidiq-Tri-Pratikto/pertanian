import NextLink from 'next/link';

import type { Me } from '@/api/client';
import { NextStep } from '@/components/tr/NextStep';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import { ContextBar } from '@/features/ContextBar';
import { readPersona } from '@/features/persona';
import { PITCH_STATUS, SOURCE_KIND, type Pitch } from '@/features/pitches/model';
import { PROVENANCE } from '@/views/parts';

type Props = { me: Me; pitch: Pitch; justSent: boolean };

/** One pitch as sent: who, to whom, what was frozen, and whose turn it is. Decisions arrive in 025. */
export function PitchView({ me, pitch, justSent }: Props) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  const mine = pitch.requester_party_id === me.active_party_id;
  const latest = pitch.submissions[pitch.submissions.length - 1];
  const snapshot = (latest?.snapshot ?? {}) as { opportunity?: { version?: number }; inventions?: { title: string; number: number }[] };
  return (
    <Screen
      persona={persona}
      current={mine ? 'pitching' : 'masuk'}
      title={`${pitch.subject_title} → ${pitch.opportunity_title}`}
      subtitle={`${SOURCE_KIND[pitch.subject_type]} · ${mine ? `kepada ${pitch.recipient_name}` : `dari ${pitch.requester_name}`}`}
      provenance={PROVENANCE}
      context={<ContextBar me={me} />}
      back={
        <NextLink className="tr-link" href={mine ? '/pitches' : '/pitches?box=masuk'}>
          Kembali ke daftar
        </NextLink>
      }>
      {justSent ? <Status tone="success" label={`Pitching terkirim kepada ${pitch.recipient_name}`} live /> : null}
      <p>
        <Status tone="neutral" label={PITCH_STATUS[pitch.status] ?? pitch.status} />
      </p>
      <NextStep who={mine ? 'other' : 'you'} title={mine ? `Menunggu ${pitch.recipient_name} meninjau` : 'Tinjau pitching ini'}>
        {mine ? 'Anda akan diberi tahu saat ada keputusan atau permintaan revisi.' : 'Keputusan dan permintaan revisi segera hadir.'}
      </NextStep>
      {latest ? (
        <section className="tr-panel tr-stack" aria-labelledby="kiriman">
          <h2 id="kiriman" className="tr-sys-type-heading-sm">{`Kiriman ${latest.number}`}</h2>
          <p className="tr-muted tr-sys-type-support">
            {[
              snapshot.opportunity?.version ? `Mandat versi ${snapshot.opportunity.version}` : null,
              ...(snapshot.inventions ?? []).map((invention) => `${invention.title} versi ${invention.number}`),
            ]
              .filter(Boolean)
              .join(' · ')}
          </p>
          <div className="tr-stack">
            {latest.brief.split('\n').map((line, index) => (
              <p key={index}>{line}</p>
            ))}
          </div>
          <h3 className="tr-sys-type-label">Berkas yang dibagikan</h3>
          {latest.files.length ? (
            <ul>
              {latest.files.map((file) => (
                <li key={`${file.document_id}-${file.version}`}>{`${file.title}, versi ${file.version}`}</li>
              ))}
            </ul>
          ) : (
            <p className="tr-muted">Tidak ada berkas yang dibagikan.</p>
          )}
        </section>
      ) : null}
    </Screen>
  );
}

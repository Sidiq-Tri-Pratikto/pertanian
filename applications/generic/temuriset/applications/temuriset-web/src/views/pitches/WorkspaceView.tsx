import NextLink from 'next/link';
import type { ReactNode } from 'react';

import type { Me } from '@/api/client';
import { Disclosure } from '@/components/tr/Disclosure';
import { EmptyState } from '@/components/tr/EmptyState';
import { NextStep } from '@/components/tr/NextStep';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import { ContextBar } from '@/features/ContextBar';
import { formatDateTime } from '@/features/organizations';
import { readPersona } from '@/features/persona';
import { PITCH_STATUS, SOURCE_KIND, type Pitch } from '@/features/pitches/model';
import { PitchActions } from '@/features/pitches/PitchActions';
import { RevisionPanel, type OwnFile } from '@/features/pitches/RevisionPanel';
import { turnOf, type TabId } from '@/features/pitches/workspace';
import { WorkspaceTabs } from '@/features/pitches/WorkspaceTabs';
import { reportHref } from '@/features/privacy/model';
import { PROVENANCE } from '@/views/parts';

type Submission = Pitch['submissions'][number];
type Snapshot = { opportunity?: { version?: number }; inventions?: { title: string; number: number }[] };

type Props = { me: Me; pitch: Pitch; tab: TabId; files: OwnFile[]; justSent: boolean };

function pins(submission: Submission): string {
  const snapshot = (submission.snapshot ?? {}) as Snapshot;
  return [snapshot.opportunity?.version ? `Mandat versi ${snapshot.opportunity.version}` : null, ...(snapshot.inventions ?? []).map((invention) => `${invention.title} versi ${invention.number}`)]
    .filter(Boolean)
    .join(' · ');
}

function Frozen({ submission }: { submission: Submission }) {
  return (
    <div className="tr-stack">
      <p className="tr-muted tr-sys-type-support">{pins(submission)}</p>
      <div className="tr-stack">
        {submission.brief.split('\n').map((line, index) => (
          <p key={index}>{line}</p>
        ))}
      </div>
    </div>
  );
}

function next(pitch: Pitch, mine: boolean, turn: 'you' | 'other' | null) {
  const other = mine ? pitch.recipient_name : pitch.requester_name;
  const round = pitch.rounds.find((item) => item.open);
  if (pitch.status === 'APPROVED_FOR_DISCUSSION') {
    return { who: 'you' as const, title: 'Diskusi terbuka', body: 'Persetujuan ini membuka diskusi; belum merupakan pendanaan atau kerja sama. Ruang diskusi dan jadwal segera hadir.' };
  }
  if (!turn) return null;
  if (turn === 'other') {
    return { who: 'other' as const, title: `Menunggu ${other}`, body: mine ? 'Anda akan diberi tahu saat ada keputusan atau permintaan revisi.' : 'Pengirim sedang menjawab permintaan revisi.' };
  }
  if (round) return { who: 'you' as const, title: `Jawab revisi putaran ${round.number}`, body: 'Jawab setiap pertanyaan wajib, lalu kirim ulang.' };
  return { who: 'you' as const, title: 'Tinjau pitching ini', body: 'Setujui untuk diskusi, minta revisi per butir, atau tolak dengan alasan singkat.' };
}

/** S13: one room for summary, revisions, documents and history, with whose turn it is above (UX-11). */
export function WorkspaceView({ me, pitch, tab, files, justSent }: Props) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  const mine = pitch.requester_party_id === me.active_party_id;
  const zone = me.account.time_zone;
  const latest = pitch.submissions[pitch.submissions.length - 1];
  const step = next(pitch, mine, turnOf(pitch, me.active_party_id));
  const rejection = [...pitch.decisions].reverse().find((decision) => decision.decision === 'REJECT');
  const shared = pitch.submissions.flatMap((submission) => submission.files.map((file) => ({ ...file, submission: submission.number })));
  const panels: Record<TabId, ReactNode> = {
    ringkasan: (
      <div className="tr-stack">
        <h2 className="tr-sys-type-heading-sm">{latest ? `Kiriman ${latest.number}` : 'Ringkasan'}</h2>
        {rejection?.reason ? (
          <Status tone="neutral" label="Alasan penolakan">
            <p>{rejection.reason}</p>
          </Status>
        ) : null}
        {latest ? <Frozen submission={latest} /> : null}
      </div>
    ),
    revisi: <RevisionPanel pitch={pitch} actingPartyId={me.active_party_id} files={files} />,
    dokumen: (
      <div className="tr-stack">
        <h2 className="tr-sys-type-heading-sm">Dokumen</h2>
        {shared.length ? (
          <ul>
            {shared.map((file) => (
              <li key={`${file.submission}-${file.document_id}-${file.version}`}>{`${file.title}, versi ${file.version} · kiriman ${file.submission}`}</li>
            ))}
          </ul>
        ) : (
          <p className="tr-muted">Tidak ada berkas yang dibagikan.</p>
        )}
      </div>
    ),
    diskusi: (
      <EmptyState icon="chat" title="Diskusi segera hadir">
        Pesan dan tugas untuk pitching ini akan tersedia di sini.
      </EmptyState>
    ),
    jadwal: (
      <EmptyState icon="calendar" title="Jadwal segera hadir">
        Usulan waktu pertemuan akan tersedia di sini setelah persetujuan.
      </EmptyState>
    ),
    riwayat: (
      <div className="tr-stack">
        <h2 className="tr-sys-type-heading-sm">Riwayat</h2>
        {pitch.submissions.map((submission) => (
          <Disclosure key={submission.number} label={`Kiriman ${submission.number} · ${formatDateTime(submission.submitted_at, zone)}`}>
            <Frozen submission={submission} />
          </Disclosure>
        ))}
        {pitch.decisions.length ? (
          <ul>
            {pitch.decisions.map((decision) => (
              <li key={decision.decided_at}>{`${decision.decision === 'APPROVE' ? 'Disetujui untuk diskusi' : 'Ditolak'} · kiriman ${decision.submission_number} · ${formatDateTime(decision.decided_at, zone)}`}</li>
            ))}
          </ul>
        ) : null}
      </div>
    ),
  };
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
      {step ? (
        <NextStep who={step.who} title={step.title}>
          {step.body}
        </NextStep>
      ) : null}
      <PitchActions pitch={pitch} actingPartyId={me.active_party_id} />
      <WorkspaceTabs pitchId={pitch.id} value={tab} panels={panels} />
      <p><NextLink className="tr-link" href={reportHref('PITCH', pitch.id)}>Laporkan</NextLink></p>
    </Screen>
  );
}

/** An unrelated account opening a room: nothing about the pitch, not even its title. */
export function NoAccessView({ me }: { me: Me }) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  return (
    <Screen persona={persona} current="pitching" title="Pitching" provenance={PROVENANCE} context={<ContextBar me={me} />}>
      <EmptyState icon="lock" title="Anda belum memiliki akses">
        Pitching ini hanya terlihat oleh pengirim dan penerimanya. Periksa konteks yang aktif.
      </EmptyState>
    </Screen>
  );
}

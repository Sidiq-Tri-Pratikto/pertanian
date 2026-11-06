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
import { DiscussionPanel, type Message, type Task } from '@/features/discussion/DiscussionPanel';
import { PitchActions } from '@/features/pitches/PitchActions';
import { RevisionPanel, type OwnFile } from '@/features/pitches/RevisionPanel';
import type { NextAction, TabId } from '@/features/pitches/workspace';
import { WorkspaceTabs } from '@/features/pitches/WorkspaceTabs';
import type { Schedule } from '@/features/scheduling/api';
import { SchedulePanel } from '@/features/scheduling/SchedulePanel';
import { PROVENANCE } from '@/views/parts';

type Submission = Pitch['submissions'][number];
type Snapshot = { opportunity?: { version?: number }; inventions?: { title: string; number: number }[] };

export type Room = { next: NextAction; schedule: Schedule; messages: Message[]; tasks: Task[] };

type Props = { me: Me; pitch: Pitch; tab: TabId; files: OwnFile[]; justSent: boolean; room: Room };

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

/** S13: one room for summary, revisions, documents and history, with whose turn it is above (UX-11). */
export function WorkspaceView({ me, pitch, tab, files, justSent, room }: Props) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  const mine = pitch.requester_party_id === me.active_party_id;
  const zone = me.account.time_zone;
  const latest = pitch.submissions[pitch.submissions.length - 1];
  const step = room.next;
  const ended = ['REJECTED', 'WITHDRAWN', 'CLOSED'].includes(pitch.status);
  const parties = [
    { id: pitch.requester_party_id, name: pitch.requester_name },
    { id: pitch.recipient_party_id, name: pitch.recipient_name },
  ];
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
    diskusi: <DiscussionPanel pitchId={pitch.id} open={!ended} messages={room.messages} tasks={room.tasks} parties={parties} actingPartyId={me.active_party_id} zone={zone} />,
    jadwal: <SchedulePanel pitchId={pitch.id} approved={pitch.status === 'APPROVED_FOR_DISCUSSION'} schedule={room.schedule} actingPartyId={me.active_party_id} zone={zone} />,
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
      {step.who ? (
        <NextStep who={step.who} title={step.title}>
          {step.text}
        </NextStep>
      ) : step.title && step.title !== PITCH_STATUS[pitch.status] ? (
        <p className="tr-sys-type-body-strong">{step.title}</p>
      ) : null}
      <PitchActions pitch={pitch} actingPartyId={me.active_party_id} />
      <WorkspaceTabs pitchId={pitch.id} value={tab} panels={panels} />
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

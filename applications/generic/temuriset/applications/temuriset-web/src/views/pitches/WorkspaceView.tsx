import NextLink from 'next/link';
import type { ReactNode } from 'react';

import type { Me } from '@/api/client';
import { Disclosure } from '@/components/tr/Disclosure';
import { EmptyState } from '@/components/tr/EmptyState';
import { NextStep } from '@/components/tr/NextStep';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import { TktBadge } from '@/components/tr/TktBadge';
import { ContextBar } from '@/features/ContextBar';
import { formatDateTime } from '@/features/organizations';
import { readPersona } from '@/features/persona';
import { PITCH_STATUS, SOURCE_KIND, type Pitch } from '@/features/pitches/model';
import { DiscussionPanel, type Message, type Task } from '@/features/discussion/DiscussionPanel';
import { PitchActions } from '@/features/pitches/PitchActions';
import { RevisionPanel, type OwnFile } from '@/features/pitches/RevisionPanel';
import { primaryFor, type NextAction, type TabId } from '@/features/pitches/workspace';
import { WorkspaceTabs } from '@/features/pitches/WorkspaceTabs';
import { reportHref } from '@/features/privacy/model';
import type { Partnership } from '@/features/relationships/model';
import type { Schedule } from '@/features/scheduling/api';
import { SchedulePanel } from '@/features/scheduling/SchedulePanel';
import { PROVENANCE } from '@/views/parts';
import { t } from '@/features/i18n/t';

type Submission = Pitch['submissions'][number];
type FrozenReadiness = { tkt_level?: number; note?: string | null; has_evidence?: boolean } | null;
type Snapshot = {
  opportunity?: { version?: number };
  inventions?: { title: string; number: number; readiness?: FrozenReadiness }[];
};

export type Room = { next: NextAction; schedule: Schedule; messages: Message[]; tasks: Task[]; relationship?: Partnership | null };

type Props = { me: Me; pitch: Pitch; tab: TabId; files: OwnFile[]; justSent: boolean; room: Room };

function pins(submission: Submission): string {
  const snapshot = (submission.snapshot ?? {}) as Snapshot;
  return [snapshot.opportunity?.version ? t('Mandat versi {n}', { n: snapshot.opportunity.version }) : null, ...(snapshot.inventions ?? []).map((invention) => t('{title} versi {n}', { title: invention.title, n: invention.number }))]
    .filter(Boolean)
    .join(' · ');
}

function Frozen({ submission }: { submission: Submission }) {
  const snapshot = (submission.snapshot ?? {}) as Snapshot;
  const readinessItems = (snapshot.inventions ?? []).filter((invention) => invention.readiness?.tkt_level);
  return (
    <div className="tr-stack">
      <p className="tr-muted tr-sys-type-support">{pins(submission)}</p>
      {readinessItems.map((invention) => (
        <TktBadge
          key={`${invention.title}-${invention.number}`}
          level={invention.readiness?.tkt_level}
          note={invention.readiness?.note}
          hasEvidence={invention.readiness?.has_evidence}
          showBar
          showMeta
        />
      ))}
      <div className="tr-stack">
        {submission.brief.split('\n').map((line, index) => (
          <p key={index}>{line}</p>
        ))}
      </div>
    </div>
  );
}

/**
 * S13: one room. Above the tabs: who, which mandate, which version and the status, then whose turn it is with one link
 * into the tab where the work is (UX-11). The six tabs keep their deep links.
 */
export function WorkspaceView({ me, pitch, tab, files, justSent, room }: Props) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  const mine = pitch.requester_party_id === me.active_party_id;
  const zone = me.account.time_zone;
  const latest = pitch.submissions[pitch.submissions.length - 1];
  const step = room.next;
  const primary = primaryFor(step, tab, pitch.id);
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
        <h2 className="tr-sys-type-heading-sm">{latest ? t('Kiriman {n}', { n: latest.number }) : t('Ringkasan')}</h2>
        {rejection?.reason ? (
          <Status tone="neutral" label={t('Alasan penolakan')}>
            <p>{rejection.reason}</p>
          </Status>
        ) : null}
        {latest ? <Frozen submission={latest} /> : null}
      </div>
    ),
    revisi: <RevisionPanel pitch={pitch} actingPartyId={me.active_party_id} files={files} />,
    dokumen: (
      <div className="tr-stack">
        <h2 className="tr-sys-type-heading-sm">{t('Dokumen')}</h2>
        {shared.length ? (
          <ul>
            {shared.map((file) => (
              <li key={`${file.submission}-${file.document_id}-${file.version}`}>{t('{title}, versi {n} · kiriman {s}', { title: file.title, n: file.version, s: file.submission })}</li>
            ))}
          </ul>
        ) : (
          <p className="tr-muted">{t('Tidak ada berkas yang dibagikan.')}</p>
        )}
      </div>
    ),
    diskusi: <DiscussionPanel pitchId={pitch.id} open={!ended} messages={room.messages} tasks={room.tasks} parties={parties} actingPartyId={me.active_party_id} zone={zone} />,
    jadwal: <SchedulePanel pitchId={pitch.id} approved={pitch.status === 'APPROVED_FOR_DISCUSSION'} schedule={room.schedule} actingPartyId={me.active_party_id} zone={zone} />,
    riwayat: (
      <div className="tr-stack">
        <h2 className="tr-sys-type-heading-sm">{t('Riwayat')}</h2>
        {pitch.submissions.map((submission) => (
          <Disclosure key={submission.number} label={t('Kiriman {n} · {time}', { n: submission.number, time: formatDateTime(submission.submitted_at, zone) })}>
            <Frozen submission={submission} />
          </Disclosure>
        ))}
        {pitch.decisions.length ? (
          <ul>
            {pitch.decisions.map((decision) => (
              <li key={decision.decided_at}>{`${decision.decision === 'APPROVE' ? t('Disetujui untuk diskusi') : t('Ditolak')} · ${t('kiriman {n}', { n: decision.submission_number })} · ${formatDateTime(decision.decided_at, zone)}`}</li>
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
      title={t('{subject} untuk {opportunity}', { subject: pitch.subject_title, opportunity: pitch.opportunity_title })}
      subtitle={`${t(SOURCE_KIND[pitch.subject_type])} · ${mine ? t('kepada {name}', { name: pitch.recipient_name }) : t('dari {name}', { name: pitch.requester_name })}`}
      provenance={PROVENANCE}
      context={<ContextBar me={me} />}
      back={
        <NextLink className="tr-link" href={mine ? '/pitches' : '/pitches?box=masuk'}>
          {t('Kembali ke daftar')}
        </NextLink>
      }>
      {justSent ? <Status tone="success" label={t('Pitching terkirim kepada {name}', { name: pitch.recipient_name })} live /> : null}
      <dl className="tr-facts" aria-label={t('Ringkasan pitching')}>
        <div>
          <dt className="tr-sys-type-support-strong">{mine ? t('Penerima') : t('Pengirim')}</dt>
          <dd>{mine ? pitch.recipient_name : pitch.requester_name}</dd>
        </div>
        <div>
          <dt className="tr-sys-type-support-strong">{t('Mandat')}</dt>
          <dd>{pitch.opportunity_title}</dd>
        </div>
        <div>
          <dt className="tr-sys-type-support-strong">{t('Versi aktif')}</dt>
          <dd>{latest ? t('Kiriman {n}', { n: latest.number }) : t('Belum dikirim')}</dd>
        </div>
        <div>
          <dt className="tr-sys-type-support-strong">{t('Status')}</dt>
          <dd>
            <Status tone="neutral" label={PITCH_STATUS[pitch.status] ?? pitch.status} />
          </dd>
        </div>
      </dl>
      {step.who ? (
        <NextStep
          who={step.who}
          title={step.title}
          action={
            primary ? (
              <NextLink className="tr-btn tr-btn--primary" href={primary.href}>
                {primary.label}
              </NextLink>
            ) : undefined
          }>
          {step.text}
        </NextStep>
      ) : step.title && step.title !== t(PITCH_STATUS[pitch.status] ?? '') ? (
        <p className="tr-sys-type-body-strong">{step.title}</p>
      ) : null}
      <PitchActions pitch={pitch} actingPartyId={me.active_party_id} />
      {room.relationship ? (
        <div className="tr-row">
          <NextLink className="tr-link" href={`/partnerships/${room.relationship.id}`}>{t('Lihat ringkasan Kerja Sama')}</NextLink>
        </div>
      ) : step.action === 'propose_partnership' && me.capabilities?.includes('confirm_relationship') ? (
        <div className="tr-row">
          <NextLink className="tr-btn tr-btn--primary" href={`/partnerships/new?pitch=${pitch.id}`}>{t('Usulkan ringkasan')}</NextLink>
        </div>
      ) : null}
      <WorkspaceTabs pitchId={pitch.id} value={tab} panels={panels} />
      <p><NextLink className="tr-link" href={reportHref('PITCH', pitch.id)}>{t('Laporkan')}</NextLink></p>
    </Screen>
  );
}

/** An unrelated account opening a room: nothing about the pitch, not even its title. */
export function NoAccessView({ me }: { me: Me }) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  return (
    <Screen persona={persona} current="pitching" title={t('Pitching')} provenance={PROVENANCE} context={<ContextBar me={me} />}>
      <EmptyState icon="lock" title={t('Anda belum memiliki akses')}>
        {t('Pitching ini hanya terlihat oleh pengirim dan penerimanya. Periksa konteks yang aktif.')}
      </EmptyState>
    </Screen>
  );
}

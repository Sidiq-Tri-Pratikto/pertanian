'use client';

import NextLink from 'next/link';
import { useRouter } from 'next/navigation';
import { useRef, useState } from 'react';

import { newIdempotencyKey } from '@/api/client';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Dialog } from '@/components/tr/Dialog';
import { ErrorSummary } from '@/components/tr/ErrorSummary';
import { Status } from '@/components/tr/Status';
import { TextArea } from '@/components/tr/TextArea';
import { VersionConflict } from '@/components/tr/VersionConflict';
import type { Pitch } from '@/features/pitches/model';
import { closeDiscussion, decide, moveTo } from '@/features/pitches/workspace';

type Kind = 'approve' | 'reject' | 'withdraw' | 'close';

const TERMINAL = ['REJECTED', 'WITHDRAWN', 'CLOSED'];

const DIALOG: Record<Kind, { title: string; confirm: string; busy: string; reason?: { label: string; hint: string; missing: string } }> = {
  approve: { title: 'Setujui untuk diskusi', confirm: 'Setujui untuk diskusi', busy: 'Menyetujui…' },
  reject: {
    title: 'Tolak pitching',
    confirm: 'Tolak pitching',
    busy: 'Menolak…',
    reason: { label: 'Alasan singkat', hint: 'Hanya terlihat oleh pengirim pitching. Penolakan tidak menurunkan reputasi publik.', missing: 'Tuliskan alasan singkat.' },
  },
  withdraw: { title: 'Tarik pitching', confirm: 'Tarik pitching', busy: 'Menarik…' },
  close: {
    title: 'Tutup diskusi',
    confirm: 'Tutup diskusi',
    busy: 'Menutup…',
    reason: { label: 'Alasan penutupan', hint: 'Kedua pihak dapat membaca alasan ini.', missing: 'Tuliskan alasan penutupan.' },
  },
};

type Props = { pitch: Pitch; actingPartyId: string };

/** The decision region of S13: one dialog per consequential action, each naming who acts and what it means. */
export function PitchActions({ pitch, actingPartyId }: Props) {
  const router = useRouter();
  const mine = pitch.requester_party_id === actingPartyId;
  const actor = mine ? pitch.requester_name : pitch.recipient_name;
  const allowed = pitch.allowed_actions;
  const [open, setOpen] = useState<Kind | null>(null);
  const [reason, setReason] = useState('');
  const [reasonError, setReasonError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<ApiError | null>(null);
  const [attempt, setAttempt] = useState(0);
  // One key per intent; kept across retries until the service gives a final answer.
  const key = useRef(newIdempotencyKey());

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    setFailure(null);
    try {
      await action();
      key.current = newIdempotencyKey();
      setOpen(null);
      router.refresh();
    } catch (error) {
      const failed = ApiError.from(error);
      if (!failed.recovery.retryable) key.current = newIdempotencyKey();
      setFailure(failed);
      setOpen(null);
      setAttempt((value) => value + 1);
    } finally {
      setBusy(false);
    }
  }

  function confirm(kind: Kind) {
    const needs = DIALOG[kind].reason;
    if (needs && !reason.trim()) {
      setReasonError(needs.missing);
      return;
    }
    setReasonError(null);
    void run(() => {
      if (kind === 'approve') return decide(pitch, actingPartyId, 'APPROVE', null, key.current);
      if (kind === 'reject') return decide(pitch, actingPartyId, 'REJECT', reason.trim(), key.current);
      if (kind === 'close') return closeDiscussion(pitch, actingPartyId, reason.trim(), key.current);
      return moveTo(pitch, actingPartyId, 'withdraw', key.current);
    });
  }

  function openDialog(kind: Kind) {
    setReason('');
    setReasonError(null);
    setOpen(kind);
  }

  const viewOnly = !allowed.length && !TERMINAL.includes(pitch.status);
  const dialog = open ? DIALOG[open] : null;
  return (
    <section className="tr-stack" aria-label="Tindakan pitching">
      {failure?.code === 'STALE_VERSION' ? (
        <VersionConflict what="Pitching ini baru saja berubah. Muat versi terbaru sebelum memutuskan." onRefresh={() => { setFailure(null); router.refresh(); }} refreshLabel="Muat versi terbaru" />
      ) : failure ? (
        <ErrorSummary title="Tindakan belum tersimpan" focusKey={attempt} id="pitch-action-errors">
          <p>{failure.message}</p>
          {failure.requestId ? <p className="tr-muted tr-sys-type-support">{`ID referensi: ${failure.requestId}`}</p> : null}
        </ErrorSummary>
      ) : null}
      {viewOnly ? <Status tone="neutral" label="Akun Anda hanya dapat melihat pitching ini" /> : null}
      <div className="tr-row">
        {allowed.includes('approve') ? (
          <Button intent="primary" id="action-approve" onClick={() => openDialog('approve')}>
            Setujui untuk diskusi
          </Button>
        ) : null}
        {allowed.includes('request_revision') ? (
          <NextLink className="tr-btn tr-btn--secondary" href={`/pitches/${pitch.id}?tab=revisi`}>
            Minta revisi
          </NextLink>
        ) : null}
        {allowed.includes('begin_review') ? (
          <Button busy={busy && !open} busyLabel="Menyimpan…" onClick={() => void run(() => moveTo(pitch, actingPartyId, 'begin-review', key.current))}>
            Mulai tinjau
          </Button>
        ) : null}
        {allowed.includes('reject') ? (
          <Button intent="danger" id="action-reject" onClick={() => openDialog('reject')}>
            Tolak
          </Button>
        ) : null}
        {allowed.includes('withdraw') ? (
          <Button intent="danger" id="action-withdraw" onClick={() => openDialog('withdraw')}>
            Tarik pitching
          </Button>
        ) : null}
        {allowed.includes('close') ? (
          <Button id="action-close" onClick={() => openDialog('close')}>
            Tutup diskusi
          </Button>
        ) : null}
      </div>
      <Dialog
        open={open !== null}
        onClose={() => setOpen(null)}
        title={dialog?.title ?? ''}
        returnFocusId={open ? `action-${open}` : undefined}
        primary={open ? { label: dialog!.confirm, onClick: () => confirm(open), busy, busyLabel: dialog!.busy, intent: open === 'approve' ? 'primary' : 'danger' } : undefined}>
        <p>{`Anda bertindak sebagai ${actor}.`}</p>
        {open === 'approve' ? <p>Persetujuan ini membuka diskusi; belum merupakan pendanaan atau kerja sama.</p> : null}
        {open === 'withdraw' ? <p>Pitching yang ditarik tidak dapat diputuskan lagi dan tidak dibuka kembali.</p> : null}
        {dialog?.reason ? (
          <TextArea label={dialog.reason.label} hint={dialog.reason.hint} required rows={3} value={reason} onChange={setReason} error={reasonError ?? undefined} limit={500} id="action-reason" />
        ) : null}
      </Dialog>
    </section>
  );
}

'use client';

import NextLink from 'next/link';
import { useRouter } from 'next/navigation';
import { useRef, useState } from 'react';

import { newIdempotencyKey } from '@/api/client';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Dialog } from '@/components/tr/Dialog';
import { Status } from '@/components/tr/Status';
import { moveMandate, type MandateAction } from '@/features/intake/api';
import type { Mandate } from '@/features/intake/model';
import { t } from '@/features/i18n/t';

const FAILURE_LABEL: Record<MandateAction, string> = {
  activate: 'Mandat belum diaktifkan',
  pause: 'Penerimaan belum dijeda',
  close: 'Penerimaan belum ditutup',
};

/** What the owner can do to one mandate. Closing cannot be undone, so it asks first. */
export function MandateActions({ mandate, actingPartyId }: { mandate: Mandate; actingPartyId: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState<MandateAction | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [failure, setFailure] = useState<{ label: string; message: string } | null>(null);
  const pending = useRef<{ action: MandateAction; key: string } | null>(null);

  async function move(action: MandateAction) {
    if (busy) return;
    if (pending.current?.action !== action) pending.current = { action, key: newIdempotencyKey() };
    setBusy(action);
    setFailure(null);
    try {
      await moveMandate(mandate.id, action, actingPartyId, mandate.version, pending.current.key);
      pending.current = null;
      setConfirming(false);
      router.refresh();
    } catch (error) {
      const apiError = ApiError.from(error);
      // Only a request that may not have arrived is retried with the same key; anything the service refused is not.
      if (!apiError.recovery.retryable) pending.current = null;
      setConfirming(false);
      setFailure({ label: FAILURE_LABEL[action], message: `${apiError.message} ${t('Kode rujukan: {id}.', { id: apiError.requestId ?? '-' })}` });
    } finally {
      setBusy(null);
    }
  }

  if (mandate.status === 'CLOSED' || mandate.status === 'EXPIRED') return null;
  return (
    <div className="tr-stack">
      {failure ? (
        <Status tone="danger" icon="alert" label={failure.label} live="alert">
          <p>{failure.message}</p>
        </Status>
      ) : null}
      <div className="tr-row">
        <NextLink className="tr-btn tr-btn--secondary" href={`/opportunities/${mandate.id}/edit`}>
          {t('Ubah mandat')}<span className="tr-sr">{` ${mandate.title || t('tanpa judul')}`}</span>
        </NextLink>
        {mandate.status === 'ACTIVE' ? (
          <Button busy={busy === 'pause'} busyLabel={t('Menjeda…')} onClick={() => move('pause')}>
            {t('Jeda penerimaan')}
          </Button>
        ) : null}
        {mandate.status === 'PAUSED' ? (
          <Button busy={busy === 'activate'} busyLabel={t('Mengaktifkan…')} onClick={() => move('activate')}>
            {t('Aktifkan lagi')}
          </Button>
        ) : null}
        {mandate.status === 'ACTIVE' || mandate.status === 'PAUSED' ? <Button onClick={() => setConfirming(true)}>{t('Tutup penerimaan')}</Button> : null}
      </div>
      <Dialog
        open={confirming}
        onClose={() => setConfirming(false)}
        title={t('Tutup penerimaan {title}?', { title: mandate.title })}
        primary={{ label: t('Tutup penerimaan'), intent: 'danger', busy: busy === 'close', busyLabel: t('Menutup…'), onClick: () => move('close') }}>
        <p>{t('Pitching baru berhenti, dan mandat ini tidak dapat dibuka kembali. Pitching yang sudah terkirim tidak berubah.')}</p>
      </Dialog>
    </div>
  );
}

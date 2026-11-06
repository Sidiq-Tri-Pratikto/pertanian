'use client';

import { useRouter } from 'next/navigation';
import { useRef, useState } from 'react';

import { getJson, newIdempotencyKey, send } from '@/api/client';
import { ApiError } from '@/api/errors';
import type { components } from '@/api/schema.generated';
import { Button } from '@/components/tr/Button';
import { Checkbox } from '@/components/tr/Checkbox';
import { Status } from '@/components/tr/Status';
import { VersionConflict } from '@/components/tr/VersionConflict';

export type CalendarStatus = components['schemas']['CalendarStatusResponse'];
type Connected = components['schemas']['CalendarConnectResponse'];
type Disconnected = components['schemas']['CalendarDisconnectResponse'];
type Failure = { message: string; requestId: string | null };

const STATE_LABEL: Record<CalendarStatus['state'], string> = {
  off: 'Kalender luar belum tersedia',
  off_with_connection: 'Kalender luar sedang nonaktif. Anda masih dapat menghapus sambungan ini dari TemuRiset.',
  disconnected: 'Kalender belum tersambung',
  pending: 'Menunggu persetujuan kalender',
  connected: 'Kalender tersambung',
  expired: 'Sambungan kalender kedaluwarsa',
};

const DISCONNECT_LABEL: Record<NonNullable<CalendarStatus['revocation']>, string> = {
  confirmed: 'Kalender terputus. Akses juga sudah dicabut di kalender.',
  not_required: 'Kalender terputus dari TemuRiset.',
  unconfirmed: 'Kalender terputus dari TemuRiset. Periksa pencabutan akses di pengaturan kalender Anda.',
};

export type CalendarConnectionProps = {
  initial: CalendarStatus | null;
  initialFailure?: Failure | null;
  callbackFailure?: Failure | null;
};

/** The account's explicit, read-only consent and local disconnect controls in S18. */
export function CalendarConnection({ initial, initialFailure, callbackFailure }: CalendarConnectionProps) {
  const router = useRouter();
  const [status, setStatus] = useState(initial);
  const [consent, setConsent] = useState(false);
  const [continuation, setContinuation] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(initial?.revocation ? DISCONNECT_LABEL[initial.revocation] : null);
  const [failure, setFailure] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  const intent = useRef<{ action: string; key: string } | null>(null);

  if (status?.state === 'off' && !notice) return null;

  async function change(action: 'connect' | 'disconnect') {
    if (!status || busy) return;
    setBusy(true);
    setFailure(null);
    setNotice(null);
    if (intent.current?.action !== action) intent.current = { action, key: newIdempotencyKey() };
    const options = { idempotencyKey: intent.current.key };
    const body = { expected_version: status.version };
    try {
      if (action === 'connect') {
        const result = await send<Connected>('POST', '/api/v1/me/calendar/connect', { ...body, consent: true }, options);
        if (result.authorization_path !== '/api/v1/me/calendar/connect') throw ApiError.unexpected();
        setStatus(result);
        setContinuation(`${result.authorization_path}?version=${result.version}`);
      } else {
        const result = await send<Disconnected>('POST', '/api/v1/me/calendar/disconnect', body, options);
        setStatus(result);
        setContinuation(null);
        setConsent(false);
        const latest = result.revocation === 'unconfirmed' && result.state !== 'off'
          ? await getJson('/api/v1/me/calendar').catch(() => null)
          : null;
        if (latest) setStatus(latest);
        const revocation = latest?.version === result.version ? latest.revocation ?? result.revocation : result.revocation;
        setNotice(DISCONNECT_LABEL[revocation]);
      }
      intent.current = null;
    } catch (cause) {
      const error = ApiError.from(cause);
      if (!error.recovery.retryable) intent.current = null;
      setFailure(error);
    } finally {
      setBusy(false);
    }
  }

  const shownFailure = failure ?? initialFailure ?? callbackFailure;
  return (
    <section id="kalender" className="tr-panel tr-stack" aria-labelledby="judul-kalender">
      <h2 id="judul-kalender" className="tr-sys-type-heading-sm">Kalender luar</h2>
      {status ? <Status label={STATE_LABEL[status.state]} tone={status.state === 'connected' ? 'success' : 'neutral'} live /> : null}
      {notice ? <Status label={notice} live /> : null}
      {failure?.code === 'STALE_VERSION' ? (
        <VersionConflict what="Sambungan kalender sudah berubah." onRefresh={() => router.refresh()} refreshLabel="Muat status terbaru" />
      ) : null}
      {shownFailure ? (
        <Status tone="danger" label={shownFailure.message} live="alert">
          {shownFailure.requestId ? <p>ID referensi {shownFailure.requestId}</p> : null}
          {!status ? <Button onClick={() => router.refresh()}>Muat status kalender</Button> : null}
        </Status>
      ) : null}
      {status && ['disconnected', 'pending', 'expired'].includes(status.state) && !continuation ? (
        <>
          <p>Gunakan kalender uji lokal. TemuRiset hanya membaca waktu sibuk atau kosong pada pilihan jadwal pertemuan Anda.</p>
          <Checkbox label="Saya setuju TemuRiset membaca waktu sibuk atau kosong dari kalender uji saya." checked={consent} onChange={setConsent} />
          <Button intent="primary" busy={busy} disabledReason={consent ? null : 'Berikan persetujuan terlebih dahulu.'} onClick={() => void change('connect')}>
            {status.state === 'pending' ? 'Mulai ulang sambungan' : 'Siapkan sambungan kalender'}
          </Button>
        </>
      ) : null}
      {continuation ? <a className="tr-btn tr-btn--primary" href={continuation} referrerPolicy="no-referrer">Lanjut ke kalender uji</a> : null}
      {status && ['connected', 'pending', 'expired', 'off_with_connection'].includes(status.state) ? (
        <Button busy={busy} onClick={() => void change('disconnect')}>Putuskan sambungan kalender</Button>
      ) : null}
    </section>
  );
}

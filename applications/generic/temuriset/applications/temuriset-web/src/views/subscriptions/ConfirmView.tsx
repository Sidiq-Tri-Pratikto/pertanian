'use client';

import Link from 'next/link';
import { useState } from 'react';

import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Status } from '@/components/tr/Status';
import { confirmSubscription, type Subscription } from '@/features/subscriptions/api';
import { AuthShell } from '@/views/AuthShell';

/** Opening the link confirms nothing; the investor presses the button, so mail scanners cannot subscribe anyone. */
export function ConfirmView({ token }: { token: string }) {
  const [done, setDone] = useState<Subscription | null>(null);
  const [failure, setFailure] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);

  async function confirm() {
    setBusy(true);
    setFailure(null);
    try {
      setDone(await confirmSubscription(token));
    } catch (error) {
      setFailure(ApiError.from(error));
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <AuthShell title="Langganan aktif" subtitle={done.email}>
        <Status tone="success" label="Kabar inovasi akan dikirim ke email ini" live />
        <p>Inovasi yang sangat sesuai minat Anda dikirim langsung. Sisanya dirangkum setiap Senin pukul 09.00 WIB.</p>
        {done.manage_token ? (
          <p>
            <Link className="tr-link" href={`/langganan/atur?token=${encodeURIComponent(done.manage_token)}`}>
              Ubah minat atau berhenti berlangganan
            </Link>
          </p>
        ) : null}
      </AuthShell>
    );
  }
  return (
    <AuthShell title="Konfirmasi langganan" subtitle="Tekan tombol di bawah untuk mulai menerima kabar inovasi.">
      {failure ? (
        <Status tone="danger" icon="alert" label={failure.code === 'NOT_FOUND' ? 'Tautan tidak berlaku' : 'Belum terkonfirmasi'} live="alert">
          <p>{failure.code === 'NOT_FOUND' ? 'Tautan ini sudah dipakai atau kedaluwarsa. Berlangganan lagi untuk tautan baru.' : failure.message}</p>
        </Status>
      ) : null}
      <div className="tr-row">
        <Button intent="primary" busy={busy} busyLabel="Mengonfirmasi…" onClick={() => void confirm()}>
          Konfirmasi langganan
        </Button>
      </div>
      <p>
        <Link className="tr-link" href="/langganan">
          Berlangganan dengan email lain
        </Link>
      </p>
    </AuthShell>
  );
}

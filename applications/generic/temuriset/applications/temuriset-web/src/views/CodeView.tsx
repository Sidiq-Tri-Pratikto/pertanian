'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState, useSyncExternalStore, type FormEvent } from 'react';

import { send, type Me } from '@/api/client';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { ErrorSummary } from '@/components/tr/ErrorSummary';
import { Status } from '@/components/tr/Status';
import { TextField } from '@/components/tr/TextField';
import { forgetPersona } from '@/features/actions';
import { homeFor, readPersona } from '@/features/persona';
import { clearPending, codeRequest, parsePending, readPendingRaw } from '@/features/signIn';
import { AuthShell } from '@/views/AuthShell';

function noSubscription() {
  return () => {};
}

/**
 * The code step of S01: where the code went, the code field, and a resend that respects the rate limit (FR-002).
 * A wrong code focuses the error summary, states the attempts left and keeps the typed code (UX-09).
 */
export function CodeView() {
  const router = useRouter();
  // The hand-off lives in this tab's sessionStorage; the server renders nothing until the browser reads it.
  const raw = useSyncExternalStore(noSubscription, readPendingRaw, () => undefined);
  const pending = raw === undefined ? null : parsePending(raw);
  const [code, setCode] = useState('');
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [failure, setFailure] = useState<{ message: string; resend: boolean } | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [busy, setBusy] = useState(false);
  const [resent, setResent] = useState(false);

  useEffect(() => {
    if (raw !== undefined && !parsePending(raw)) router.replace('/start');
  }, [raw, router]);

  if (!pending) return null;

  function fail(message: string, resend: boolean, field: string | null = null) {
    setFieldError(field);
    setFailure({ message, resend });
    setAttempt((count) => count + 1);
  }

  async function verify(event: FormEvent) {
    event.preventDefault();
    if (busy || !pending) return;
    if (!/^\d{6}$/.test(code.trim())) {
      fail('Isi kode verifikasi enam angka dari email Anda.', false, 'Isi kode verifikasi enam angka dari email Anda.');
      return;
    }
    setBusy(true);
    setResent(false);
    try {
      const me = await send<Me>('POST', '/api/v1/auth/verify', { email: pending.email, code: code.trim() });
      await forgetPersona();
      clearPending();
      router.replace(pending.returnTo ?? homeFor(readPersona(me.account.persona) ?? 'inovator'));
      router.refresh();
    } catch (error) {
      const apiError = ApiError.from(error);
      setBusy(false);
      if (apiError.code === 'CODE_INVALID') {
        const left = `Kode tidak cocok. Sisa percobaan: ${apiError.attemptsLeft ?? 0}.`;
        fail(left, apiError.attemptsLeft === 0, left);
      } else {
        fail(apiError.message, apiError.code === 'CODE_EXPIRED');
      }
    }
  }

  async function resend() {
    if (!pending) return;
    try {
      await send('POST', '/api/v1/auth/code', codeRequest(pending));
      setFailure(null);
      setFieldError(null);
      setResent(true);
    } catch (error) {
      const apiError = ApiError.from(error);
      const wait = apiError.recovery.retry_after_seconds;
      fail(wait ? `${apiError.message} Kode baru dapat diminta dalam ${Math.ceil(wait / 60)} menit.` : apiError.message, false);
    }
  }

  return (
    <AuthShell title="Masukkan kode verifikasi" subtitle={`Kami mengirim kode enam angka ke ${pending.email}. Kode berlaku 10 menit.`}>
      {failure ? (
        <ErrorSummary
          errors={fieldError ? [{ fieldId: 'kode', message: fieldError }] : []}
          focusKey={attempt}
          retry={failure.resend ? { label: 'Kirim ulang kode', onClick: resend } : undefined}>
          {fieldError ? null : failure.message}
        </ErrorSummary>
      ) : null}
      {resent ? <Status tone="success" label="Kode baru sudah dikirim" live /> : null}
      <form onSubmit={verify} noValidate className="tr-panel tr-stack">
        <TextField
          id="kode"
          label="Kode verifikasi"
          hint="Enam angka dari email TemuRiset."
          value={code}
          onChange={setCode}
          error={fieldError}
          inputMode="numeric"
          autoComplete="one-time-code"
          required
        />
        <div className="tr-row">
          <Button type="submit" intent="primary" icon="arrow" busy={busy} busyLabel="Memeriksa…">
            Masuk
          </Button>
          <Button onClick={resend}>Kirim ulang kode</Button>
        </div>
      </form>
      <p>
        <Link className="tr-link" href={pending.purpose === 'sign_up' ? '/start' : '/start?masuk=1'}>
          Ubah email
        </Link>
      </p>
    </AuthShell>
  );
}

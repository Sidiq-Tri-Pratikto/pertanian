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
import { useLocale, useMessages } from '@/features/i18n/LocaleProvider';
import { localHref, rememberLocale } from '@/features/i18n/locale';

function noSubscription() {
  return () => {};
}

/**
 * The code step of S01: where the code went, the code field, and a resend that respects the rate limit (FR-002).
 * A wrong code focuses the error summary, states the attempts left and keeps the typed code (UX-09).
 */
export function CodeView() {
  const router = useRouter();
  const page = useLocale();
  const words = useMessages().code;
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
    if (raw !== undefined && !parsePending(raw)) router.replace(localHref(page, '/start'));
  }, [raw, router, page]);

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
      fail(words.invalidFormat, false, words.invalidFormat);
      return;
    }
    setBusy(true);
    setResent(false);
    try {
      const me = await send<Me>('POST', '/api/v1/auth/verify', { email: pending.email, code: code.trim() });
      await forgetPersona();
      clearPending();
      rememberLocale(page);
      router.replace(pending.returnTo ?? homeFor(readPersona(me.account.persona) ?? 'inovator'));
      router.refresh();
    } catch (error) {
      const apiError = ApiError.from(error);
      setBusy(false);
      if (apiError.code === 'CODE_INVALID') {
        const left = words.wrong(apiError.attemptsLeft ?? 0);
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
      fail(wait ? `${apiError.message} ${words.resendIn(Math.ceil(wait / 60))}` : apiError.message, false);
    }
  }

  return (
    <AuthShell title={words.title} subtitle={words.subtitle(pending.email)}>
      {failure ? (
        <ErrorSummary
          errors={fieldError ? [{ fieldId: 'kode', message: fieldError }] : []}
          focusKey={attempt}
          retry={failure.resend ? { label: words.resend, onClick: resend } : undefined}>
          {fieldError ? null : failure.message}
        </ErrorSummary>
      ) : null}
      {resent ? <Status tone="success" label={words.resent} live /> : null}
      <form onSubmit={verify} noValidate className="tr-panel tr-stack">
        <TextField
          id="kode"
          label={words.label}
          hint={words.hint}
          value={code}
          onChange={setCode}
          error={fieldError}
          inputMode="numeric"
          autoComplete="one-time-code"
          required
        />
        <div className="tr-row">
          <Button type="submit" intent="primary" icon="arrow" busy={busy} busyLabel={words.checking}>
            {words.submit}
          </Button>
          <Button onClick={resend}>{words.resend}</Button>
        </div>
      </form>
      <p>
        <Link className="tr-link" href={localHref(page, pending.purpose === 'sign_up' ? '/start' : '/start?masuk=1')}>
          {words.changeEmail}
        </Link>
      </p>
    </AuthShell>
  );
}

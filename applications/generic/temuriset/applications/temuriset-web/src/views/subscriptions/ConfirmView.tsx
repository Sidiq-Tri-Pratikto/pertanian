'use client';

import Link from 'next/link';
import { useState } from 'react';

import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Status } from '@/components/tr/Status';
import { confirmSubscription, type Subscription } from '@/features/subscriptions/api';
import { AuthShell } from '@/views/AuthShell';
import { useLocale, useMessages } from '@/features/i18n/LocaleProvider';
import { localHref } from '@/features/i18n/locale';

/** Opening the link confirms nothing; the investor presses the button, so mail scanners cannot subscribe anyone. */
export function ConfirmView({ token }: { token: string }) {
  const page = useLocale();
  const words = useMessages().confirm;
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
      <AuthShell title={words.activeTitle} subtitle={done.email}>
        <Status tone="success" label={words.activeStatus} live />
        <p>{words.activeBody}</p>
        {done.manage_token ? (
          <p>
            <Link className="tr-link" href={localHref(page, `/langganan/atur?token=${encodeURIComponent(done.manage_token)}`)}>
              {words.manage}
            </Link>
          </p>
        ) : null}
      </AuthShell>
    );
  }
  return (
    <AuthShell title={words.title} subtitle={words.subtitle}>
      {failure ? (
        <Status tone="danger" icon="alert" label={failure.code === 'NOT_FOUND' ? words.invalidLabel : words.failedLabel} live="alert">
          <p>{failure.code === 'NOT_FOUND' ? words.invalidBody : failure.message}</p>
        </Status>
      ) : null}
      <div className="tr-row">
        <Button intent="primary" busy={busy} busyLabel={words.confirming} onClick={() => void confirm()}>
          {words.submit}
        </Button>
      </div>
      <p>
        <Link className="tr-link" href={localHref(page, '/langganan')}>
          {words.other}
        </Link>
      </p>
    </AuthShell>
  );
}

'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Status } from '@/components/tr/Status';
import { useLocale, useMessages } from '@/features/i18n/LocaleProvider';
import { localHref } from '@/features/i18n/locale';
import { confirmFollow, previewFollow, type Follow } from '@/features/subscriptions/api';
import { AuthShell } from '@/views/AuthShell';

/** Opening the link only shows what would be confirmed; the visitor presses the button, so mail scanners follow nothing. */
export function FollowConfirmView({ token }: { token: string }) {
  const page = useLocale();
  const words = useMessages().follow;
  const [pending, setPending] = useState<Follow | null>(null);
  const [done, setDone] = useState<Follow | null>(null);
  const [invalid, setInvalid] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    previewFollow(token)
      .then(setPending)
      .catch(() => setInvalid(true));
  }, [token]);

  async function confirm() {
    setBusy(true);
    setFailure(null);
    try {
      setDone(await confirmFollow(token));
    } catch (error) {
      const failed = ApiError.from(error);
      if (failed.code === 'NOT_FOUND') setInvalid(true);
      else setFailure(failed.message);
    } finally {
      setBusy(false);
    }
  }

  if (invalid) {
    return (
      <AuthShell title={words.invalidTitle}>
        <p>{words.invalidBody}</p>
      </AuthShell>
    );
  }
  if (done) {
    return (
      <AuthShell title={words.confirmed} subtitle={done.email}>
        <Status tone="success" label={words.following(done.invention_title)} live />
        <p>{words.confirmedBody}</p>
        <div className="tr-row">
          <Link className="tr-btn tr-btn--primary" href={localHref(page, `/temuan/${done.invention_id}`)}>
            {words.back}
          </Link>
          {done.manage_token ? (
            <Link className="tr-link" href={localHref(page, `/ikuti/atur?token=${encodeURIComponent(done.manage_token)}`)}>
              {words.manage}
            </Link>
          ) : null}
        </div>
      </AuthShell>
    );
  }
  if (!pending) {
    return (
      <AuthShell title={words.confirmTitle}>
        <p role="status">{words.loading}</p>
      </AuthShell>
    );
  }
  return (
    <AuthShell title={words.confirmTitle} subtitle={pending.email}>
      <p className="tr-sys-type-label">{words.confirmFor(pending.invention_title)}</p>
      <p>{words.confirmHelp}</p>
      {failure ? <Status tone="danger" icon="alert" label={failure} live="alert" /> : null}
      <div className="tr-row">
        <Button intent="primary" busy={busy} busyLabel={words.confirming} onClick={() => void confirm()}>
          {words.confirm}
        </Button>
      </div>
    </AuthShell>
  );
}

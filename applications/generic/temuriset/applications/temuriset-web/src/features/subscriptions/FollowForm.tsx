'use client';

import { useState } from 'react';

import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Status } from '@/components/tr/Status';
import { TextField } from '@/components/tr/TextField';
import { useLocale, useMessages } from '@/features/i18n/LocaleProvider';
import { follow } from '@/features/subscriptions/api';

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Follow one invention by email, no account (053). The answer is the same for every address, so the page always
 * says to check the inbox; nothing is sent until the visitor confirms from that email.
 */
export function FollowForm({ inventionId }: { inventionId: string }) {
  const locale = useLocale();
  const words = useMessages().follow;
  const [email, setEmail] = useState('');
  const [invalid, setInvalid] = useState(false);
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);

  async function submit() {
    const address = email.trim();
    setInvalid(!EMAIL.test(address));
    if (!EMAIL.test(address)) return;
    setBusy(true);
    setFailure(null);
    try {
      await follow(inventionId, address, locale);
      setSent(true);
    } catch (error) {
      setFailure(ApiError.from(error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="tr-panel tr-stack" aria-labelledby="ikuti-inovasi">
      <h2 id="ikuti-inovasi" className="tr-sys-type-heading-sm">
        {words.title}
      </h2>
      {sent ? (
        <Status tone="success" label={words.inbox} live>
          <p>{words.inboxBody}</p>
          <p className="tr-muted tr-sys-type-support">{words.spam}</p>
        </Status>
      ) : (
        <form
          className="tr-stack"
          noValidate
          onSubmit={(event) => {
            event.preventDefault();
            void submit();
          }}>
          <p>{words.help}</p>
          <TextField id="ikuti-email" type="email" autoComplete="email" label={words.email} hint={words.emailHint} value={email} onChange={setEmail} error={invalid ? words.emailInvalid : undefined} required />
          {failure ? <Status tone="danger" icon="alert" label={failure} live="alert" /> : null}
          <div className="tr-row">
            <Button type="submit" intent="primary" busy={busy} busyLabel={words.sending}>
              {words.send}
            </Button>
          </div>
        </form>
      )}
    </section>
  );
}

'use client';

import Link from 'next/link';
import { useState, useSyncExternalStore, type FormEvent } from 'react';

import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { ErrorSummary } from '@/components/tr/ErrorSummary';
import { Status } from '@/components/tr/Status';
import { TextField } from '@/components/tr/TextField';
import { hasTopics, keywordsOf, subscribe, type Topics } from '@/features/subscriptions/api';
import { TopicsFields } from '@/features/subscriptions/TopicsFields';
import { AuthShell } from '@/views/AuthShell';
import { carriedEmail, forgetEmail, subscribeNever } from '@/features/i18n/carry';
import { useLocale, useMessages } from '@/features/i18n/LocaleProvider';
import { localHref } from '@/features/i18n/locale';

/** Quick subscription for investors: an email and topics, nothing else. Details need a normal signup. */
export function SubscribeView() {
  const page = useLocale();
  const messages = useMessages();
  const words = messages.subscribe;
  // An email typed before switching language starts the field.
  const carried = useSyncExternalStore(subscribeNever, carriedEmail, () => '');
  const [typedEmail, setEmail] = useState<string | null>(null);
  const email = typedEmail ?? carried;
  const [topics, setTopics] = useState<Topics>({ sectors: [], stages: [], keywords: [] });
  const [keywords, setKeywords] = useState('');
  const [errors, setErrors] = useState<{ fieldId: string; message: string }[]>([]);
  const [failure, setFailure] = useState<ApiError | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const chosen = { ...topics, keywords: keywordsOf(keywords) };
    const found = [
      ...(email.includes('@') ? [] : [{ fieldId: 'email', message: words.emailRequired }]),
      ...(hasTopics(chosen) ? [] : [{ fieldId: 'topics', message: messages.topics.required }]),
    ];
    setErrors(found);
    setFailure(null);
    if (found.length) {
      setAttempt((value) => value + 1);
      return;
    }
    setBusy(true);
    try {
      await subscribe(email.trim(), chosen, page);
      forgetEmail();
      setSent(true);
    } catch (error) {
      setFailure(ApiError.from(error));
      setAttempt((value) => value + 1);
    } finally {
      setBusy(false);
    }
  }

  if (sent) {
    return (
      <AuthShell title={words.sentTitle} subtitle={words.sentSubtitle}>
        <Status tone="success" label={words.sentStatus} live />
        <p>{words.sentBody(email.trim())}</p>
        <p className="tr-muted">{words.spam}</p>
      </AuthShell>
    );
  }
  return (
    <AuthShell title={words.title} subtitle={words.subtitle}>
      <form className="tr-stack" onSubmit={(event) => void submit(event)} noValidate>
        {errors.length ? <ErrorSummary errors={errors} focusKey={attempt} id="subscribe-errors" /> : null}
        {failure ? (
          <Status tone="danger" icon="alert" label={words.notRecorded} live="alert">
            <p>{failure.message}</p>
            {failure.requestId ? <p className="tr-sys-type-support">{messages.clientErrors.reference(failure.requestId)}</p> : null}
          </Status>
        ) : null}
        <TextField label={words.email} type="email" required value={email} onChange={setEmail} id="email" autoComplete="email" />
        <TopicsFields topics={topics} keywords={keywords} onTopics={setTopics} onKeywords={setKeywords} error={errors.some((item) => item.fieldId === 'topics') ? messages.topics.requiredShort : undefined} />
        <p className="tr-muted tr-sys-type-support">
          {words.how}
        </p>
        <div className="tr-row">
          <Button type="submit" intent="primary" busy={busy} busyLabel={words.sending}>
            {words.submit}
          </Button>
        </div>
      </form>
      <p>
        {words.detailsQuestion}{' '}
        <Link className="tr-link" href={localHref(page, '/start')}>
          {words.signUp}
        </Link>
      </p>
    </AuthShell>
  );
}

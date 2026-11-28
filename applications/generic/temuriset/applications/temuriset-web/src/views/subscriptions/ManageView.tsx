'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { SaveState, type SaveStatus } from '@/components/tr/SaveState';
import { Select } from '@/components/tr/Select';
import { Status } from '@/components/tr/Status';
import { hasTopics, keywordsOf, readSubscription, unsubscribe, updateTopics, type Subscription, type Topics } from '@/features/subscriptions/api';
import { TopicsFields } from '@/features/subscriptions/TopicsFields';
import { AuthShell } from '@/views/AuthShell';
import { useLocale, useMessages } from '@/features/i18n/LocaleProvider';
import { localHref } from '@/features/i18n/locale';

const LANGUAGES = [
  { value: 'id', label: 'Bahasa Indonesia' },
  { value: 'en', label: 'English' },
];

/** Change topics, email language, or leave, from the link in any email; no account needed. */
export function ManageView({ token }: { token: string }) {
  const page = useLocale();
  const messages = useMessages();
  const words = messages.manage;
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [topics, setTopics] = useState<Topics>({ sectors: [], stages: [], keywords: [] });
  const [keywords, setKeywords] = useState('');
  const [language, setLanguage] = useState<'id' | 'en'>('id');
  const [missing, setMissing] = useState(false);
  const [save, setSave] = useState<SaveStatus>('saved');
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    readSubscription(token)
      .then((found) => {
        setSubscription(found);
        setTopics(found.topics);
        setKeywords((found.topics.keywords ?? []).join(', '));
        setLanguage(found.locale === 'en' ? 'en' : 'id');
      })
      .catch(() => setMissing(true));
  }, [token]);

  async function saveTopics() {
    const chosen = { ...topics, keywords: keywordsOf(keywords) };
    if (!hasTopics(chosen)) {
      setMessage(messages.topics.required);
      return;
    }
    setSave('saving');
    setMessage(null);
    try {
      setSubscription(await updateTopics(token, chosen, language));
      setSave('saved');
    } catch (error) {
      setSave('failed');
      setMessage(ApiError.from(error).message);
    }
  }

  async function leave() {
    try {
      setSubscription(await unsubscribe(token));
    } catch (error) {
      setMessage(ApiError.from(error).message);
    }
  }

  if (missing) {
    return (
      <AuthShell title={words.expiredTitle}>
        <p>{words.expiredBody}</p>
      </AuthShell>
    );
  }
  if (!subscription) {
    return (
      <AuthShell title={words.title}>
        <p role="status">{words.loading}</p>
      </AuthShell>
    );
  }
  if (subscription.status === 'UNSUBSCRIBED') {
    return (
      <AuthShell title={words.stoppedTitle} subtitle={subscription.email}>
        <Status tone="neutral" label={words.stoppedStatus} live />
        <p>
          <Link className="tr-link" href={localHref(page, '/langganan')}>
            {words.again}
          </Link>
        </p>
      </AuthShell>
    );
  }
  return (
    <AuthShell title={words.title} subtitle={subscription.email}>
      {message ? <Status tone="danger" icon="alert" label={message} live="alert" /> : null}
      <TopicsFields
        topics={topics}
        keywords={keywords}
        onTopics={(next) => {
          setTopics(next);
          setSave('local');
        }}
        onKeywords={(next) => {
          setKeywords(next);
          setSave('local');
        }}
      />
      <Select
        id="bahasa-email"
        label={words.language}
        hint={words.languageHint}
        value={language}
        onChange={(next) => {
          setLanguage(next === 'en' ? 'en' : 'id');
          setSave('local');
        }}
        options={LANGUAGES}
        emptyLabel={null}
      />
      <div className="tr-row">
        <Button intent="primary" busy={save === 'saving'} busyLabel={words.saving} onClick={() => void saveTopics()}>
          {words.save}
        </Button>
        <SaveState state={save} onRetry={() => void saveTopics()} />
      </div>
      <section className="tr-panel tr-stack" aria-labelledby="berhenti">
        <h2 id="berhenti" className="tr-sys-type-heading-sm">
          {words.stopTitle}
        </h2>
        <p>{words.stopBody}</p>
        <div className="tr-row">
          <Button intent="danger" onClick={() => void leave()}>
            {words.stop}
          </Button>
        </div>
      </section>
    </AuthShell>
  );
}

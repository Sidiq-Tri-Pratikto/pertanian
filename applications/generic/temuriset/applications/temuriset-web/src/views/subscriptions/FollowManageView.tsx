'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Select } from '@/components/tr/Select';
import { Status } from '@/components/tr/Status';
import { useLocale, useMessages } from '@/features/i18n/LocaleProvider';
import { localHref } from '@/features/i18n/locale';
import { readFollow, setFollowLanguage, unfollow, type Follow } from '@/features/subscriptions/api';
import { AuthShell } from '@/views/AuthShell';

const LANGUAGES = [
  { value: 'id', label: 'Bahasa Indonesia' },
  { value: 'en', label: 'English' },
];

/** Change the email language or unfollow, from the link in any follow email; no account needed. */
export function FollowManageView({ token }: { token: string }) {
  const page = useLocale();
  const words = useMessages().follow;
  const [record, setRecord] = useState<Follow | null>(null);
  const [language, setLanguage] = useState<string>('id');
  const [missing, setMissing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<{ tone: 'success' | 'danger'; text: string } | null>(null);

  useEffect(() => {
    readFollow(token)
      .then((found) => {
        setRecord(found);
        setLanguage(found.locale);
      })
      .catch(() => setMissing(true));
  }, [token]);

  async function run(action: () => Promise<Follow>, success?: string) {
    setBusy(true);
    setNotice(null);
    try {
      setRecord(await action());
      if (success) setNotice({ tone: 'success', text: success });
    } catch (error) {
      setNotice({ tone: 'danger', text: ApiError.from(error).message });
    } finally {
      setBusy(false);
    }
  }

  if (missing) {
    return (
      <AuthShell title={words.invalidTitle}>
        <p>{words.invalidBody}</p>
      </AuthShell>
    );
  }
  if (!record) {
    return (
      <AuthShell title={words.manage}>
        <p role="status">{words.loading}</p>
      </AuthShell>
    );
  }
  const back = (
    <Link className="tr-link" href={localHref(page, `/temuan/${record.invention_id}`)}>
      {words.back}
    </Link>
  );
  if (record.status === 'UNSUBSCRIBED') {
    return (
      <AuthShell title={words.stopTitle} subtitle={record.email}>
        <Status tone="neutral" label={words.stopDone} live />
        <p>{words.stopPrompt}</p>
        <p>{back}</p>
      </AuthShell>
    );
  }
  return (
    <AuthShell title={words.manage} subtitle={record.email}>
      <Status tone="success" label={words.following(record.invention_title)} />
      <div aria-live="polite">{notice ? <Status tone={notice.tone} label={notice.text} /> : null}</div>
      <Select id="bahasa-email" label={words.language} value={language} onChange={setLanguage} options={LANGUAGES} emptyLabel={null} />
      <div className="tr-row">
        <Button intent="primary" busy={busy} busyLabel={words.saving} onClick={() => void run(() => setFollowLanguage(token, language === 'en' ? 'en' : 'id'), words.languageSaved)}>
          {words.saveLanguage}
        </Button>
        {back}
      </div>
      <section className="tr-panel tr-stack" aria-labelledby="berhenti-mengikuti">
        <h2 id="berhenti-mengikuti" className="tr-sys-type-heading-sm">
          {words.stop}
        </h2>
        <p>{words.stopHelp}</p>
        <div className="tr-row">
          <Button intent="danger" onClick={() => void run(() => unfollow(token))}>
            {words.stop}
          </Button>
        </div>
      </section>
    </AuthShell>
  );
}

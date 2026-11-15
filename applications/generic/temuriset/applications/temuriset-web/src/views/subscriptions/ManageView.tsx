'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { SaveState, type SaveStatus } from '@/components/tr/SaveState';
import { Status } from '@/components/tr/Status';
import { hasTopics, keywordsOf, readSubscription, unsubscribe, updateTopics, type Subscription, type Topics } from '@/features/subscriptions/api';
import { TopicsFields } from '@/features/subscriptions/TopicsFields';
import { AuthShell } from '@/views/AuthShell';

/** Change topics or leave, from the link in any email; no account needed. */
export function ManageView({ token }: { token: string }) {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [topics, setTopics] = useState<Topics>({ sectors: [], stages: [], keywords: [] });
  const [keywords, setKeywords] = useState('');
  const [missing, setMissing] = useState(false);
  const [save, setSave] = useState<SaveStatus>('saved');
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    readSubscription(token)
      .then((found) => {
        setSubscription(found);
        setTopics(found.topics);
        setKeywords((found.topics.keywords ?? []).join(', '));
      })
      .catch(() => setMissing(true));
  }, [token]);

  async function saveTopics() {
    const chosen = { ...topics, keywords: keywordsOf(keywords) };
    if (!hasTopics(chosen)) {
      setMessage('Pilih setidaknya satu sektor, tahap, atau kata kunci.');
      return;
    }
    setSave('saving');
    setMessage(null);
    try {
      setSubscription(await updateTopics(token, chosen));
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
      <AuthShell title="Tautan tidak berlaku">
        <p>Tautan ini sudah kedaluwarsa. Buka tautan dari email kabar inovasi yang terbaru.</p>
      </AuthShell>
    );
  }
  if (!subscription) {
    return (
      <AuthShell title="Langganan kabar inovasi">
        <p role="status">Memuat langganan…</p>
      </AuthShell>
    );
  }
  if (subscription.status === 'UNSUBSCRIBED') {
    return (
      <AuthShell title="Anda sudah berhenti berlangganan" subtitle={subscription.email}>
        <Status tone="neutral" label="Tidak ada lagi kabar inovasi yang dikirim ke email ini" live />
        <p>
          <Link className="tr-link" href="/langganan">
            Berlangganan lagi
          </Link>
        </p>
      </AuthShell>
    );
  }
  return (
    <AuthShell title="Langganan kabar inovasi" subtitle={subscription.email}>
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
      <div className="tr-row">
        <Button intent="primary" busy={save === 'saving'} busyLabel="Menyimpan…" onClick={() => void saveTopics()}>
          Simpan minat
        </Button>
        <SaveState state={save} onRetry={() => void saveTopics()} />
      </div>
      <section className="tr-panel tr-stack" aria-labelledby="berhenti">
        <h2 id="berhenti" className="tr-sys-type-heading-sm">
          Berhenti berlangganan
        </h2>
        <p>Tidak ada lagi alert atau rangkuman mingguan yang dikirim ke email ini.</p>
        <div className="tr-row">
          <Button intent="danger" onClick={() => void leave()}>
            Berhenti berlangganan
          </Button>
        </div>
      </section>
    </AuthShell>
  );
}

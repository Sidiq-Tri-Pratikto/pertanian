'use client';

import Link from 'next/link';
import { useState, type FormEvent } from 'react';

import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { ErrorSummary } from '@/components/tr/ErrorSummary';
import { Status } from '@/components/tr/Status';
import { TextField } from '@/components/tr/TextField';
import { hasTopics, keywordsOf, subscribe, type Topics } from '@/features/subscriptions/api';
import { TopicsFields } from '@/features/subscriptions/TopicsFields';
import { AuthShell } from '@/views/AuthShell';

/** Quick subscription for investors: an email and topics, nothing else. Details need a normal signup. */
export function SubscribeView() {
  const [email, setEmail] = useState('');
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
      ...(email.includes('@') ? [] : [{ fieldId: 'email', message: 'Tulis alamat email Anda.' }]),
      ...(hasTopics(chosen) ? [] : [{ fieldId: 'topics', message: 'Pilih setidaknya satu sektor, tahap, atau kata kunci.' }]),
    ];
    setErrors(found);
    setFailure(null);
    if (found.length) {
      setAttempt((value) => value + 1);
      return;
    }
    setBusy(true);
    try {
      await subscribe(email.trim(), chosen);
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
      <AuthShell title="Periksa email Anda" subtitle="Satu langkah lagi.">
        <Status tone="success" label="Tautan konfirmasi sedang dikirim" live />
        <p>{`Kami mengirim tautan konfirmasi ke ${email.trim()}. Kabar inovasi baru dikirim setelah Anda mengonfirmasi.`}</p>
        <p className="tr-muted">Tidak menerima email? Periksa folder spam, atau coba lagi beberapa menit lagi.</p>
      </AuthShell>
    );
  }
  return (
    <AuthShell title="Kabar inovasi untuk investor" subtitle="Dapatkan ringkasan singkat inovasi yang sesuai minat Anda lewat email, tanpa membuat akun.">
      <form className="tr-stack" onSubmit={(event) => void submit(event)} noValidate>
        {errors.length ? <ErrorSummary errors={errors} focusKey={attempt} id="subscribe-errors" /> : null}
        {failure ? (
          <Status tone="danger" icon="alert" label="Langganan belum tercatat" live="alert">
            <p>{failure.message}</p>
            {failure.requestId ? <p className="tr-sys-type-support">{`ID referensi: ${failure.requestId}`}</p> : null}
          </Status>
        ) : null}
        <TextField label="Email" type="email" required value={email} onChange={setEmail} id="email" autoComplete="email" />
        <TopicsFields topics={topics} keywords={keywords} onTopics={setTopics} onKeywords={setKeywords} error={errors.some((item) => item.fieldId === 'topics') ? 'Pilih setidaknya satu minat.' : undefined} />
        <p className="tr-muted tr-sys-type-support">
          Inovasi yang sangat sesuai dikirim langsung; sisanya dirangkum setiap Senin pukul 09.00 WIB. Hanya inovasi yang pengelolanya setuju yang dikirim. Anda dapat berhenti kapan saja dari tautan di setiap email.
        </p>
        <div className="tr-row">
          <Button type="submit" intent="primary" busy={busy} busyLabel="Mengirim…">
            Berlangganan
          </Button>
        </div>
      </form>
      <p>
        Ingin melihat detail dan menghubungi inovator?{' '}
        <Link className="tr-link" href="/start">
          Daftar akun investor
        </Link>
      </p>
    </AuthShell>
  );
}

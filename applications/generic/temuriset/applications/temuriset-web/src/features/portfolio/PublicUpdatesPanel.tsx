'use client';

import { useRouter } from 'next/navigation';
import { useId, useState } from 'react';

import { newIdempotencyKey, send } from '@/api/client';
import { ApiError } from '@/api/errors';
import type { components } from '@/api/schema.generated';
import { Button } from '@/components/tr/Button';
import { Disclosure } from '@/components/tr/Disclosure';
import { Select } from '@/components/tr/Select';
import { Status } from '@/components/tr/Status';
import { TextArea } from '@/components/tr/TextArea';
import { TextField } from '@/components/tr/TextField';
import { intlLocale, t } from '@/features/i18n/t';

export type PublicUpdate = components['schemas']['InventionUpdateResponse'];
type Props = { inventionId: string; actingPartyId: string; updates: PublicUpdate[]; pageOn: boolean };
type Draft = { title: string; body: string; language: string };
type Notice = { tone: 'success' | 'danger'; text: string } | null;

const LANGUAGES = [
  { value: 'id', label: 'Bahasa Indonesia' },
  { value: 'en', label: 'English' },
];
const date = (iso: string) => new Intl.DateTimeFormat(intlLocale(), { dateStyle: 'medium', timeZone: 'Asia/Jakarta' }).format(new Date(iso));

function failure(error: unknown): string {
  const failed = ApiError.from(error);
  return failed.code === 'STALE_VERSION' ? t('Kabar ini baru saja berubah. Muat ulang halaman lalu coba lagi.') : failed.message;
}

function statusLabel(update: PublicUpdate): string {
  if (update.status === 'PUBLISHED') return t('Terbit {date}', { date: date(update.published_at!) });
  if (update.status === 'WITHDRAWN') return t('Ditarik dari halaman publik');
  return t('Draf, belum terlihat');
}

/** Title, text and language of one update; used for a new update and for a correction. */
function UpdateForm({ initial, submitLabel, onSubmit }: { initial: Draft; submitLabel: string; onSubmit: (draft: Draft) => Promise<boolean> }) {
  const id = useId();
  const [draft, setDraft] = useState(initial);
  const [errors, setErrors] = useState<{ title?: string; body?: string }>({});
  const [busy, setBusy] = useState(false);

  async function submit() {
    const found = { title: draft.title.trim() ? undefined : t('Tulis judul kabar.'), body: draft.body.trim() ? undefined : t('Tulis isi kabar.') };
    setErrors(found);
    if (found.title || found.body) return;
    setBusy(true);
    const done = await onSubmit({ ...draft, title: draft.title.trim(), body: draft.body.trim() });
    setBusy(false);
    if (done && !initial.title) setDraft(initial);
  }

  return (
    <div className="tr-stack">
      <TextField id={`${id}-judul`} label={t('Judul kabar')} value={draft.title} onChange={(title) => setDraft({ ...draft, title })} error={errors.title} required />
      <TextArea id={`${id}-isi`} label={t('Isi kabar')} hint={t('Apa yang berubah, dan siapa yang melaporkannya.')} value={draft.body} onChange={(body) => setDraft({ ...draft, body })} error={errors.body} rows={4} limit={1200} required />
      <Select id={`${id}-bahasa`} label="Bahasa tulisan Anda" value={draft.language} onChange={(language) => setDraft({ ...draft, language })} options={LANGUAGES} emptyLabel={null} />
      <div className="tr-row">
        <Button intent="primary" busy={busy} busyLabel="Menyimpan…" onClick={() => void submit()}>
          {submitLabel}
        </Button>
      </div>
    </div>
  );
}

/**
 * Public updates (052): short news on the public page. A new update starts as a draft; publishing shows it, and only
 * the first publication will ever be announced, so a correction or republication never repeats it.
 */
export function PublicUpdatesPanel({ inventionId, actingPartyId, updates, pageOn }: Props) {
  const router = useRouter();
  const [notice, setNotice] = useState<Notice>(null);
  const base = `/api/v1/inventions/${inventionId}/updates`;

  async function run(action: () => Promise<unknown>, success: string): Promise<boolean> {
    setNotice(null);
    try {
      await action();
      setNotice({ tone: 'success', text: success });
      router.refresh();
      return true;
    } catch (error) {
      setNotice({ tone: 'danger', text: failure(error) });
      return false;
    }
  }

  const create = (draft: Draft) =>
    run(
      () => send('POST', base, { acting_party_id: actingPartyId, title: draft.title, body: draft.body, content_locale: draft.language }, { idempotencyKey: newIdempotencyKey() }),
      t('Draf kabar tersimpan. Terbitkan bila sudah siap.'),
    );
  const edit = (update: PublicUpdate) => (draft: Draft) =>
    run(
      () => send('PUT', `${base}/${update.id}`, { acting_party_id: actingPartyId, expected_version: update.version, title: draft.title, body: draft.body, content_locale: draft.language }),
      update.status === 'PUBLISHED' ? t('Perbaikan tersimpan dan langsung terlihat. Kabar ini tidak dikirim ulang.') : t('Perbaikan tersimpan.'),
    );
  const act = (update: PublicUpdate, action: 'publish' | 'withdraw') =>
    void run(
      () => send('POST', `${base}/${update.id}/${action}`, { acting_party_id: actingPartyId, expected_version: update.version }, { idempotencyKey: newIdempotencyKey() }),
      action === 'publish' ? t('“{title}” terbit di halaman publik.', { title: update.title }) : t('“{title}” ditarik dari halaman publik.', { title: update.title }),
    );

  return (
    <section className="tr-panel tr-stack" aria-labelledby="kabar-publik">
      <h2 id="kabar-publik" className="tr-sys-type-heading-sm">
        {t('Kabar publik')}
      </h2>
      <p className="tr-muted">{t('Tiga kabar terbit terbaru tampil di halaman publik. Kabar yang diperbaiki tetap terbit dan tidak diumumkan ulang.')}</p>
      {pageOn ? null : <Status tone="neutral" icon="lock" label={t('Nyalakan halaman publik di atas agar kabar dapat diterbitkan. Draf tetap dapat ditulis.')} />}
      <Disclosure label={t('Tulis kabar baru')} defaultOpen={updates.length === 0}>
        <UpdateForm initial={{ title: '', body: '', language: 'id' }} submitLabel={t('Simpan sebagai draf')} onSubmit={create} />
      </Disclosure>
      {updates.length ? (
        <ul className="tr-list" aria-label={t('Kabar inovasi ini')}>
          {updates.map((update) => (
            <li key={update.id} className="tr-listrow tr-stack">
              <h3 className="tr-sys-type-label">{update.title}</h3>
              <p className="tr-muted tr-sys-type-support">{statusLabel(update)}</p>
              <p lang={update.content_locale === 'en' ? 'en' : undefined}>{update.body}</p>
              <div className="tr-row">
                {update.status === 'PUBLISHED' ? (
                  <Button onClick={() => act(update, 'withdraw')}>{t('Tarik dari halaman')}</Button>
                ) : (
                  <Button onClick={() => act(update, 'publish')}>{t('Terbitkan')}</Button>
                )}
              </div>
              <Disclosure label={t('Perbaiki teks')}>
                <UpdateForm initial={{ title: update.title, body: update.body, language: update.content_locale }} submitLabel={t('Simpan perbaikan')} onSubmit={edit(update)} />
              </Disclosure>
            </li>
          ))}
        </ul>
      ) : null}
      <div aria-live="polite">{notice ? <Status tone={notice.tone} label={notice.text} /> : null}</div>
    </section>
  );
}

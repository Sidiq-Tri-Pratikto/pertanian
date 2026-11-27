'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { send } from '@/api/client';
import type { components } from '@/api/schema.generated';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Checkbox } from '@/components/tr/Checkbox';
import { Select } from '@/components/tr/Select';
import { Status } from '@/components/tr/Status';
import { TextArea } from '@/components/tr/TextArea';
import { TextField } from '@/components/tr/TextField';
import type { DocumentView } from '@/features/documents/model';

type PublicPage = components['schemas']['PublicPageResponse'];
type Props = { inventionId: string; actingPartyId: string; version: number; page: PublicPage; documents: DocumentView[] };

const IMAGE = new Set(['image/jpeg', 'image/png', 'image/webp']);
const LANGUAGES = [
  { value: 'id', label: 'Bahasa Indonesia' },
  { value: 'en', label: 'English' },
];

/** The owner's available images, newest version of each, as photo choices. */
function photoChoices(documents: DocumentView[]) {
  return documents.flatMap((document) => {
    const latest = [...document.versions].reverse().find((version) => version.file_state === 'AVAILABLE' && IMAGE.has(version.media_type));
    return latest ? [{ value: `${document.id}:${latest.number}`, label: `${document.title}, versi ${latest.number}` }] : [];
  });
}

/**
 * The public invention page (051): what anyone may see signed out, with an optional photo and field-test summary.
 * Separate from investor news on purpose: turning the page on sends no email to anyone.
 */
export function PublicPageForm({ inventionId, actingPartyId, version, page, documents }: Props) {
  const router = useRouter();
  const choices = photoChoices(documents);
  const [enabled, setEnabled] = useState(Boolean(page.enabled));
  const [fieldTest, setFieldTest] = useState(page.field_test ?? '');
  const [photo, setPhoto] = useState(page.photo ? `${page.photo.document_id}:${page.photo.version}` : '');
  const [alt, setAlt] = useState(page.photo?.alt ?? '');
  const [language, setLanguage] = useState<string>(page.content_locale ?? 'id');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<{ tone: 'success' | 'danger'; text: string; altError?: string } | null>(null);

  async function save() {
    if (photo && !alt.trim()) {
      setNotice({ tone: 'danger', text: 'Tulis apa yang terlihat di foto.', altError: 'Tulis apa yang terlihat di foto, untuk pembaca layar dan saat foto tidak dimuat.' });
      return;
    }
    setBusy(true);
    setNotice(null);
    const [documentId, number] = photo.split(':');
    try {
      await send('PUT', `/api/v1/inventions/${inventionId}/public-page`, {
        acting_party_id: actingPartyId,
        expected_version: version,
        enabled,
        field_test: fieldTest.trim() || null,
        photo: photo ? { document_id: documentId, version: Number(number) } : null,
        photo_alt: alt.trim() || null,
        content_locale: language,
      });
      setNotice({ tone: 'success', text: enabled ? 'Halaman publik tersimpan dan terlihat oleh siapa pun.' : 'Tersimpan. Halaman publik tidak terlihat.' });
      router.refresh();
    } catch (error) {
      const failed = ApiError.from(error);
      setNotice({ tone: 'danger', text: failed.code === 'STALE_VERSION' ? 'Inovasi ini baru saja berubah. Muat ulang halaman lalu coba lagi.' : failed.message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="tr-panel tr-stack" aria-labelledby="halaman-publik">
      <h2 id="halaman-publik" className="tr-sys-type-heading-sm">
        Halaman publik
      </h2>
      <p className="tr-muted">Siapa pun dengan tautannya dapat membaca judul, ringkasan, sektor, tahap, serta foto dan uji lapangan di bawah. Ini terpisah dari kabar untuk investor: menyalakan halaman ini tidak mengirim email ke siapa pun.</p>
      <Checkbox id="halaman-publik-aktif" label="Tampilkan halaman publik inovasi ini" checked={enabled} onChange={setEnabled} />
      <TextArea id="uji-lapangan" label="Ringkasan uji lapangan (opsional)" hint="Apa yang sudah diuji, di mana, dan siapa yang melaporkannya." value={fieldTest} onChange={setFieldTest} rows={3} limit={600} />
      {choices.length ? (
        <>
          <Select id="foto-publik" label="Foto (opsional)" hint="Data lokasi dan kamera di dalam foto dihapus sebelum ditampilkan." value={photo} onChange={setPhoto} options={choices} emptyLabel="Tanpa foto" />
          {photo ? <TextField id="foto-alt" label="Apa yang terlihat di foto" value={alt} onChange={setAlt} error={notice?.altError} required /> : null}
        </>
      ) : (
        <p className="tr-muted tr-sys-type-support">
          Untuk menampilkan foto, unggah gambar JPEG, PNG atau WEBP di{' '}
          <Link className="tr-link" href={`/inventions/${inventionId}/edit?step=2`}>
            langkah bukti
          </Link>
          .
        </p>
      )}
      <Select id="bahasa-konten" label="Bahasa tulisan Anda" hint="Pembaca halaman berbahasa lain melihat keterangan bahasa ini." value={language} onChange={setLanguage} options={LANGUAGES} emptyLabel={null} />
      <div className="tr-row">
        <Button intent="primary" busy={busy} busyLabel="Menyimpan…" onClick={() => void save()}>
          Simpan halaman publik
        </Button>
        {page.enabled ? (
          <Link className="tr-link" href={`/temuan/${inventionId}`}>
            Lihat halaman publik
          </Link>
        ) : null}
      </div>
      <div aria-live="polite">{notice ? <Status tone={notice.tone} label={notice.text} /> : null}</div>
    </section>
  );
}

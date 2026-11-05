'use client';

import { useCallback, useEffect, useRef, useState, type ChangeEvent } from 'react';

import { newIdempotencyKey, send, type Me } from '@/api/client';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Dialog } from '@/components/tr/Dialog';
import { DocumentItem, FILE } from '@/components/tr/DocumentItem';
import { FieldError } from '@/components/tr/FieldError';
import { Status } from '@/components/tr/Status';
import { ACCEPT_ATTRIBUTE, refusal, settled, type DocumentView } from '@/features/documents/model';
import { uploadFile, type Upload } from '@/features/documents/upload';

const POLL_MS = 1500;

type Transfer = { id: string; title: string; progress: number; upload: Upload };
type Revoking = { grantId: string; recipient: string; openerId: string };

/**
 * Step 2's documents: upload with progress and cancel, three independent states per file, every grant, and an honest
 * revocation (UX-10). State changes are announced politely without moving focus.
 */
export function DocumentsPanel({ me, initial }: { me: Me; initial: DocumentView[] }) {
  const [documents, setDocuments] = useState(initial);
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [announcement, setAnnouncement] = useState('');
  const [revoking, setRevoking] = useState<Revoking | null>(null);
  const [revokeBusy, setRevokeBusy] = useState(false);
  const [revokeFailure, setRevokeFailure] = useState<string | null>(null);
  // After a revocation the opener disappears with its grant, so focus goes back to the upload field.
  const [returnId, setReturnId] = useState<string | undefined>(undefined);
  const input = useRef<HTMLInputElement>(null);
  const known = useRef(new Map<string, string>());

  const refresh = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/documents', { cache: 'no-store', signal: AbortSignal.timeout(10_000) });
      if (response.ok) setDocuments((await response.json()) as DocumentView[]);
    } catch {
      // The next poll tries again; the list on screen stays as it was.
    }
  }, []);

  // Poll until every file has finished its scan and text reading (FR-002).
  useEffect(() => {
    if (documents.every(settled)) return;
    const timer = setTimeout(refresh, POLL_MS);
    return () => clearTimeout(timer);
  }, [documents, refresh]);

  // Announce each file-state change once.
  useEffect(() => {
    for (const document of documents) {
      const state = document.versions.at(-1)?.file_state ?? '';
      const before = known.current.get(document.id);
      if (before !== undefined && before !== state) setAnnouncement(`${document.title}: ${FILE[state]?.[0] ?? state}`);
      known.current.set(document.id, state);
    }
  }, [documents]);

  // Leaving the page during a transfer asks first.
  useEffect(() => {
    if (!transfers.length) return;
    const warn = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [transfers.length]);

  function choose(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    const refused = refusal(file);
    setFieldError(refused);
    if (refused) return;
    const id = newIdempotencyKey();
    const title = file.name.replace(/\.[^.]+$/, '') || 'Dokumen';
    const upload = uploadFile(file, title, me.active_party_id, (progress) =>
      setTransfers((current) => current.map((transfer) => (transfer.id === id ? { ...transfer, progress } : transfer))),
    );
    setTransfers((current) => [...current, { id, title, progress: 0, upload }]);
    setAnnouncement(`${title}: Sedang diunggah`);
    upload.promise
      .then(() => refresh())
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') setAnnouncement(`${title}: Unggahan dibatalkan`);
        else setFieldError(ApiError.from(error).message);
      })
      .finally(() => setTransfers((current) => current.filter((transfer) => transfer.id !== id)));
  }

  async function revoke() {
    if (!revoking || revokeBusy) return;
    setRevokeBusy(true);
    setRevokeFailure(null);
    try {
      await send('POST', `/api/v1/grants/${revoking.grantId}/revoke`, { acting_party_id: me.active_party_id }, { idempotencyKey: newIdempotencyKey() });
      setAnnouncement(`Akses ${revoking.recipient} dicabut. Salinan yang sudah diunduh tidak dapat ditarik kembali.`);
      setReturnId('unggah-berkas');
      setRevoking(null);
      await refresh();
    } catch (error) {
      setRevokeFailure(ApiError.from(error).message);
    } finally {
      setRevokeBusy(false);
    }
  }

  return (
    <div className="tr-stack">
      <p className="tr-muted">Dokumen selalu privat sampai Anda membagikan satu versi kepada satu penerima pitching. PDF dan DOCX sampai 20 MB, gambar sampai 5 MB.</p>
      <div className={fieldError ? 'tr-field tr-field--error' : 'tr-field'}>
        <label className="tr-field__label tr-sys-type-label" htmlFor="unggah-berkas">
          Unggah dokumen bukti
        </label>
        {fieldError ? <FieldError id="unggah-berkas-error">{fieldError}</FieldError> : null}
        <input
          ref={input}
          id="unggah-berkas"
          type="file"
          className="tr-input"
          accept={ACCEPT_ATTRIBUTE}
          aria-invalid={fieldError ? true : undefined}
          aria-describedby={fieldError ? 'unggah-berkas-error' : undefined}
          onChange={choose}
        />
      </div>
      <div aria-live="polite" className="tr-sr">
        {announcement}
      </div>
      <ul className="tr-stack">
        {transfers.map((transfer) => (
          <li key={transfer.id}>
            <DocumentItem
              title={transfer.title}
              file="UPLOADING"
              action={
                <>
                  <progress max={1} value={transfer.progress} aria-label={`Kemajuan unggahan ${transfer.title}`} />
                  <Button onClick={() => transfer.upload.cancel()}>
                    Batalkan unggahan<span className="tr-sr">{` ${transfer.title}`}</span>
                  </Button>
                </>
              }
            />
          </li>
        ))}
        {documents.map((document) => {
          const latest = document.versions.at(-1);
          const active = document.grants.filter((grant) => !grant.revoked_at);
          return (
            <li key={document.id}>
              <DocumentItem
                title={document.title}
                version={latest?.number}
                file={latest?.file_state}
                extraction={latest?.extraction_state}
                review={latest?.review_state}
                grants={document.grants.map((grant) => ({ recipient: grant.grantee_name, version: grant.version, revoked: Boolean(grant.revoked_at) }))}
                action={active.map((grant) => (
                  <Button
                    key={grant.id}
                    intent="danger"
                    id={`cabut-${grant.id}`}
                    onClick={() => {
                      setReturnId(`cabut-${grant.id}`);
                      setRevoking({ grantId: grant.id, recipient: grant.grantee_name, openerId: `cabut-${grant.id}` });
                    }}>
                    Cabut akses<span className="tr-sr">{` ${grant.grantee_name} untuk ${document.title}`}</span>
                  </Button>
                ))}
              />
            </li>
          );
        })}
      </ul>
      {!documents.length && !transfers.length ? <p className="tr-muted">Belum ada dokumen.</p> : null}
      <Dialog
        open={revoking !== null}
        onClose={() => setRevoking(null)}
        title={revoking ? `Cabut akses ${revoking.recipient}?` : ''}
        returnFocusId={returnId}
        primary={{ label: 'Cabut akses', intent: 'danger', busy: revokeBusy, busyLabel: 'Mencabut…', onClick: revoke }}>
        <p>Unduhan baru akan diblokir sejak sekarang. Salinan yang sudah diunduh sebelumnya tidak dapat ditarik kembali.</p>
        {revokeFailure ? (
          <Status tone="danger" icon="alert" label="Akses belum dicabut" live="alert">
            <p>{revokeFailure}</p>
          </Status>
        ) : null}
      </Dialog>
    </div>
  );
}

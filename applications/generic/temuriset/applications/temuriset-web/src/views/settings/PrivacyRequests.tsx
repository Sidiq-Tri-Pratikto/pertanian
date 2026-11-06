'use client';

import { useState } from 'react';

import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Dialog } from '@/components/tr/Dialog';
import { ErrorSummary } from '@/components/tr/ErrorSummary';
import { Status } from '@/components/tr/Status';
import { downloadExport, submitPrivacyRequest } from '@/features/privacy/api';
import { PRIVACY_STATUS, type ActingScope, type PrivacyInput, type PrivacyRequest, type SectionData } from '@/features/privacy/model';
import { useIntent } from '@/features/privacy/useIntent';

type Props = { scope: ActingScope; initial: SectionData<PrivacyRequest> };

function DeletionAnswer({ request }: { request: PrivacyRequest }) {
  const { answer } = request;
  return (
    <div className="tr-stack">
      {answer.to_remove.length ? <><strong>Akan dihapus</strong><ul>{answer.to_remove.map((item) => <li key={item.key}>{item.label}</li>)}</ul></> : null}
      {answer.removed.length ? <><strong>Sudah dihapus</strong><ul>{answer.removed.map((item) => <li key={item.key}>{item.label}</li>)}</ul></> : null}
      {answer.retained.length ? <><strong>Tetap disimpan</strong><ul>{answer.retained.map((item) => <li key={item.key}>{item.label}. {item.reason} {item.period}</li>)}</ul></> : null}
      <p>{answer.notice}</p>
    </div>
  );
}

export function PrivacyRequests({ scope, initial }: Props) {
  const [requests, setRequests] = useState(initial.data);
  const [dialog, setDialog] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [downloadFailure, setDownloadFailure] = useState<ApiError | null>(null);
  const [message, setMessage] = useState('');
  const action = useIntent(submitPrivacyRequest);
  const input = (kind: PrivacyInput['kind']): PrivacyInput => ({
    kind, acting_party_id: scope.id, expected_version: null,
  });

  async function create(kind: PrivacyInput['kind']) {
    if (kind === 'DELETION') setDialog(false);
    const result = await action.run(input(kind));
    if (!result) return;
    setRequests((current) => [result, ...current.filter((item) => item.id !== result.id)]);
    setMessage(kind === 'EXPORT' ? 'Ekspor siap diunduh.' : 'Permintaan penghapusan diterima.');
  }

  async function download(id: string) {
    if (downloading) return;
    setDownloading(id);
    setDownloadFailure(null);
    try {
      await downloadExport(id);
      setMessage('Unduhan ekspor dimulai.');
    } catch (error) {
      setDownloadFailure(ApiError.from(error));
    } finally {
      setDownloading(null);
    }
  }

  return (
    <section className="tr-panel tr-stack" aria-labelledby="judul-privasi">
      <h2 id="judul-privasi" className="tr-sys-type-heading-sm">Permintaan privasi</h2>
      <p>Bertindak sebagai <strong>{scope.label}</strong></p>
      <p>Salinan yang sudah diunduh tidak dapat ditarik kembali.</p>
      {action.failure || downloadFailure ? (
        <ErrorSummary id="galat-privasi" focusKey={downloadFailure ? undefined : action.attempt} title="Permintaan belum dapat diselesaikan">
          {(downloadFailure ?? action.failure)?.message}
          {(downloadFailure ?? action.failure)?.requestId ? ` ID referensi ${(downloadFailure ?? action.failure)?.requestId}.` : ''}
        </ErrorSummary>
      ) : null}
      <div className="tr-row">
        <Button busy={action.busy} disabledReason={action.blocked(input('EXPORT'))} onClick={() => void create('EXPORT')}>Minta ekspor data</Button>
        <Button id="buka-hapus-data" busy={action.busy} disabledReason={action.blocked(input('DELETION'))} onClick={() => setDialog(true)}>Minta penghapusan data</Button>
      </div>
      <Dialog
        open={dialog}
        title="Ajukan penghapusan data?"
        onClose={() => setDialog(false)}
        returnFocusId="buka-hapus-data"
        primary={{ label: 'Ajukan penghapusan', intent: 'danger', onClick: () => void create('DELETION') }}>
        <p>Petugas akan meninjau permintaan Anda. Sebagian data dapat disimpan sesuai kebijakan retensi. Rincian dan alasannya muncul setelah permintaan diajukan.</p>
      </Dialog>
      <p role="status">{message}</p>
      {initial.failure ? (
        <Status label="Status privasi belum tersedia" tone="warning">
          {initial.failure.message}{initial.failure.requestId ? ` ID referensi ${initial.failure.requestId}.` : ''}
        </Status>
      ) : null}
      {requests.length ? (
        <ul className="tr-stack">
          {requests.map((request) => (
            <li key={request.id} className="tr-stack">
              <strong>{request.kind === 'DELETION' ? 'Penghapusan data' : 'Ekspor data'}</strong>
              <Status label={PRIVACY_STATUS[request.status]} />
              {request.kind === 'DELETION' ? <DeletionAnswer request={request} /> : request.status === 'FULFILLED' ? (
                <Button busy={downloading === request.id} onClick={() => void download(request.id)}>Unduh ekspor</Button>
              ) : null}
            </li>
          ))}
        </ul>
      ) : initial.failure ? null : <p className="tr-muted">Belum ada permintaan privasi.</p>}
    </section>
  );
}

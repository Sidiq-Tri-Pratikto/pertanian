'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState, type FormEvent } from 'react';

import { newIdempotencyKey, type Me } from '@/api/client';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Checkbox } from '@/components/tr/Checkbox';
import { ContextSwitcher } from '@/components/tr/ContextSwitcher';
import { ErrorSummary } from '@/components/tr/ErrorSummary';
import { Field, fieldIds } from '@/components/tr/Field';
import { Screen } from '@/components/tr/Screen';
import { Select } from '@/components/tr/Select';
import { ContextBar, contextOptions } from '@/features/ContextBar';
import { readPersona } from '@/features/persona';
import {
  changeImport, createExport, downloadExport, readExport, readImport, validateImport,
  type ExportRequest, type ExportStatus, type ImportStatus, type PreviewRow,
} from '@/features/portability/api';
import type { InventionSummary } from '@/features/portfolio/model';
import { PROVENANCE } from '@/views/parts';

const STATUS = {
  NOT_STARTED: 'Belum dimulai', PENDING: 'Sedang diproses', SUCCEEDED: 'Selesai',
  FAILED: 'Gagal', CANCELLED: 'Dibatalkan', EXPIRED: 'Kedaluwarsa',
};
const ACTION = { CREATE: 'Buat draf', UPDATE: 'Perbarui draf', UNCHANGED: 'Tidak berubah', CONFLICT: 'Konflik' };
const OUTCOME = { COMMITTED: 'Tersimpan', SKIPPED: 'Dilewati', UNCHANGED: 'Tidak berubah' };
const CONFLICTS = {
  facts: 'Fakta yang dilindungi berbeda',
  rights_claims: 'Klaim hak yang sudah ditinjau berbeda',
  destination: 'Data tujuan berubah atau tidak tersedia',
  partner_profile: 'Profil mitra yang sudah ada perlu ditinjau',
};
const FIELDS: Record<string, string> = {
  title: 'judul', summary: 'ringkasan', problem: 'masalah', solution: 'solusi', intended_users: 'pengguna',
  sector: 'sektor', stage: 'tahap', keywords: 'kata kunci', facts: 'fakta', private_notes: 'catatan privat',
  subtype: 'jenis mitra', thesis: 'fokus mitra', sectors: 'sektor', stages: 'tahap', regions: 'wilayah',
  support_forms: 'bentuk dukungan', relationship_forms: 'bentuk kerja sama', review_expectations: 'harapan peninjauan',
  check_range: 'kisaran kontribusi', intake_from: 'awal penerimaan', intake_until: 'akhir penerimaan',
  contact_route: 'jalur kontak', external_url: 'tautan kontak',
};
const POLL_MS = 1_000;

type Failure = { error: ApiError; focus?: number };

function FailedAction({ failure, id, title, field }: { failure: Failure; id: string; title: string; field?: string }) {
  const { error } = failure;
  return (
    <ErrorSummary
      id={id} title={title} focusKey={failure.focus}
      errors={field ? [{ fieldId: field, message: error.message }] : undefined}>
      {[field ? null : error.message, error.requestId && `Kode rujukan ${error.requestId}.`].filter(Boolean).join(' ')}
    </ErrorSummary>
  );
}

function useMonitor<T>(
  id: string | undefined, pending: boolean, read: (id: string) => Promise<T>,
  receive: (state: T) => void, fail: (failure: Failure) => void,
) {
  useEffect(() => {
    if (!id || !pending) return;
    let stopped = false;
    let timer: number;
    const poll = async () => {
      try {
        const next = await read(id);
        if (!stopped) {
          receive(next);
          timer = window.setTimeout(poll, POLL_MS);
        }
      } catch (error) {
        if (!stopped) fail({ error: ApiError.from(error) });
      }
    };
    timer = window.setTimeout(poll, POLL_MS);
    return () => {
      stopped = true;
      window.clearTimeout(timer);
    };
  }, [id, pending, read, receive, fail]);
}

function Preview({ rows }: { rows: PreviewRow[] }) {
  return (
    <ul className="tr-stack">
      {rows.map((row) => (
        <li key={row.external_id} className="tr-panel tr-stack" style={{ overflowWrap: 'anywhere' }}>
          <h4 className="tr-sys-type-label">{row.resource === 'INVENTION' ? 'Inovasi' : 'Profil mitra'} · {row.external_id}</h4>
          <p>{ACTION[row.action]}{row.outcome ? ` · ${OUTCOME[row.outcome]}` : ''}</p>
          {row.mapped_fields.length ? <p>Pemetaan {row.mapped_fields.map((field) => FIELDS[field] ?? field).join(', ')}</p> : null}
          {row.skipped_fields.length ? <p>Lewati {row.skipped_fields.map((field) => FIELDS[field] ?? field).join(', ')}</p> : null}
          {row.conflicts.length ? <p>{row.conflicts.map((field) => CONFLICTS[field]).join('. ')}.</p> : null}
        </li>
      ))}
    </ul>
  );
}

function ImportPanel({ me }: { me: Me }) {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [mapPrivate, setMapPrivate] = useState(false);
  const [run, setRun] = useState<ImportStatus | null>(null);
  const [failure, setFailure] = useState<Failure | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [offset, setOffset] = useState(0);
  const uploadKey = useRef<string | null>(null);
  const actionKeys = useRef<Record<string, string>>({});
  const pending = Boolean(run && [run.validation, run.preview, run.apply].some((stage) => stage.status === 'PENDING'));
  useMonitor(run?.id, pending && !failure && !busy && offset === 0, readImport, setRun, setFailure);
  const canReview = run?.preview.status === 'SUCCEEDED' && run.apply.status === 'NOT_STARTED';
  const imported = run && run.committed > 0 && (run.apply.status === 'SUCCEEDED' || run.apply.status === 'CANCELLED');
  useEffect(() => {
    if (imported) router.refresh();
  }, [imported, router]);
  const fileHint = 'Format JSON versi 1. Maksimal 20 MiB dan 2.000 data.';
  const fileIds = fieldIds('portability-file', fileHint);

  async function stage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file || busy || pending) return;
    setBusy('upload');
    setFailure(null);
    uploadKey.current ??= newIdempotencyKey();
    try {
      setRun(await validateImport(file, me.active_party_id, mapPrivate, uploadKey.current));
      uploadKey.current = null;
      actionKeys.current = {};
      setConfirmed(false);
      setOffset(0);
    } catch (error) {
      setFailure({ error: ApiError.from(error), focus: Date.now() });
    } finally {
      setBusy(null);
    }
  }

  async function refresh(page = offset) {
    if (!run || busy) return;
    setBusy('refresh');
    setFailure(null);
    try {
      setRun(await readImport(run.id, page));
      setOffset(page);
    } catch (error) {
      setFailure({ error: ApiError.from(error) });
    } finally {
      setBusy(null);
    }
  }

  async function change(action: 'apply' | 'cancel') {
    if (!run || busy || (action === 'apply' && !confirmed)) return;
    setBusy(action);
    setFailure(null);
    const signature = `${action}-${run.version}`;
    actionKeys.current[signature] ??= newIdempotencyKey();
    try {
      const result = await changeImport(run.id, action, me.active_party_id, run.version, actionKeys.current[signature]);
      setRun({ ...result, rows: run.rows, next_offset: run.next_offset });
      setOffset(0);
    } catch (error) {
      setFailure({ error: ApiError.from(error), focus: Date.now() });
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="tr-panel tr-stack" aria-labelledby="portability-import-title">
      <h2 id="portability-import-title" className="tr-sys-type-heading-sm">Impor berkas JSON</h2>
      <form className="tr-stack" onSubmit={stage}>
        <Field ids={fileIds} label="Berkas JSON" hint={fileHint}>
          <input id={fileIds.id} type="file" accept=".json,application/json" className="tr-input"
            aria-describedby={fileIds.describedBy} style={{ maxInlineSize: '100%', minInlineSize: 0 }}
            onChange={(event) => { uploadKey.current = null; setFile(event.target.files?.[0] ?? null); }} />
        </Field>
        <Checkbox label="Petakan catatan privat ke draf" checked={mapPrivate}
          onChange={(checked) => { uploadKey.current = null; setMapPrivate(checked); }} />
        <Button type="submit" intent="primary" busy={busy === 'upload'}
          disabledReason={!file ? 'Pilih berkas terlebih dahulu.' : pending || busy ? 'Tunggu pekerjaan saat ini.' : null}>
          Validasi berkas
        </Button>
      </form>
      {failure ? <FailedAction failure={failure} title="Impor belum dapat dilanjutkan" id="portability-import-error" field={fileIds.id} /> : null}
      {run ? (
        <>
          <div role="status" className="tr-stack">
            <h3 className="tr-sys-type-heading-sm">Status impor</h3>
            <ul>
              <li>Validasi · {STATUS[run.validation.status]} · {run.validation.processed} data</li>
              <li>Pratinjau · {STATUS[run.preview.status]} · {run.preview.processed} dari {run.total} data</li>
              <li>Penerapan · {STATUS[run.apply.status]} · {run.apply.processed} dari {run.total} data</li>
            </ul>
            <p>{run.committed} tersimpan · {run.skipped} dilewati</p>
            {run.validation.status === 'FAILED' ? <p>Validasi gagal. Periksa skema dan isi berkas lalu unggah kembali.</p> : null}
            {run.preview.status === 'FAILED' || run.apply.status === 'FAILED' ? <p>Pekerjaan terhenti. Periksa data yang tersimpan sebelum memulai impor baru.</p> : null}
          </div>
          <Button busy={busy === 'refresh'} onClick={() => void refresh()}>Periksa status impor</Button>
          {run.preview.status === 'SUCCEEDED' ? (
            <section className="tr-stack" aria-labelledby="portability-preview">
              <h3 id="portability-preview" className="tr-sys-type-heading-sm">Pratinjau perubahan</h3>
              <p>Baris yang berkonflik akan dilewati. Selesaikan konflik di data asli, lalu unggah kembali untuk mendapat pratinjau baru.</p>
              <Preview rows={run.rows ?? []} />
              <div className="tr-row">
                {offset > 0 ? <Button onClick={() => void refresh(Math.max(0, offset - 50))}>Data sebelumnya</Button> : null}
                {run.next_offset != null ? <Button onClick={() => void refresh(run.next_offset ?? 0)}>Data berikutnya</Button> : null}
              </div>
            </section>
          ) : null}
          {canReview ? (
            <div className="tr-stack">
              <ContextSwitcher readOnly value={me.active_party_id} options={contextOptions(me)} actionLabel="Menerapkan atas nama" />
              <Checkbox label="Saya sudah meninjau pratinjau" checked={confirmed} onChange={setConfirmed} />
              <Button intent="primary" busy={busy === 'apply'} onClick={() => void change('apply')}
                disabledReason={confirmed ? null : 'Tinjau dan konfirmasi pratinjau terlebih dahulu.'}>Terapkan impor</Button>
            </div>
          ) : null}
          {pending || canReview ? <Button busy={busy === 'cancel'} onClick={() => void change('cancel')}>Batalkan impor</Button> : null}
        </>
      ) : <p>Pratinjau akan muncul setelah berkas lolos validasi.</p>}
    </section>
  );
}

function ExportPanel({ me, inventions }: { me: Me; inventions: InventionSummary[] }) {
  const [selected, setSelected] = useState('');
  const [documentId, setDocumentId] = useState('');
  const [documentVersion, setDocumentVersion] = useState('1');
  const [privateNotes, setPrivateNotes] = useState(false);
  const [job, setJob] = useState<ExportStatus | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [failure, setFailure] = useState<Failure | null>(null);
  const key = useRef<string | null>(null);
  useMonitor(job?.id, job?.status === 'PENDING' && !failure && !busy, readExport, setJob, setFailure);
  const documentIds = fieldIds('portability-document');
  const versionIds = fieldIds('portability-document-version');
  const options = inventions.flatMap((invention) => {
    const title = invention.title || 'Inovasi tanpa judul';
    return [
      ...(invention.has_draft ? [{ value: `DRAFT:${invention.id}`, label: `${title} · Draf` }] : []),
      ...(invention.published_number ? [{ value: `PUBLISHED:${invention.id}`, label: `${title} · Versi terbit ${invention.published_number}` }] : []),
    ];
  });

  async function queue(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || job?.status === 'PENDING') return;
    const selections: ExportRequest['selections'] = [];
    const [version, id] = selected.split(':');
    if (id && (version === 'DRAFT' || version === 'PUBLISHED')) {
      selections.push({ kind: 'INVENTION', invention_id: id, version, include_private_notes: privateNotes });
    }
    if (documentId.trim()) {
      selections.push({ kind: 'DOCUMENT', document_id: documentId.trim(), version: Number(documentVersion) });
    }
    if (!selections.length) return;
    setBusy('export');
    setFailure(null);
    key.current ??= newIdempotencyKey();
    try {
      setJob(await createExport({ acting_party_id: me.active_party_id, expected_version: null, selections }, key.current));
      key.current = null;
    } catch (error) {
      setFailure({ error: ApiError.from(error), focus: Date.now() });
    } finally {
      setBusy(null);
    }
  }

  async function access(action: 'refresh' | 'download') {
    if (!job || busy) return;
    setBusy(action);
    setFailure(null);
    try {
      if (action === 'refresh') setJob(await readExport(job.id));
      else await downloadExport(job.id);
    } catch (error) {
      setFailure({ error: ApiError.from(error), focus: Date.now() });
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="tr-panel tr-stack" aria-labelledby="portability-export-title">
      <h2 id="portability-export-title" className="tr-sys-type-heading-sm">Ekspor pilihan</h2>
      <form className="tr-stack" onSubmit={queue}>
        <Select label="Versi inovasi" value={selected} options={options} emptyLabel={options.length ? 'Pilih versi inovasi' : 'Belum ada versi inovasi'}
          onChange={(value) => { key.current = null; setSelected(value); }} />
        {selected ? <Checkbox label="Sertakan catatan privat" checked={privateNotes}
          onChange={(checked) => { key.current = null; setPrivateNotes(checked); }} /> : null}
        <Field ids={documentIds} label="ID dokumen (opsional)">
          <input id={documentIds.id} className="tr-input" value={documentId} maxLength={36}
            onChange={(event) => { key.current = null; setDocumentId(event.target.value); }} />
        </Field>
        {documentId ? (
          <Field ids={versionIds} label="Nomor versi dokumen">
            <input id={versionIds.id} type="number" min={1} max={2147483647} required
              className="tr-input" value={documentVersion}
              onChange={(event) => { key.current = null; setDocumentVersion(event.target.value); }} />
          </Field>
        ) : null}
        <ContextSwitcher readOnly value={me.active_party_id} options={contextOptions(me)} actionLabel="Mengekspor atas nama" />
        <Button type="submit" intent="primary" busy={busy === 'export'}
          disabledReason={job?.status === 'PENDING' ? 'Ekspor sebelumnya sedang diproses.' : !selected && !documentId.trim() ? 'Pilih inovasi atau masukkan ID dokumen.' : null}>
          Siapkan ekspor
        </Button>
      </form>
      {failure ? <FailedAction failure={failure} title="Ekspor belum dapat dilanjutkan" id="portability-export-error" /> : null}
      {job ? (
        <>
          <div className="tr-stack" role="status">
            <p>Ekspor · {STATUS[job.status]}</p>
            {job.status === 'EXPIRED' ? <p>Hasil ekspor sudah tidak tersedia. Siapkan ekspor baru dengan akses yang masih berlaku.</p> : null}
            {job.status === 'FAILED' ? <p>Berkas tidak dapat dibuat. Periksa pilihan dan ukuran dokumen lalu coba lagi.</p> : null}
          </div>
          <div className="tr-row">
            <Button busy={busy === 'refresh'} onClick={() => void access('refresh')}>Periksa status ekspor</Button>
            {job.status === 'SUCCEEDED' ? <Button intent="primary" busy={busy === 'download'} onClick={() => void access('download')}>Unduh JSON</Button> : null}
          </div>
        </>
      ) : <p>Unduhan tersedia selama 24 jam dan mengikuti izin akses saat ini.</p>}
    </section>
  );
}

export function PortabilityView({ me, inventions }: { me: Me; inventions: InventionSummary[] }) {
  return (
    <Screen persona={readPersona(me.account.persona) ?? 'inovator'} current="inovasi" title="Impor dan ekspor data"
      back={<Link className="tr-link" href="/inventions">Kembali</Link>} provenance={PROVENANCE} context={<ContextBar me={me} />}>
      <ImportPanel me={me} />
      <ExportPanel me={me} inventions={inventions} />
    </Screen>
  );
}

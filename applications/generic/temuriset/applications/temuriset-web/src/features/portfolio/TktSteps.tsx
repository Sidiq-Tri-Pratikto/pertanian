'use client';

import { useState, type ChangeEvent } from 'react';

import { getJson } from '@/api/client';
import { ApiError } from '@/api/errors';
import { Select } from '@/components/tr/Select';
import { Status } from '@/components/tr/Status';
import { TextArea } from '@/components/tr/TextArea';
import { TktBar } from '@/components/tr/TktBadge';
import { Toggletip } from '@/components/tr/Toggletip';
import type { DocumentView } from '@/features/documents/model';
import { uploadFile } from '@/features/documents/upload';
import { t } from '@/features/i18n/t';
import { labelOf, STAGES } from '@/features/portfolio/model';
import { mismatch, TKT_DEFINITION, TKT_GROUPS, TKT_LEVELS } from '@/features/portfolio/tkt';

export type ReadinessDraft = {
  tkt_level: number;
  note: string;
  evidence: { document_id: string; version: number } | null;
};

type TktStepsProps = {
  value: ReadinessDraft | null;
  onChange: (next: ReadinessDraft | null) => void;
  stage: string;
  actingPartyId: string;
  documents: DocumentView[];
};

/** Owner's AVAILABLE documents, newest available version of each, as TKT evidence choices. */
function availableChoices(documents: DocumentView[]) {
  return documents.flatMap((document) => {
    const latest = [...document.versions].reverse().find((version) => version.file_state === 'AVAILABLE');
    return latest
      ? [{ value: `${document.id}:${latest.number}`, label: t('{title}, versi {n}', { title: document.title, n: latest.number }) }]
      : [];
  });
}

/**
 * Editor step 2 optional TKT picker (#tkt, spec 056 US1): grouped native radio list (1–9 + "Belum mengisi TKT"),
 * per-level Toggletip with example evidence, 9-segment bar, advisory stage mismatch note, optional note and evidence.
 */
export function TktSteps({ value, onChange, stage, actingPartyId, documents: initialDocuments }: TktStepsProps) {
  const [documents, setDocuments] = useState<DocumentView[]>(initialDocuments);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const choices = availableChoices(documents);
  const selectedEvidence = value?.evidence ? `${value.evidence.document_id}:${value.evidence.version}` : '';
  const mismatchKind = mismatch(stage, value?.tkt_level);
  const stageName = labelOf(STAGES, stage);

  function selectLevel(level: number | null) {
    if (level === null) {
      onChange(null);
      return;
    }
    onChange({
      tkt_level: level,
      note: value?.note ?? '',
      evidence: value?.evidence ?? null,
    });
  }

  function selectEvidence(encoded: string) {
    if (!value) return;
    if (!encoded) {
      onChange({ ...value, evidence: null });
      return;
    }
    const [documentId, version] = encoded.split(':');
    onChange({ ...value, evidence: { document_id: documentId, version: Number(version) } });
  }

  async function onUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file || !value) return;
    setUploading(true);
    setUploadError(null);
    setUploadStatus(t('Sedang diperiksa keamanannya'));
    try {
      const title = file.name.replace(/\.[^.]+$/, '').slice(0, 120) || t('Dokumentasi TKT');
      await uploadFile(file, title, actingPartyId, () => undefined).promise;
      // Poll briefly for the scanner worker to mark the uploaded file AVAILABLE.
      let found: { doc: DocumentView; version: number } | null = null;
      for (let attempt = 0; attempt < 10; attempt += 1) {
        const latest = await getJson('/api/v1/documents');
        setDocuments(latest);
        const match = latest.find((doc: DocumentView) => doc.title === title);
        const ready = match ? [...match.versions].reverse().find((v) => v.file_state === 'AVAILABLE') : undefined;
        if (match && ready) {
          found = { doc: match, version: ready.number };
          break;
        }
        await new Promise((resolve) => setTimeout(resolve, 600));
      }
      if (found) {
        onChange({ ...value, evidence: { document_id: found.doc.id, version: found.version } });
        setUploadStatus(null);
      } else {
        setUploadStatus(t('Sedang diperiksa keamanannya'));
      }
    } catch (error) {
      setUploadStatus(null);
      setUploadError(ApiError.from(error).message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <fieldset id="tkt" className="tr-fieldset tr-stack">
      <legend className="tr-field__label tr-sys-type-heading-sm">
        <span className="tr-row">
          <span>{t('Tingkat Kesiapterapan Teknologi (TKT) — opsional')}</span>
          <Toggletip label={t('Apa itu TKT?')} id="tip-apa-itu-tkt">
            {t(TKT_DEFINITION)}
          </Toggletip>
        </span>
      </legend>
      <p className="tr-muted tr-sys-type-support">
        {t('Nyatakan tingkat kesiapan teknologi (1–9) bila sudah diketahui. Nilainya dinyatakan inovator dan dapat diubah kapan saja.')}
      </p>

      <div className="tr-tkt-steps tr-stack">
        <label className="tr-tkt-row__label">
          <input type="radio" name="tkt-level" value="" checked={value === null} onChange={() => selectLevel(null)} />
          <span className="tr-sys-type-label">{t('Belum mengisi TKT')}</span>
        </label>

        {TKT_GROUPS.map((group) => (
          <div key={group.id} className="tr-stack">
            <p className="tr-sys-type-support-strong tr-muted">{`${t(group.label)} (${group.min}–${group.max})`}</p>
            {TKT_LEVELS.filter((item) => item.group === group.id).map((item) => (
              <div key={item.level} className="tr-tkt-row">
                <label className="tr-tkt-row__label">
                  <input
                    type="radio"
                    name="tkt-level"
                    value={String(item.level)}
                    checked={value?.tkt_level === item.level}
                    onChange={() => selectLevel(item.level)}
                  />
                  <span>
                    <span className="tr-sys-type-label">{`TKT ${item.level} · ${t(item.name)}`}</span>
                    <span className="tr-muted tr-sys-type-support tr-tkt-row__meaning">{t(item.meaning)}</span>
                  </span>
                </label>
                <Toggletip label={`TKT ${item.level}`} id={`tip-tkt-${item.level}`}>
                  {t('Contoh bukti: {example}', { example: t(item.example) })}
                </Toggletip>
              </div>
            ))}
          </div>
        ))}
      </div>

      {value !== null ? (
        <div className="tr-stack">
          <TktBar level={value.tkt_level} />
          {mismatchKind && stageName ? (
            <Status
              tone="neutral"
              label={
                mismatchKind === 'above'
                  ? t('TKT {level} biasanya sudah melewati tahap {stage}. Periksa lagi tahap atau TKT.', {
                      level: value.tkt_level,
                      stage: t(stageName),
                    })
                  : t('TKT {level} biasanya masih di bawah tahap {stage}. Periksa lagi tahap atau TKT.', {
                      level: value.tkt_level,
                      stage: t(stageName),
                    })
              }
            />
          ) : null}
          <TextArea
            id="tkt-catatan"
            label={t('Catatan TKT')}
            hint={t('Apa yang membuktikan tingkat ini? Misalnya: diuji di dua koperasi selama tiga bulan.')}
            limit={500}
            rows={2}
            value={value.note}
            onChange={(note) => onChange({ ...value, note })}
          />
          <Select
            id="tkt-dokumen"
            label={t('Dokumentasi TKT')}
            hint={t('Foto, laporan uji, atau sertifikat. Berkas tetap privat dan hanya dibagikan saat pitching.')}
            value={selectedEvidence}
            onChange={selectEvidence}
            options={choices}
            emptyLabel={t('Tanpa berkas dokumentasi')}
          />
          <div className="tr-field">
            <label htmlFor="tkt-unggah" className="tr-sys-type-support-strong">
              {t('Unggah berkas baru')}
            </label>
            <input
              id="tkt-unggah"
              type="file"
              accept="application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,image/png,image/jpeg,image/webp"
              disabled={uploading}
              onChange={(event) => void onUpload(event)}
            />
          </div>
          {uploadStatus ? <Status tone="neutral" label={uploadStatus} live /> : null}
          {uploadError ? <Status tone="danger" label={uploadError} live="alert" /> : null}
        </div>
      ) : null}
    </fieldset>
  );
}

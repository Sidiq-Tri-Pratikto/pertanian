'use client';

import { useState, type FormEvent } from 'react';

import { Button } from '@/components/tr/Button';
import { ErrorSummary } from '@/components/tr/ErrorSummary';
import { Field, fieldIds } from '@/components/tr/Field';
import { Status } from '@/components/tr/Status';
import { submitReport } from '@/features/privacy/api';
import {
  REPORT_CATEGORIES, REPORT_STATUS, SUBJECT_LABELS,
  type ActingScope, type Report, type ReportCategory, type ReportInput, type ReportSubject, type SectionData,
} from '@/features/privacy/model';
import { useIntent } from '@/features/privacy/useIntent';

type Props = { scope: ActingScope; subject: ReportSubject | null; initial: SectionData<Report> };

export function ReportForm({ scope, subject, initial }: Props) {
  const [reports, setReports] = useState(initial.data);
  const [category, setCategory] = useState<ReportCategory>('OTHER');
  const [label, setLabel] = useState('');
  const [reason, setReason] = useState('');
  const [invalid, setInvalid] = useState(0);
  const [receipt, setReceipt] = useState('');
  const action = useIntent(submitReport);
  const reasonError = invalid ? 'Isi alasan laporan.' : undefined;
  const reasonIds = fieldIds('alasan-laporan', undefined, reasonError);
  const categoryIds = fieldIds('kategori-laporan');
  const labelIds = fieldIds('label-laporan');
  const input: ReportInput = {
    acting_party_id: scope.id,
    expected_version: null,
    category,
    subject_type: subject?.type ?? 'OTHER',
    subject_id: subject?.id ?? null,
    subject_label: label.trim(),
    reason: reason.trim(),
  };

  async function send(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!input.reason) {
      setInvalid((count) => count + 1);
      return;
    }
    setInvalid(0);
    const result = await action.run(input);
    if (result) {
      setReports((current) => [result, ...current.filter((item) => item.id !== result.id)]);
      setReceipt(`Laporan ${result.case_number} diterima.`);
      setLabel('');
      setReason('');
    }
  }

  return (
    <section id="laporkan" className="tr-panel tr-stack" aria-labelledby="judul-laporan">
      <h2 id="judul-laporan" className="tr-sys-type-heading-sm">Laporkan masalah</h2>
      <p>Laporan ditangani secara privat dan tidak memengaruhi reputasi publik.</p>
      <p>Bertindak sebagai <strong>{scope.label}</strong></p>
      {subject ? <p>Objek laporan <strong>{SUBJECT_LABELS[subject.type]}</strong></p> : null}
      <form className="tr-stack" onSubmit={send} noValidate aria-busy={action.busy}>
        {reasonError ? (
          <ErrorSummary id="galat-laporan" focusKey={invalid} errors={[{ fieldId: reasonIds.id, message: reasonError }]} />
        ) : action.failure ? (
          <ErrorSummary id="galat-laporan" focusKey={action.attempt} title="Laporan belum terkirim">
            {action.failure.message}{action.failure.requestId ? ` ID referensi ${action.failure.requestId}.` : ''}
          </ErrorSummary>
        ) : null}
        <Field ids={categoryIds} label="Kategori">
          <select id={categoryIds.id} className="tr-select" value={category} onChange={(event) => setCategory(event.target.value as ReportCategory)}>
            {Object.entries(REPORT_CATEGORIES).map(([value, name]) => <option key={value} value={value}>{name}</option>)}
          </select>
        </Field>
        <Field ids={labelIds} label="Nama objek bila diperlukan">
          <input id={labelIds.id} className="tr-input" value={label} maxLength={200} onChange={(event) => setLabel(event.target.value)} />
        </Field>
        <Field ids={reasonIds} label="Alasan laporan" required error={reasonError}>
          <textarea
            id={reasonIds.id}
            className="tr-textarea"
            value={reason}
            maxLength={4000}
            required
            aria-invalid={Boolean(reasonError)}
            aria-describedby={reasonIds.describedBy}
            onChange={(event) => { setReason(event.target.value); setInvalid(0); }}
          />
        </Field>
        <Button type="submit" intent="primary" busy={action.busy} disabledReason={action.blocked(input)}>Kirim laporan</Button>
      </form>
      <p role="status">{receipt}</p>
      <h3 className="tr-sys-type-label">Laporan Anda</h3>
      {initial.failure ? (
        <Status label="Daftar laporan belum tersedia" tone="warning">
          {initial.failure.message}{initial.failure.requestId ? ` ID referensi ${initial.failure.requestId}.` : ''}
        </Status>
      ) : null}
      {reports.length ? (
        <ul className="tr-stack">
          {reports.map((report) => <li key={report.id}>{report.case_number} · {REPORT_STATUS[report.status]}</li>)}
        </ul>
      ) : initial.failure ? null : <p className="tr-muted">Belum ada laporan.</p>}
    </section>
  );
}

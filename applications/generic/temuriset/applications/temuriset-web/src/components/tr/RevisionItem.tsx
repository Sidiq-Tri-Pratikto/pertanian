import type { ReactNode } from 'react';

import { ChoiceGroup } from '@/components/tr/ChoiceGroup';
import { Status } from '@/components/tr/Status';
import { TextArea } from '@/components/tr/TextArea';

export type RevisionValue = { response?: string; text?: string };

export const RESPONSES = [
  { value: 'CAN', label: 'Dapat dipenuhi' },
  { value: 'DISCUSS', label: 'Perlu diskusi' },
  { value: 'CANNOT', label: 'Belum dapat dipenuhi', hint: 'Jawaban jujur ini tetap sah untuk dikirim. Ini bukan persetujuan.' },
];

type RevisionItemProps = {
  id: string;
  round: number;
  index: number;
  question: string;
  reason?: string;
  required: boolean;
  due?: string | null;
  value: RevisionValue;
  onChange: (value: RevisionValue) => void;
  attachments?: ReactNode;
  review?: ReactNode;
  error?: string;
};

function dueDate(value: string): string {
  return new Intl.DateTimeFormat('id-ID', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`));
}

/** Port of TR.RevisionItem: one question, its reason, and an answer that may honestly be no. */
export function RevisionItem({ id, round, index, question, reason, required, due, value, onChange, attachments, review, error }: RevisionItemProps) {
  return (
    <article className="tr-revision" id={id}>
      <div className="tr-req__head">
        <h3 className="tr-sys-type-label">{`Putaran ${round} · Pertanyaan ${index}`}</h3>
        <Status tone={required ? 'action' : 'neutral'} icon={null} label={required ? 'Wajib dijawab' : 'Opsional'} />
      </div>
      <p className="tr-sys-type-body-strong">{question}</p>
      {reason ? (
        <p>
          <span className="tr-muted">Alasan: </span>
          {reason}
        </p>
      ) : null}
      {due ? <p className="tr-muted tr-sys-type-support">{`Batas waktu: ${dueDate(due)}`}</p> : null}
      <ChoiceGroup
        name={`${id}-response`}
        legend="Tanggapan Anda"
        required={required}
        options={RESPONSES}
        value={value.response}
        onChange={(response) => onChange({ ...value, response })}
        error={error}
      />
      <TextArea
        label="Penjelasan"
        hint="Anda dapat menjelaskan apa yang sudah ada dan apa yang belum."
        rows={3}
        value={value.text ?? ''}
        onChange={(text) => onChange({ ...value, text })}
        id={`${id}-text`}
      />
      {attachments}
      {review}
    </article>
  );
}

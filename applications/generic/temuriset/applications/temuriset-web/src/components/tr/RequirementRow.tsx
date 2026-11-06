import type { ReactNode } from 'react';

import { Status, type Tone } from '@/components/tr/Status';

type Result = 'PASS' | 'FAIL' | 'UNKNOWN' | 'NOT_APPLICABLE';

const RESULT: Record<Result, [string, Tone]> = {
  PASS: ['Terpenuhi', 'success'],
  FAIL: ['Tidak terpenuhi', 'danger'],
  UNKNOWN: ['Belum diketahui', 'warning'],
  NOT_APPLICABLE: ['Tidak berlaku', 'neutral'],
};
const STAGE: Record<string, string> = {
  SUBMISSION: 'Saat pengajuan',
  DISCUSSION: 'Saat diskusi',
  PILOT: 'Saat pilot',
  COMMERCIALIZATION: 'Saat komersialisasi',
};
const MODE: Record<string, string> = {
  DECLARATION: 'Pernyataan',
  DOCUMENT_PRESENT: 'Dokumen tersedia',
  REVIEWER_CONFIRMED: 'Diperiksa peninjau',
};

type RequirementRowProps = {
  label: string;
  result: Result;
  stage?: string;
  mandatory?: boolean;
  mode?: string;
  reason?: string;
  source?: string;
  action?: ReactNode;
  /** Recorded deviation D6: the row may sit directly under a section heading. */
  headingLevel?: 3 | 4;
};

/** Port of TR.RequirementRow: a requirement, what it means, and when it applies. */
export function RequirementRow({ label, result, stage, mandatory, mode, reason, source, action, headingLevel = 4 }: RequirementRowProps) {
  const [text, tone] = RESULT[result];
  // Later-stage work keeps its real result but is never styled as a submission blocker.
  const later = Boolean(stage && stage !== 'SUBMISSION' && result !== 'PASS');
  const Heading = `h${headingLevel}` as const;
  const facts = [stage ? STAGE[stage] : undefined, mandatory === false ? 'Preferensi' : 'Wajib', mode ? MODE[mode] : undefined].filter(Boolean).join(' · ');
  return (
    <li className="tr-req">
      <div className="tr-req__head">
        <Heading className="tr-sys-type-label">{label}</Heading>
        <Status tone={later ? 'neutral' : tone} icon={result === 'NOT_APPLICABLE' ? 'minus' : undefined} label={text} />
      </div>
      <p className="tr-muted tr-sys-type-support">{facts}</p>
      {later ? <p className="tr-sys-type-support">Untuk tahap berikutnya. Tidak menghalangi pengajuan.</p> : null}
      {reason ? <p>{reason}</p> : null}
      {source ? <p className="tr-muted tr-sys-type-support">{`Sumber: ${source}`}</p> : null}
      {action ? <div className="tr-row">{action}</div> : null}
    </li>
  );
}

import type { ReactNode } from 'react';

import { SummaryList } from '@/components/tr/SummaryList';

export type MandateReviewValues = {
  title: string;
  outcome: string;
  included: string;
  excluded: string;
  support: string;
  stages: string;
  forms: string;
  timing: string;
  financial: ReactNode;
  requirements: string[];
};

const EMPTY = <span className="tr-muted">Belum diisi</span>;

/** What the mandate will say, as a check-your-answers list, before it goes live. */
export function MandateReview({ values }: { values: MandateReviewValues }) {
  const rows: [string, ReactNode][] = [
    ['Judul', values.title],
    ['Hasil', values.outcome],
    ['Termasuk', values.included],
    ['Tidak termasuk', values.excluded],
    ['Dukungan', values.support],
    ['Tahap yang diterima', values.stages],
    ['Bentuk kerja sama', values.forms],
    ['Waktu', values.timing],
    ['Dasar keuangan', values.financial],
    [
      'Syarat',
      values.requirements.length ? (
        <ul>
          {values.requirements.map((label) => (
            <li key={label}>{label}</li>
          ))}
        </ul>
      ) : null,
    ],
  ];
  return <SummaryList rows={rows.map(([label, value]) => ({ id: label, label, value: value || EMPTY }))} />;
}

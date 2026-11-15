import Link from 'next/link';

import { EmptyState } from '@/components/tr/EmptyState';
import { STAGES } from '@/features/portfolio/model';
import type { Teaser } from '@/features/subscriptions/api';
import { AuthShell } from '@/views/AuthShell';

/** The brief public summary an investor opens from an email. Anything more needs a normal signup. */
export function TeaserView({ teaser }: { teaser: Teaser | null }) {
  if (!teaser) {
    return (
      <AuthShell title="Inovasi tidak tersedia">
        <EmptyState
          icon="question"
          title="Ringkasan ini tidak tersedia"
          action={
            <Link className="tr-link" href="/langganan">
              Atur kabar inovasi Anda
            </Link>
          }>
          Pengelolanya mungkin sudah menarik inovasi ini dari kabar untuk investor.
        </EmptyState>
      </AuthShell>
    );
  }
  const stage = STAGES.find((item) => item.value === teaser.stage)?.label;
  const detail = `/inventions/${teaser.id}`;
  return (
    <AuthShell title={teaser.title} subtitle={`Inovator: ${teaser.inventor_name}`}>
      <section className="tr-panel tr-stack" aria-labelledby="ringkasan">
        <h2 id="ringkasan" className="tr-sys-type-heading-sm">
          Ringkasan
        </h2>
        <p>{teaser.summary}</p>
        <p className="tr-muted">{[teaser.sector, stage].filter(Boolean).join(' · ')}</p>
        {teaser.keywords.length ? <p className="tr-muted tr-sys-type-support">{`Kata kunci: ${teaser.keywords.join(', ')}`}</p> : null}
      </section>
      <section className="tr-panel tr-stack" aria-labelledby="detail">
        <h2 id="detail" className="tr-sys-type-heading-sm">
          Ingin tahu lebih banyak?
        </h2>
        <p>Masalah, solusi, fakta, bukti, dan cara menghubungi inovator tersedia untuk akun investor.</p>
        <div className="tr-row">
          <Link className="tr-btn tr-btn--primary" href={`/start?kembali=${encodeURIComponent(detail)}`}>
            Daftar untuk melihat detail
          </Link>
          <Link className="tr-link" href={`/start?masuk=1&kembali=${encodeURIComponent(detail)}`}>
            Sudah punya akun? Masuk
          </Link>
        </div>
      </section>
    </AuthShell>
  );
}

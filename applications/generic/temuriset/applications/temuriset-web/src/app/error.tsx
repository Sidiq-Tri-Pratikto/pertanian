'use client';

import { EmptyState } from '@/components/tr/EmptyState';
import { Button } from '@/components/tr/Button';

/** Shown when a page could not reach the service; nothing the visitor typed is lost by retrying. */
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <main id="isi" className="tr-root tr-page tr-section">
      <h1 className="tr-sys-type-heading-lg">Layanan belum tersedia</h1>
      <EmptyState icon="alert" title="Halaman ini belum dapat dimuat" action={<Button icon="refresh" onClick={reset}>Coba lagi</Button>}>
        Layanan TemuRiset belum dapat dihubungi. Coba lagi beberapa saat lagi.
      </EmptyState>
    </main>
  );
}

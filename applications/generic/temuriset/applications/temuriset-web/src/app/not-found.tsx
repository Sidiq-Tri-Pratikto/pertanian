import Link from 'next/link';

import { EmptyState } from '@/components/tr/EmptyState';

export default function NotFound() {
  return (
    <main id="isi" className="tr-root tr-page tr-section">
      <h1 className="tr-sys-type-heading-lg">Halaman tidak ditemukan</h1>
      <EmptyState
        icon="question"
        title="Alamat ini tidak tersedia"
        action={
          <Link className="tr-link" href="/">
            Kembali ke awal
          </Link>
        }>
        Periksa alamatnya, atau kembali ke halaman awal.
      </EmptyState>
    </main>
  );
}

'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { ApiError } from '@/api/errors';
import { Checkbox } from '@/components/tr/Checkbox';
import { Status } from '@/components/tr/Status';
import { setInvestorDigest } from '@/features/subscriptions/api';

type Props = { inventionId: string; actingPartyId: string; version: number; enabled: boolean };

/** The managing party decides whether investor alerts and digests may include the published invention. */
export function InvestorDigestToggle({ inventionId, actingPartyId, version, enabled }: Props) {
  const router = useRouter();
  const [on, setOn] = useState(enabled);
  const [failure, setFailure] = useState<string | null>(null);

  async function change(next: boolean) {
    setOn(next);
    setFailure(null);
    try {
      await setInvestorDigest(inventionId, actingPartyId, version, next);
      router.refresh();
    } catch (error) {
      setOn(!next);
      const failed = ApiError.from(error);
      setFailure(failed.code === 'STALE_VERSION' ? 'Inovasi ini baru saja berubah. Muat ulang halaman lalu coba lagi.' : failed.message);
    }
  }

  return (
    <section className="tr-panel tr-stack" aria-labelledby="kabar-investor">
      <h2 id="kabar-investor" className="tr-sys-type-heading-sm">
        Kabar untuk investor
      </h2>
      <Checkbox
        id="investor-digest"
        label="Sertakan dalam kabar untuk investor yang berlangganan"
        hint="Investor yang minatnya cocok menerima judul, ringkasan, sektor, tahap, dan nama Anda bila profil publik Anda terbit. Detail tetap memerlukan akun."
        checked={on}
        onChange={(next) => void change(next)}
      />
      {failure ? <Status tone="danger" icon="alert" label={failure} live="alert" /> : null}
    </section>
  );
}

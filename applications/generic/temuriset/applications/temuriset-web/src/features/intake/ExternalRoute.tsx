'use client';

import { useState } from 'react';

import { newIdempotencyKey } from '@/api/client';
import { Link } from '@/components/tr/Link';
import { recordHandoff } from '@/features/intake/api';

type Props = { partyId: string; actingPartyId: string; url: string; /** False for the partner opening its own form. */ record: boolean };

/** A partner's own form. Following it is noted as a handoff and never becomes a pitch (AC24). */
export function ExternalRoute({ partyId, actingPartyId, url, record }: Props) {
  const [unrecorded, setUnrecorded] = useState(false);

  function follow() {
    if (!record) return;
    setUnrecorded(false);
    // The person is already on their way to the other site, so a failure here only changes what this page says.
    recordHandoff(partyId, actingPartyId, newIdempotencyKey()).catch(() => setUnrecorded(true));
  }

  return (
    <div className="tr-stack">
      <p className="tr-muted">Mitra ini menerima lewat formulirnya sendiri. Tautan ini membuka situs lain dan bukan pitching yang terkirim. TemuRiset hanya mencatat bahwa Anda membukanya.</p>
      <p>
        <Link href={url} external onClick={follow}>
          Buka formulir mitra
        </Link>
      </p>
      {unrecorded ? (
        <p className="tr-muted" role="status">
          Pembukaan ini belum tercatat di TemuRiset. Anda tetap dapat mengisi formulirnya.
        </p>
      ) : null}
    </div>
  );
}

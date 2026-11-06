'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { newIdempotencyKey } from '@/api/client';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Status } from '@/components/tr/Status';
import { createMandate } from '@/features/intake/api';

/** Starts a mandate as a draft and opens its editor. */
export function NewMandate({ actingPartyId }: { actingPartyId: string }) {
  const router = useRouter();
  const [key] = useState(newIdempotencyKey);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);

  async function start() {
    if (busy) return;
    setBusy(true);
    setFailure(null);
    try {
      const created = await createMandate(actingPartyId, key);
      router.push(`/opportunities/${created.id}/edit`);
    } catch (error) {
      setFailure(ApiError.from(error).message);
      setBusy(false);
    }
  }

  return (
    <div className="tr-stack">
      {failure ? (
        <Status tone="danger" icon="alert" label="Mandat belum dibuat" live="alert">
          <p>{failure}</p>
        </Status>
      ) : null}
      <div className="tr-row">
        <Button intent="primary" icon="arrow" busy={busy} busyLabel="Membuat…" onClick={start}>
          Buat mandat
        </Button>
      </div>
    </div>
  );
}

'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Status } from '@/components/tr/Status';
import { createInvention } from '@/features/portfolio/api';

/** Starts an empty draft and opens step 1 of the editor. */
export function NewInventionButton({ actingPartyId }: { actingPartyId: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);

  async function create() {
    if (busy) return;
    setBusy(true);
    setFailure(null);
    try {
      const invention = await createInvention(actingPartyId);
      router.push(`/inventions/${invention.id}/edit?step=1`);
    } catch (error) {
      setFailure(ApiError.from(error).message);
      setBusy(false);
    }
  }

  return (
    <div className="tr-stack">
      {failure ? (
        <Status tone="danger" icon="alert" label="Inovasi belum dibuat" live="alert">
          <p>{failure}</p>
        </Status>
      ) : null}
      <div className="tr-row">
        <Button intent="primary" icon="check" busy={busy} busyLabel="Membuat…" onClick={create}>
          Tambah inovasi
        </Button>
      </div>
    </div>
  );
}

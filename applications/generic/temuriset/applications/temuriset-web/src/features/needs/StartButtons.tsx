'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { newIdempotencyKey } from '@/api/client';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Select } from '@/components/tr/Select';
import { Status } from '@/components/tr/Status';
import { createFundingRequest, createSupportRequest } from '@/features/needs/api';

function Failure({ message, label }: { message: string | null; label: string }) {
  return message ? (
    <Status tone="danger" icon="alert" label={label} live="alert">
      <p>{message}</p>
    </Status>
  ) : null;
}

/** Starts a support request for one published invention and opens it. */
export function NewSupportRequest({ actingPartyId, inventions, initial }: { actingPartyId: string; inventions: { id: string; title: string }[]; initial?: string }) {
  const router = useRouter();
  const [invention, setInvention] = useState(initial && inventions.some((item) => item.id === initial) ? initial : (inventions[0]?.id ?? ''));
  const [key] = useState(newIdempotencyKey);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);

  async function start() {
    if (busy || !invention) return;
    setBusy(true);
    setFailure(null);
    try {
      const created = await createSupportRequest(actingPartyId, invention, key);
      router.push(`/support-requests/${created.id}`);
    } catch (error) {
      setFailure(ApiError.from(error).message);
      setBusy(false);
    }
  }

  if (!inventions.length) {
    return <p className="tr-muted">Terbitkan inovasi terlebih dahulu. Kebutuhan dukungan selalu merujuk versi yang sudah terbit.</p>;
  }
  return (
    <div className="tr-stack">
      <Failure message={failure} label="Kebutuhan belum dibuat" />
      <Select label="Untuk inovasi" value={invention} onChange={setInvention} options={inventions.map((item) => ({ value: item.id, label: item.title }))} emptyLabel={null} />
      <div className="tr-row">
        <Button intent="primary" icon="arrow" busy={busy} busyLabel="Membuat…" onClick={start}>
          Tambah kebutuhan dukungan
        </Button>
      </div>
    </div>
  );
}

/** Starts a company raise as a draft and opens its editor. */
export function NewFundingRequest({ actingPartyId }: { actingPartyId: string }) {
  const router = useRouter();
  const [key] = useState(newIdempotencyKey);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);

  async function start() {
    if (busy) return;
    setBusy(true);
    setFailure(null);
    try {
      const created = await createFundingRequest(actingPartyId, key);
      router.push(`/funding-requests/${created.id}/edit`);
    } catch (error) {
      setFailure(ApiError.from(error).message);
      setBusy(false);
    }
  }

  return (
    <div className="tr-stack">
      <Failure message={failure} label="Pendanaan belum dibuat" />
      <div className="tr-row">
        <Button icon="building" busy={busy} busyLabel="Membuat…" onClick={start}>
          Mulai pendanaan perusahaan
        </Button>
      </div>
    </div>
  );
}

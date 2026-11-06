'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Button } from '@/components/tr/Button';
import { mark } from '@/features/discovery/api';

type Props = { subjectType: string; subjectId: string; title: string; saved: boolean; actingPartyId: string };

/** Save and "Kurang relevan" act for the acting party only; nothing public changes. */
export function ItemActions({ subjectType, subjectId, title, saved, actingPartyId }: Props) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  async function act(kind: 'saved-items' | 'discovery-feedback', on: boolean) {
    setBusy(true);
    setFailed(false);
    try {
      await mark(kind, subjectType, subjectId, actingPartyId, on);
      router.refresh();
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Button busy={busy} busyLabel="Menyimpan" onClick={() => act('saved-items', !saved)}>
        {saved ? 'Hapus dari simpanan' : 'Simpan'}
        <span className="tr-sr">{`: ${title}`}</span>
      </Button>
      <Button busy={busy} busyLabel="Menyimpan" onClick={() => act('discovery-feedback', true)}>
        Kurang relevan
        <span className="tr-sr">{`: ${title}`}</span>
      </Button>
      {failed ? (
        <span role="status" className="tr-muted tr-sys-type-support">
          Belum tersimpan. Coba lagi.
        </span>
      ) : null}
    </>
  );
}

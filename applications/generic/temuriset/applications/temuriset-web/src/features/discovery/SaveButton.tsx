'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Button } from '@/components/tr/Button';
import { mark } from '@/features/discovery/api';
import { t } from '@/features/i18n/t';

type Props = {
  subjectType: string;
  subjectId: string;
  title: string;
  saved: boolean;
  actingPartyId: string;
  /** Words for the unsaved state, such as "Simpan inovasi". */
  label?: string;
  intent?: 'primary' | 'secondary';
};

/** Saves or unsaves one subject for the acting party only; nothing public changes. A failure says so and keeps the state. */
export function SaveButton({ subjectType, subjectId, title, saved, actingPartyId, label = t('Simpan'), intent }: Props) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  async function toggle() {
    setBusy(true);
    setFailed(false);
    try {
      await mark('saved-items', subjectType, subjectId, actingPartyId, !saved);
      router.refresh();
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Button intent={intent} busy={busy} busyLabel={t('Menyimpan')} onClick={() => void toggle()}>
        {saved ? t('Hapus dari simpanan') : t(label)}
        <span className="tr-sr">{`: ${title}`}</span>
      </Button>
      {failed ? (
        <span role="status" className="tr-muted tr-sys-type-support">
          {t('Belum tersimpan. Coba lagi.')}
        </span>
      ) : null}
    </>
  );
}

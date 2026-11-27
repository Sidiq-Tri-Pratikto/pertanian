'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Button } from '@/components/tr/Button';
import { mark } from '@/features/discovery/api';
import { SaveButton } from '@/features/discovery/SaveButton';
import { t } from '@/features/i18n/t';

type Props = { subjectType: string; subjectId: string; title: string; saved: boolean; actingPartyId: string };

/** Save and "Kurang relevan" act for the acting party only; nothing public changes. */
export function ItemActions({ subjectType, subjectId, title, saved, actingPartyId }: Props) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  async function hide() {
    setBusy(true);
    setFailed(false);
    try {
      await mark('discovery-feedback', subjectType, subjectId, actingPartyId, true);
      router.refresh();
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <SaveButton subjectType={subjectType} subjectId={subjectId} title={title} saved={saved} actingPartyId={actingPartyId} />
      <Button busy={busy} busyLabel={t('Menyimpan')} onClick={() => void hide()}>
        Kurang relevan
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

import NextLink from 'next/link';

import type { Me } from '@/api/client';
import { EmptyState } from '@/components/tr/EmptyState';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import { ContextBar } from '@/features/ContextBar';
import { MandateForm } from '@/features/intake/MandateForm';
import type { Mandate } from '@/features/intake/model';
import { readPersona } from '@/features/persona';
import { MandateCard } from '@/views/intake/MandateCard';
import { PROVENANCE } from '@/views/parts';
import { t } from '@/features/i18n/t';

/** S09: the editor for the partner who owns the mandate, and an honest state for anyone else. */
export function MandateEditView({ me, mandate }: { me: Me; mandate: Mandate }) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  const allowed = mandate.partner_party_id === me.active_party_id && (me.capabilities?.includes('edit_portfolio') ?? false);
  const ended = mandate.status === 'CLOSED' || mandate.status === 'EXPIRED';
  return (
    <Screen
      persona={persona}
      current="mandat"
      title={t('Ubah mandat')}
      subtitle={allowed && mandate.title ? `${mandate.title} · Versi ${mandate.number}` : undefined}
      back={
        <NextLink className="tr-link" href="/opportunities">
          {t('Kembali ke mandat')}
        </NextLink>
      }
      provenance={PROVENANCE}
      context={<ContextBar me={me} />}>
      {!allowed ? (
        <EmptyState icon="lock" title={t('Akses dibatasi')}>
          {t('Hanya pihak pemilik mandat dengan izin mengubah yang dapat membuka halaman ini. Periksa konteks yang sedang Anda pakai.')}
        </EmptyState>
      ) : ended ? (
        <>
          <Status tone="neutral" icon="lock" label={t('Tidak dapat diubah')}>
            <p>{t('Mandat ini sudah ditutup atau berakhir, sehingga isinya tidak dapat diubah. Pitching yang sudah terkirim tidak berubah.')}</p>
          </Status>
          <MandateCard mandate={mandate} />
        </>
      ) : (
        <MandateForm key={mandate.id} mandate={mandate} actingPartyId={me.active_party_id} />
      )}
    </Screen>
  );
}

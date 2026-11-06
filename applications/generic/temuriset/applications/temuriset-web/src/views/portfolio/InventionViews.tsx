import Link from 'next/link';

import type { Me } from '@/api/client';
import { Button } from '@/components/tr/Button';
import { EmptyState } from '@/components/tr/EmptyState';
import { FactSource } from '@/components/tr/FactSource';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import { ContextBar } from '@/features/ContextBar';
import { readPersona } from '@/features/persona';
import { NewInventionButton } from '@/features/portfolio/NewInventionButton';
import {
  CLAIM_KINDS,
  CLAIM_STATUSES,
  labelOf,
  STAGES,
  STATUS_LABEL,
  type Invention,
  type InventionSummary,
  type PublicInvention,
} from '@/features/portfolio/model';
import { PROVENANCE } from '@/views/parts';

/** S04 list: the acting party's inventions, drafts and archived ones included. */
export function InventionsView({ me, inventions }: { me: Me; inventions: InventionSummary[] }) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  return (
    <Screen
      persona={persona}
      current="inovasi"
      title="Inovasi Saya"
      subtitle="Profil inovasi yang Anda kelola. Draf hanya terlihat oleh Anda."
      provenance={PROVENANCE}
      context={<ContextBar me={me} />}>
      <p><Link className="tr-link" href="/inventions/import">Impor dan ekspor data</Link></p>
      {inventions.length ? (
        <>
          <ul className="tr-stack">
            {inventions.map((invention) => (
              <li key={invention.id} className="tr-panel tr-stack">
                <h2 className="tr-sys-type-heading-sm">{invention.title || 'Inovasi tanpa judul'}</h2>
                <p className="tr-row">
                  <Status tone={invention.status === 'PUBLISHED' ? 'success' : 'neutral'} label={STATUS_LABEL[invention.status] ?? invention.status} />
                  {invention.published_number ? <span className="tr-muted">{`Versi terbit ${invention.published_number}`}</span> : null}
                  {invention.published_number && invention.has_draft ? <span className="tr-tag tr-sys-type-support">Ada draf perubahan</span> : null}
                </p>
                <p>
                  <Link className="tr-link" href={`/inventions/${invention.id}`}>
                    Buka<span className="tr-sr">{` ${invention.title || 'inovasi tanpa judul'}`}</span>
                  </Link>
                </p>
              </li>
            ))}
          </ul>
          <NewInventionButton actingPartyId={me.active_party_id} />
        </>
      ) : (
        <EmptyState icon="bulb" title="Belum ada inovasi" action={<NewInventionButton actingPartyId={me.active_party_id} />}>
          Susun profil dalam empat langkah. Draf tersimpan walau belum lengkap, dan hanya versi yang Anda terbitkan yang terlihat oleh orang lain.
        </EmptyState>
      )}
    </Screen>
  );
}

type DetailProps = {
  me: Me;
  /** The owner's view, when the acting party manages it. */
  invention?: Invention;
  /** The public projection, for everyone else. */
  publicView?: PublicInvention;
  justPublished?: number;
};

/** S04 detail: honest about what exists now, what is planned, and who says so (UX-04). */
export function InventionView({ me, invention, publicView, justPublished }: DetailProps) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  const shown = invention ? (invention.published ?? invention.draft) : publicView;
  const owner = Boolean(invention);
  if (!shown) {
    return (
      <Screen persona={persona} title="Inovasi tidak ditemukan" provenance={PROVENANCE} context={<ContextBar me={me} />}>
        <EmptyState icon="question" title="Inovasi ini tidak tersedia" action={<Link className="tr-link" href="/inventions">Kembali ke Inovasi Saya</Link>}>
          Inovasi mungkin belum terbit, sudah diarsipkan, atau dikelola pihak lain.
        </EmptyState>
      </Screen>
    );
  }
  const current = shown.facts.filter((fact) => fact.timing === 'CURRENT');
  const planned = shown.facts.filter((fact) => fact.timing !== 'CURRENT');
  const action = owner ? (
    <Link className="tr-btn tr-btn--primary" href={`/inventions/${invention!.id}/edit?step=1`}>
      {invention!.draft && invention!.published ? 'Lanjutkan draf perubahan' : 'Ubah inovasi'}
    </Link>
  ) : (
    <Button intent="primary" disabledReason="Menyimpan inovasi tersedia bersama fitur Jelajahi.">
      Simpan inovasi
    </Button>
  );
  return (
    <Screen
      persona={persona}
      current={owner ? 'inovasi' : undefined}
      title={shown.title || 'Inovasi tanpa judul'}
      subtitle={owner ? undefined : `Dikelola ${publicView!.managing_party_name}`}
      back={
        <Link className="tr-link" href={owner ? '/inventions' : '/discover'}>
          Kembali
        </Link>
      }
      provenance={PROVENANCE}
      context={<ContextBar me={me} />}>
      {justPublished ? <Status tone="success" label={`Versi ${justPublished} sudah terbit`} live /> : null}
      {owner && !invention!.published ? <Status tone="neutral" label="Draf, belum terbit" /> : null}
      {owner && invention!.status === 'ARCHIVED' ? <Status tone="warning" label="Diarsipkan" /> : null}
      <div className="tr-row">{action}</div>
      <section className="tr-panel tr-stack" aria-labelledby="ringkasan-inovasi">
        <h2 id="ringkasan-inovasi" className="tr-sys-type-heading-sm">
          Ringkasan
        </h2>
        {shown.summary ? <p>{shown.summary}</p> : null}
        <dl className="tr-facts">
          <div>
            <dt className="tr-sys-type-support-strong">Masalah</dt>
            <dd>{shown.problem || 'Belum diisi'}</dd>
          </div>
          <div>
            <dt className="tr-sys-type-support-strong">Solusi saat ini</dt>
            <dd>{shown.solution || 'Belum diisi'}</dd>
          </div>
          <div>
            <dt className="tr-sys-type-support-strong">Tahap</dt>
            <dd>{labelOf(STAGES, shown.stage) || 'Belum diisi'}</dd>
          </div>
          <div>
            <dt className="tr-sys-type-support-strong">Pengguna</dt>
            <dd>{shown.intended_users || 'Belum diisi'}</dd>
          </div>
        </dl>
      </section>
      <section className="tr-panel tr-stack" aria-labelledby="fakta-inovasi">
        <h2 id="fakta-inovasi" className="tr-sys-type-heading-sm">
          Saat ini dan direncanakan
        </h2>
        {[...current, ...planned].length ? (
          <ul className="tr-stack">
            {[...current, ...planned].map((fact, index) => (
              <li key={index}>
                {`${fact.label}: `}
                <FactSource value={`${fact.value} ${fact.unit ?? ''}`.trim()} timing={fact.timing} provenance={fact.provenance ?? undefined} />
              </li>
            ))}
          </ul>
        ) : (
          <p className="tr-muted">Belum ada fakta.</p>
        )}
      </section>
      <section className="tr-panel tr-stack" aria-labelledby="orang-hak">
        <h2 id="orang-hak" className="tr-sys-type-heading-sm">
          Orang dan hak
        </h2>
        {shown.claims.length ? (
          <ul className="tr-stack">
            {shown.claims.map((claim, index) => (
              <li key={index}>
                <strong>{claim.subject_name}</strong>
                {` · ${labelOf(CLAIM_KINDS, claim.kind)} · ${labelOf(CLAIM_STATUSES, claim.status) || 'Diperiksa'}`}
                {claim.scope ? <span className="tr-muted">{` · Cakupan: ${claim.scope}`}</span> : null}
                {claim.source ? <span className="tr-muted">{` · Sumber: ${claim.source}`}</span> : null}
              </li>
            ))}
          </ul>
        ) : (
          <p className="tr-muted">Belum ada klaim. Klaim bukan sertifikat kepemilikan.</p>
        )}
      </section>
      <section className="tr-panel tr-stack" aria-labelledby="dokumen-inovasi">
        <h2 id="dokumen-inovasi" className="tr-sys-type-heading-sm">
          Dokumen
        </h2>
        <p className="tr-muted">
          {owner ? 'Dokumen bukti privat. Kelola di langkah 2 editor.' : 'Dokumen dibagikan per pitching, hanya kepada penerima pitching tersebut.'}
        </p>
      </section>
      <section className="tr-panel tr-stack" aria-labelledby="dukungan-inovasi">
        <h2 id="dukungan-inovasi" className="tr-sys-type-heading-sm">
          Kebutuhan dukungan
        </h2>
        {owner ? (
          <p>
            <Link className="tr-link" href={`/support-requests?invention=${invention!.id}`}>
              Lihat kebutuhan dukungan dan pendanaan
            </Link>
          </p>
        ) : (
          <p className="tr-muted">Kebutuhan dukungan tampil bersama fitur Jelajahi.</p>
        )}
      </section>
    </Screen>
  );
}

import Link from 'next/link';

import type { Me } from '@/api/client';
import { EmptyState } from '@/components/tr/EmptyState';
import { FactSource } from '@/components/tr/FactSource';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import { TktBadge } from '@/components/tr/TktBadge';
import { ContextBar } from '@/features/ContextBar';
import { SaveButton } from '@/features/discovery/SaveButton';
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
import { InvestorDigestToggle } from '@/features/subscriptions/InvestorDigestToggle';
import { PublicPageForm } from '@/features/portfolio/PublicPageForm';
import { PublicUpdatesPanel, type PublicUpdate } from '@/features/portfolio/PublicUpdatesPanel';
import type { DocumentView } from '@/features/documents/model';
import { PROVENANCE } from '@/views/parts';
import { t } from '@/features/i18n/t';

/** S04 list: the acting party's inventions, drafts and archived ones included. */
export function InventionsView({ me, inventions }: { me: Me; inventions: InventionSummary[] }) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  return (
    <Screen
      persona={persona}
      current="inovasi"
      title="Inovasi Saya"
      subtitle={t('Profil inovasi yang Anda kelola. Draf hanya terlihat oleh Anda.')}
      provenance={PROVENANCE}
      context={<ContextBar me={me} />}>
      <p><Link className="tr-link" href="/inventions/import">{t('Impor dan ekspor data')}</Link></p>
      {inventions.length ? (
        <>
          <ul className="tr-stack">
            {inventions.map((invention) => (
              <li key={invention.id} className="tr-panel tr-stack">
                <h2 className="tr-sys-type-heading-sm">{invention.title || t('Inovasi tanpa judul')}</h2>
                <p className="tr-row">
                  <Status tone={invention.status === 'PUBLISHED' ? 'success' : 'neutral'} label={STATUS_LABEL[invention.status] ?? invention.status} />
                  {invention.published_number ? <span className="tr-muted">{t('Versi terbit {n}', { n: invention.published_number })}</span> : null}
                  {invention.published_number && invention.has_draft ? <span className="tr-tag tr-sys-type-support">{t('Ada draf perubahan')}</span> : null}
                </p>
                <p>
                  <Link className="tr-link" href={`/inventions/${invention.id}`}>
                    {t('Buka')}<span className="tr-sr">{` ${invention.title || t('inovasi tanpa judul')}`}</span>
                  </Link>
                </p>
              </li>
            ))}
          </ul>
          <NewInventionButton actingPartyId={me.active_party_id} />
        </>
      ) : (
        <EmptyState icon="bulb" title={t('Belum ada inovasi')} action={<NewInventionButton actingPartyId={me.active_party_id} />}>
          {t('Susun profil dalam empat langkah. Draf tersimpan walau belum lengkap, dan hanya versi yang Anda terbitkan yang terlihat oleh orang lain.')}
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
  /** Whether the acting party saved this invention; only read for someone else's invention. */
  saved?: boolean;
  /** The owner's documents, for the public photo choice. */
  documents?: DocumentView[];
  /** The owner's public updates (052). */
  updates?: PublicUpdate[];
};

/** S04 detail: honest about what exists now, what is planned, and who says so (UX-04). */
export function InventionView({ me, invention, publicView, justPublished, saved = false, documents = [], updates = [] }: DetailProps) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  const shown = invention ? (invention.published ?? invention.draft) : publicView;
  const owner = Boolean(invention);
  if (!shown) {
    return (
      <Screen persona={persona} title={t('Inovasi tidak ditemukan')} provenance={PROVENANCE} context={<ContextBar me={me} />}>
        <EmptyState icon="question" title={t('Inovasi ini tidak tersedia')} action={<Link className="tr-link" href="/inventions">{t('Kembali ke Inovasi Saya')}</Link>}>
          {t('Inovasi mungkin belum terbit, sudah diarsipkan, atau dikelola pihak lain.')}
        </EmptyState>
      </Screen>
    );
  }
  const current = shown.facts.filter((fact) => fact.timing === 'CURRENT');
  const planned = shown.facts.filter((fact) => fact.timing !== 'CURRENT');
  const action = owner ? (
    <Link className="tr-btn tr-btn--primary" href={`/inventions/${invention!.id}/edit?step=1`}>
      {invention!.draft && invention!.published ? t('Lanjutkan draf perubahan') : t('Ubah inovasi')}
    </Link>
  ) : (
    <SaveButton subjectType="INVENTION" subjectId={publicView!.id} title={shown.title} saved={saved} actingPartyId={me.active_party_id} label={t('Simpan inovasi')} intent="primary" />
  );
  return (
    <Screen
      persona={persona}
      current={owner ? 'inovasi' : undefined}
      title={shown.title || t('Inovasi tanpa judul')}
      subtitle={owner ? undefined : t('Dikelola {name}', { name: publicView!.managing_party_name })}
      back={
        <Link className="tr-link" href={owner ? '/inventions' : '/discover'}>
          {t('Kembali')}
        </Link>
      }
      provenance={PROVENANCE}
      context={<ContextBar me={me} />}>
      {justPublished ? <Status tone="success" label={t('Versi {n} sudah terbit', { n: justPublished })} live /> : null}
      {owner && !invention!.published ? <Status tone="neutral" label={t('Draf, belum terbit')} /> : null}
      {owner && invention!.status === 'ARCHIVED' ? <Status tone="warning" label="Diarsipkan" /> : null}
      <div className="tr-row">
        {action}
        {/* Scenario 5 of the demo: an investor inviting an inventor to pitch is announced, not built yet. */}
        {!owner && persona === 'mitra' ? <Status tone="neutral" label={t('Ajak pitching · segera hadir')} /> : null}
      </div>
      {owner && invention!.published && invention!.status !== 'ARCHIVED' ? (
        <>
          <PublicPageForm inventionId={invention!.id} actingPartyId={me.active_party_id} version={invention!.version} page={invention!.public_page ?? {}} documents={documents} />
          <PublicUpdatesPanel inventionId={invention!.id} actingPartyId={me.active_party_id} updates={updates} pageOn={Boolean(invention!.public_page?.enabled)} />
          <InvestorDigestToggle inventionId={invention!.id} actingPartyId={me.active_party_id} version={invention!.version} enabled={Boolean(invention!.investor_digest)} />
        </>
      ) : null}
      <section className="tr-panel tr-stack" aria-labelledby="ringkasan-inovasi">
        <h2 id="ringkasan-inovasi" className="tr-sys-type-heading-sm">
          {t('Ringkasan')}
        </h2>
        {shown.readiness ? (
          <TktBadge
            level={shown.readiness.tkt_level}
            stageLabel={labelOf(STAGES, shown.stage)}
            note={shown.readiness.note}
            hasEvidence={shown.readiness.has_evidence}
            showBar
            showMeta
          />
        ) : null}
        {shown.summary ? <p>{shown.summary}</p> : null}
        <dl className="tr-facts">
          <div>
            <dt className="tr-sys-type-support-strong">{t('Masalah')}</dt>
            <dd>{shown.problem || t('Belum diisi')}</dd>
          </div>
          <div>
            <dt className="tr-sys-type-support-strong">{t('Solusi saat ini')}</dt>
            <dd>{shown.solution || t('Belum diisi')}</dd>
          </div>
          <div>
            <dt className="tr-sys-type-support-strong">{t('Tahap')}</dt>
            <dd>{labelOf(STAGES, shown.stage) || t('Belum diisi')}</dd>
          </div>
          <div>
            <dt className="tr-sys-type-support-strong">{t('Pengguna')}</dt>
            <dd>{shown.intended_users || t('Belum diisi')}</dd>
          </div>
        </dl>
      </section>
      <section className="tr-panel tr-stack" aria-labelledby="fakta-inovasi">
        <h2 id="fakta-inovasi" className="tr-sys-type-heading-sm">
          {t('Saat ini dan direncanakan')}
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
          <p className="tr-muted">{t('Belum ada fakta.')}</p>
        )}
      </section>
      <section className="tr-panel tr-stack" aria-labelledby="orang-hak">
        <h2 id="orang-hak" className="tr-sys-type-heading-sm">
          {t('Orang dan hak')}
        </h2>
        {shown.claims.length ? (
          <ul className="tr-stack">
            {shown.claims.map((claim, index) => (
              <li key={index}>
                <strong>{claim.subject_name}</strong>
                {` · ${labelOf(CLAIM_KINDS, claim.kind)} · ${labelOf(CLAIM_STATUSES, claim.status) || t('Diperiksa')}`}
                {claim.scope ? <span className="tr-muted">{` · ${t('Cakupan')}: ${claim.scope}`}</span> : null}
                {claim.source ? <span className="tr-muted">{` · ${t('Sumber')}: ${claim.source}`}</span> : null}
              </li>
            ))}
          </ul>
        ) : (
          <p className="tr-muted">{t('Belum ada klaim. Klaim bukan sertifikat kepemilikan.')}</p>
        )}
      </section>
      <section className="tr-panel tr-stack" aria-labelledby="dokumen-inovasi">
        <h2 id="dokumen-inovasi" className="tr-sys-type-heading-sm">
          {t('Dokumen')}
        </h2>
        <p className="tr-muted">
          {owner ? t('Dokumen bukti privat. Kelola di langkah 2 editor.') : t('Dokumen dibagikan per pitching, hanya kepada penerima pitching tersebut.')}
        </p>
      </section>
      <section className="tr-panel tr-stack" aria-labelledby="dukungan-inovasi">
        <h2 id="dukungan-inovasi" className="tr-sys-type-heading-sm">
          {t('Kebutuhan dukungan')}
        </h2>
        {owner ? (
          <p>
            <Link className="tr-link" href={`/support-requests?invention=${invention!.id}`}>
              {t('Lihat kebutuhan dukungan dan pendanaan')}
            </Link>
          </p>
        ) : (
          <p className="tr-muted">{t('Kebutuhan dukungan tampil bersama fitur Jelajahi.')}</p>
        )}
      </section>
    </Screen>
  );
}

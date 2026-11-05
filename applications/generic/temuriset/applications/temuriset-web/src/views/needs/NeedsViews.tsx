import Link from 'next/link';
import type { ReactNode } from 'react';

import type { Me } from '@/api/client';
import { EmptyState } from '@/components/tr/EmptyState';
import { FinancialScope } from '@/components/tr/FinancialScope';
import { FundingRequestCard } from '@/components/tr/FundingRequestCard';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import { ContextBar } from '@/features/ContextBar';
import { FundingForm } from '@/features/needs/FundingForm';
import { FINANCING_FORMS, FINANCING_STAGES, NEED_STATUS, SUPPORT_FORMS, type FundingRequest, type LegalEntity, type SupportRequest } from '@/features/needs/model';
import { NewFundingRequest, NewSupportRequest } from '@/features/needs/StartButtons';
import { SupportForm } from '@/features/needs/SupportForm';
import { readPersona } from '@/features/persona';
import { labelOf } from '@/features/portfolio/model';
import { PROVENANCE } from '@/views/parts';

type Published = { id: string; title: string };

export const FUNDING_OFF = 'Pendanaan Perusahaan tidak tersedia di layanan ini. Riwayat yang sudah ada tetap dapat dibaca, tetapi tidak dapat diubah.';

function OffNotice() {
  return (
    <Status tone="neutral" icon="lock" label="Pendanaan Perusahaan tidak aktif">
      <p>{FUNDING_OFF}</p>
    </Status>
  );
}

function SupportBudget({ request, compact }: { request: SupportRequest; compact?: boolean }) {
  const budget = request.budget;
  return (
    <FinancialScope
      compact={compact}
      subject="project"
      currency={budget?.currency}
      min={budget?.min}
      max={budget?.max}
      period={budget?.period || undefined}
      scope={budget?.scope || undefined}
      estimateDate={compact ? undefined : budget?.estimated_on}
      assumptions={compact ? undefined : budget?.assumptions || undefined}
      noncash={budget && !budget.financial ? 'Tanpa dana tunai' : undefined}
    />
  );
}

function FundingCard({ request, linkInventions, action }: { request: FundingRequest; linkInventions?: boolean; action?: ReactNode }) {
  return (
    <FundingRequestCard
      headingLevel={linkInventions ? 2 : 3}
      company={request.subject_type === 'PROPOSED_ENTITY' ? request.proposed_name || 'Perusahaan baru' : request.subject_label}
      proposedEntity={request.subject_type === 'PROPOSED_ENTITY'}
      stage={labelOf(FINANCING_STAGES, request.financing_stage)}
      form={labelOf(FINANCING_FORMS, request.financing_form)}
      purpose={request.intended_use || undefined}
      currency={request.currency}
      target={request.target_amount}
      desiredMin={request.desired_min}
      desiredMax={request.desired_max}
      partialAccepted={request.accepts_partial}
      inventions={request.inventions.map((invention) =>
        linkInventions ? (
          <Link key={invention.invention_id} className="tr-link" href={`/inventions/${invention.invention_id}`}>
            {`${invention.title}, versi ${invention.version}`}
          </Link>
        ) : (
          `${invention.title}, versi ${invention.version}`
        ),
      )}
      action={action}
    />
  );
}

type ListProps = {
  me: Me;
  support: SupportRequest[];
  funding: FundingRequest[];
  published: Published[];
  fundingOn: boolean;
  /** Preselects the invention to start a need for, from the editor's step 3. */
  invention?: string;
};

/** S06 list: the acting party's support requests and company raises. */
export function NeedsView({ me, support, funding, published, fundingOn, invention }: ListProps) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  return (
    <Screen
      persona={persona}
      current="inovasi"
      title="Kebutuhan dan pendanaan"
      subtitle="Dukungan proyek per inovasi, dan pendanaan perusahaan yang dapat didukung beberapa inovasi."
      provenance={PROVENANCE}
      context={<ContextBar me={me} />}>
      <section className="tr-stack" aria-labelledby="dukungan-proyek">
        <h2 id="dukungan-proyek" className="tr-sys-type-heading-sm">
          Dukungan Proyek
        </h2>
        {support.length ? (
          <ul className="tr-stack">
            {support.map((request) => (
              <li key={request.id} className="tr-panel tr-stack">
                <h3 className="tr-sys-type-label">{request.outcome || 'Kebutuhan tanpa judul'}</h3>
                <p className="tr-row">
                  <Status tone={request.status === 'ACTIVE' ? 'success' : 'neutral'} label={NEED_STATUS[request.status] ?? request.status} />
                  <span className="tr-muted">{`${request.invention_title}, versi ${request.invention_version}`}</span>
                </p>
                <SupportBudget request={request} compact />
                <p>
                  <Link className="tr-link" href={`/support-requests/${request.id}`}>
                    Buka<span className="tr-sr">{` ${request.outcome || 'kebutuhan tanpa judul'}`}</span>
                  </Link>
                </p>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState icon="bulb" title="Belum ada kebutuhan dukungan">
            Nyatakan hasil yang ingin dicapai, bentuk dukungan, dan kisaran biaya untuk satu inovasi yang sudah terbit.
          </EmptyState>
        )}
        <NewSupportRequest actingPartyId={me.active_party_id} inventions={published} initial={invention} />
      </section>
      <section id="pendanaan" className="tr-stack" aria-labelledby="pendanaan-perusahaan">
        <h2 id="pendanaan-perusahaan" className="tr-sys-type-heading-sm">
          Pendanaan Perusahaan
        </h2>
        {fundingOn ? null : <OffNotice />}
        {funding.length ? (
          <ul className="tr-stack">
            {funding.map((request) => (
              <li key={request.id}>
                <FundingCard
                  request={request}
                  action={
                    <Link className="tr-link" href={`/funding-requests/${request.id}`}>
                      Buka<span className="tr-sr">{` pendanaan ${request.subject_label}`}</span>
                    </Link>
                  }
                />
              </li>
            ))}
          </ul>
        ) : fundingOn ? (
          <p className="tr-muted">Belum ada pendanaan perusahaan. Satu putaran dapat ditautkan ke beberapa inovasi.</p>
        ) : null}
        {fundingOn ? <NewFundingRequest actingPartyId={me.active_party_id} /> : null}
      </section>
    </Screen>
  );
}

/** S06 detail: what the need is for, its labelled money, and the form. */
export function SupportView({ me, request, returnTo }: { me: Me; request: SupportRequest; returnTo?: string | null }) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  const forms = request.support_forms.map((form) => labelOf([...SUPPORT_FORMS], form)).join(', ');
  return (
    <Screen
      persona={persona}
      current="inovasi"
      title={request.outcome || 'Kebutuhan dukungan'}
      subtitle={`Untuk ${request.invention_title}, versi ${request.invention_version}`}
      back={
        <Link className="tr-link" href={returnTo ?? '/support-requests'}>
          Kembali
        </Link>
      }
      provenance={PROVENANCE}
      context={<ContextBar me={me} />}>
      <section className="tr-panel tr-stack" aria-labelledby="ringkasan-kebutuhan">
        <h2 id="ringkasan-kebutuhan" className="tr-sys-type-heading-sm">
          Ringkasan
        </h2>
        <p className="tr-row">
          <Status tone={request.status === 'ACTIVE' ? 'success' : 'neutral'} label={NEED_STATUS[request.status] ?? request.status} />
          <span className="tr-muted">{`Versi ${request.version}`}</span>
        </p>
        {forms ? <p>{`Bentuk dukungan: ${forms}`}</p> : null}
        <SupportBudget request={request} />
      </section>
      <SupportForm key={request.version} request={request} actingPartyId={me.active_party_id} returnTo={returnTo} />
    </Screen>
  );
}

/** S07 detail: one raise card, with links to each invention that supports it. */
export function FundingView({ me, request, fundingOn }: { me: Me; request: FundingRequest; fundingOn: boolean }) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  return (
    <Screen
      persona={persona}
      current="inovasi"
      title="Pendanaan Perusahaan"
      subtitle={`Versi ${request.version} · ${NEED_STATUS[request.status] ?? request.status}`}
      back={
        <Link className="tr-link" href="/support-requests#pendanaan">
          Kembali
        </Link>
      }
      provenance={PROVENANCE}
      context={<ContextBar me={me} />}>
      {fundingOn ? null : <OffNotice />}
      <FundingCard
        request={request}
        linkInventions
        action={
          fundingOn ? (
            <Link className="tr-btn tr-btn--primary" href={`/funding-requests/${request.id}/edit`}>
              Ubah pendanaan
            </Link>
          ) : undefined
        }
      />
      {request.legal_entity ? (
        <p className="tr-muted">{`${request.legal_entity.name}: dinyatakan sendiri, belum diperiksa.`}</p>
      ) : null}
    </Screen>
  );
}

type EditProps = { me: Me; request: FundingRequest; entities: LegalEntity[]; published: Published[]; fundingOn: boolean };

/** S07 editor, or the notice when this deployment does not run company funding. */
export function FundingEditView({ me, request, entities, published, fundingOn }: EditProps) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  return (
    <Screen
      persona={persona}
      current="inovasi"
      title="Ubah pendanaan perusahaan"
      back={
        <Link className="tr-link" href={`/funding-requests/${request.id}`}>
          Kembali
        </Link>
      }
      provenance={PROVENANCE}
      context={<ContextBar me={me} />}>
      {fundingOn ? (
        <FundingForm key={request.version} request={request} entities={entities} inventions={published} actingPartyId={me.active_party_id} />
      ) : (
        <>
          <OffNotice />
          <FundingCard request={request} />
        </>
      )}
    </Screen>
  );
}

import { Disclosure } from '@/components/tr/Disclosure';
import { FinancialScope } from '@/components/tr/FinancialScope';
import { RequirementRow } from '@/components/tr/RequirementRow';
import { Status } from '@/components/tr/Status';
import { MandateActions } from '@/features/intake/MandateActions';
import { AVAILABILITY_REASON, MANDATE_STATUS, scopeProps, type Mandate } from '@/features/intake/model';

export const MANUAL_REVIEW_TAG = <span className="tr-tag tr-sys-type-support">Ditinjau manual</span>;

type Props = {
  mandate: Mandate;
  /** The acting party when it may change this mandate. */
  editingAs?: string | null;
};

/** One mandate: status, version, what it offers, and its requirements with no pass or fail implied. */
export function MandateCard({ mandate, editingAs }: Props) {
  const title = mandate.title || 'Mandat tanpa judul';
  const headingId = `mandat-${mandate.id}`;
  const reason = mandate.target_availability.reason;
  const support = [mandate.support, mandate.timing]
    .filter(Boolean)
    .map((part) => `${part}.`)
    .join(' ');
  return (
    <article className="tr-panel tr-stack" aria-labelledby={headingId}>
      <h3 id={headingId} className="tr-sys-type-label">
        {title}
      </h3>
      <p className="tr-row">
        <Status tone={mandate.status === 'ACTIVE' ? 'success' : 'neutral'} label={MANDATE_STATUS[mandate.status] ?? mandate.status} />
        <span className="tr-muted">{`Versi ${mandate.number}`}</span>
        {mandate.general_intake_label ? <span className="tr-tag tr-sys-type-support">{mandate.general_intake_label}</span> : null}
      </p>
      {mandate.outcome ? <p>{mandate.outcome}</p> : null}
      {support ? <p className="tr-muted">{`Dukungan: ${support}`}</p> : null}
      {mandate.financial ? <FinancialScope compact {...scopeProps(mandate.financial)} /> : null}
      {reason ? <p className="tr-muted">{AVAILABILITY_REASON[reason]}</p> : null}
      {mandate.requirements.length ? (
        <Disclosure label="Syarat mandat ini">
          <ul>
            {mandate.requirements.map((row) => (
              <RequirementRow
                key={row.id}
                label={row.label}
                result="NOT_APPLICABLE"
                stage={row.applies_at}
                mandatory={row.mandatory}
                mode={row.verification_mode}
                reason={row.reason}
                action={row.operator === 'manual_review' ? MANUAL_REVIEW_TAG : undefined}
              />
            ))}
          </ul>
        </Disclosure>
      ) : null}
      {editingAs ? <MandateActions mandate={mandate} actingPartyId={editingAs} /> : null}
    </article>
  );
}

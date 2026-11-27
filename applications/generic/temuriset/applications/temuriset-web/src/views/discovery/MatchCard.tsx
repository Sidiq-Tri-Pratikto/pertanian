import NextLink from 'next/link';

import { Disclosure } from '@/components/tr/Disclosure';
import { RequirementRow } from '@/components/tr/RequirementRow';
import { Status, type Tone } from '@/components/tr/Status';
import { ELIGIBILITY, matchesHref, percent, READINESS, score, type MatchResult, type MatchSourceRef } from '@/features/discovery/model';
import { AVAILABILITY_REASON } from '@/features/intake/model';

/** The label's tone comes from the enums, never from its words. Green belongs to real requirement results only. */
export function labelTone(result: MatchResult): Tone {
  if (result.eligibility === 'INCOMPATIBLE' || result.readiness === 'BLOCKED_FOR_THIS_TARGET') return 'danger';
  if (result.eligibility === 'NEEDS_VERIFICATION' || result.readiness === 'NEEDS_INFORMATION') return 'warning';
  return 'neutral';
}

function primaryAction(result: MatchResult, source: MatchSourceRef) {
  const back = encodeURIComponent(matchesHref(source));
  const gap = result.gap;
  if (gap?.action === 'complete-budget' && source.type === 'SUPPORT_REQUEST') {
    return { href: `/support-requests/${source.id}?return=${back}`, label: 'Lengkapi kisaran biaya' };
  }
  if (gap?.action === 'complete-contribution' && source.type === 'FUNDING_REQUEST') {
    return { href: `/funding-requests/${source.id}/edit?return=${back}`, label: 'Lengkapi kisaran kontribusi' };
  }
  if (result.readiness === 'READY_TO_SUBMIT' && result.availability.available) {
    return { href: `/pitches/new?source=${source.type}:${source.id}&target=${result.opportunity_id}`, label: 'Siapkan pitching' };
  }
  // The partner's profile lists its mandates; there is no page per mandate for the sender.
  return { href: `/partners/${result.partner_party_id}`, label: 'Lihat mandat' };
}

type Props = { result: MatchResult; source: MatchSourceRef };

/**
 * S10, action first: who and which mandate, whether it takes pitches, the one requirement that decides, and one
 * action. Why it matches (reasons, eligibility, readiness, score range, evidence) and every requirement row wait on
 * request; a blocking requirement never hides there (UX-07).
 */
export function MatchCard({ result, source }: Props) {
  const action = primaryAction(result, source);
  const headingId = `kecocokan-${result.opportunity_id}`;
  const intake = result.availability.available ? 'Menerima pitching' : result.availability.reason ? AVAILABILITY_REASON[result.availability.reason] : 'Belum menerima pitching';
  const deciding = result.gap ? `${result.gap.result === 'FAIL' ? 'Menghalangi' : 'Perlu dilengkapi'}: ${result.gap.reason}` : 'Tidak ada syarat wajib yang menghalangi';
  return (
    <article className="tr-card" aria-labelledby={headingId}>
      <div className="tr-card__body tr-stack">
        <p className="tr-muted tr-sys-type-support">{result.partner}</p>
        <h3 id={headingId} className="tr-sys-type-heading-sm">
          {result.title}
        </h3>
        <p>
          <Status tone={labelTone(result)} icon={null} label={result.label} />
        </p>
        <dl className="tr-facts">
          <div>
            <dt className="tr-sys-type-support-strong">Penerimaan</dt>
            <dd>{intake}</dd>
          </div>
          <div>
            <dt className="tr-sys-type-support-strong">Syarat penentu</dt>
            <dd>{deciding}</dd>
          </div>
        </dl>
        <div className="tr-row">
          <NextLink className="tr-btn tr-btn--primary" href={action.href}>
            {action.label}
          </NextLink>
        </div>
        <Disclosure label="Mengapa cocok?">
          {result.reasons.length ? (
            <ul className="tr-reasons">
              {result.reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          ) : null}
          <dl className="tr-facts">
            <div>
              <dt className="tr-sys-type-support-strong">Kelayakan</dt>
              <dd>{ELIGIBILITY[result.eligibility]}</dd>
            </div>
            <div>
              <dt className="tr-sys-type-support-strong">Kesiapan</dt>
              <dd>{READINESS[result.readiness]}</dd>
            </div>
            <div>
              <dt className="tr-sys-type-support-strong">Kisaran kecocokan</dt>
              <dd>{`${score(result.fit.lower, 'lower')}–${score(result.fit.upper, 'upper')} dari 100 · informasi ${percent(result.fit.coverage)}`}</dd>
            </div>
          </dl>
          <p>Kisaran ini mencerminkan informasi yang belum lengkap, bukan peluang pendanaan. Semakin lengkap informasinya, semakin sempit kisarannya.</p>
          <p>{`Bukti: ${result.evidence.provided} tersedia, ${result.evidence.reviewed} sudah diperiksa, dari ${result.evidence.applicable} syarat.`}</p>
        </Disclosure>
        <Disclosure label="Rincian syarat">
          {result.evidence.note ? <p>{result.evidence.note}</p> : null}
          <ul className="tr-stack">
            {result.rows.map((row) => (
              <RequirementRow key={row.requirement_id} label={row.label} result={row.result} stage={row.applies_at} mandatory={row.mandatory} mode={row.verification_mode} reason={row.reason} />
            ))}
          </ul>
        </Disclosure>
      </div>
    </article>
  );
}

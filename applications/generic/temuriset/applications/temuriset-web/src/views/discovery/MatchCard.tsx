import NextLink from 'next/link';

import { Disclosure } from '@/components/tr/Disclosure';
import { RequirementRow } from '@/components/tr/RequirementRow';
import { Status, type Tone } from '@/components/tr/Status';
import { ELIGIBILITY, matchesHref, percent, READINESS, score, type MatchResult, type MatchSourceRef } from '@/features/discovery/model';
import { AVAILABILITY_REASON } from '@/features/intake/model';

/** Computed labels never use the success colour; green belongs to real requirement results only. */
const LABEL_TONE: Record<string, Tone> = {
  'Tidak cocok untuk target ini': 'danger',
  'Perlu konfirmasi': 'warning',
  'Informasi belum cukup': 'warning',
};

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
    return { href: '/segera-hadir/pemeriksaan-pitching', label: 'Siapkan pitching' };
  }
  return { href: `/opportunities/${result.opportunity_id}`, label: 'Lihat mandat' };
}

type Props = { result: MatchResult; source: MatchSourceRef };

/** S10: label, up to three reasons, the blocking gap, one action; rows and the score note on request (UX-07). */
export function MatchCard({ result, source }: Props) {
  const action = primaryAction(result, source);
  const headingId = `kecocokan-${result.opportunity_id}`;
  return (
    <article className="tr-card" aria-labelledby={headingId}>
      <div className="tr-card__body tr-stack">
        <p className="tr-muted tr-sys-type-support">{result.partner}</p>
        <h3 id={headingId} className="tr-sys-type-heading-sm">
          {result.title}
        </h3>
        <p>
          <Status tone={LABEL_TONE[result.label] ?? 'neutral'} icon={null} label={result.label} />
        </p>
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
            <dd>{`${score(result.fit.lower)}–${score(result.fit.upper)} · informasi ${percent(result.fit.coverage)}`}</dd>
          </div>
        </dl>
        {result.reasons.length ? (
          <ul className="tr-reasons">
            {result.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        ) : null}
        {result.gap ? <p>{`${result.gap.result === 'FAIL' ? 'Menghalangi' : 'Perlu dilengkapi'}: ${result.gap.reason}`}</p> : null}
        {!result.availability.available && result.availability.reason ? <p className="tr-muted">{AVAILABILITY_REASON[result.availability.reason]}</p> : null}
        <div className="tr-row">
          <NextLink className="tr-btn tr-btn--primary" href={action.href}>
            {action.label}
          </NextLink>
        </div>
        <Disclosure label="Rincian syarat">
          {result.evidence.note ? <p>{result.evidence.note}</p> : null}
          <ul className="tr-stack">
            {result.rows.map((row) => (
              <RequirementRow key={row.requirement_id} label={row.label} result={row.result} stage={row.applies_at} mandatory={row.mandatory} mode={row.verification_mode} reason={row.reason} />
            ))}
          </ul>
        </Disclosure>
        <Disclosure label="Tentang kisaran kecocokan">
          <p>Kisaran ini mencerminkan informasi yang belum lengkap, bukan peluang pendanaan. Semakin lengkap informasinya, semakin sempit kisarannya.</p>
          <p>{`Bukti: ${result.evidence.provided} tersedia, ${result.evidence.reviewed} sudah diperiksa, dari ${result.evidence.applicable} syarat.`}</p>
        </Disclosure>
      </div>
    </article>
  );
}

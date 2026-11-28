import NextLink from 'next/link';

import { Status, type Tone } from '@/components/tr/Status';
import { finderHref, type PartnerBestFit } from '@/features/discovery/fit';
import { score, type DiscoveryItem, type Filters } from '@/features/discovery/model';
import { t } from '@/features/i18n/t';

type Props = {
  item: DiscoveryItem;
  active: boolean;
  filters: Filters;
  selectedProduct?: string;
};

function fitTone(fit: PartnerBestFit): Tone {
  if (fit.eligibility === 'INCOMPATIBLE') return 'danger';
  if (fit.eligibility === 'NEEDS_VERIFICATION') return 'warning';
  if (fit.label === 'Kecocokan kuat') return 'success';
  return 'neutral';
}

function barFillClass(fit: PartnerBestFit): string {
  if (fit.eligibility === 'INCOMPATIBLE') return 'tr-meter__fill tr-meter__fill--mismatch';
  const lower = Number(fit.fit.lower);
  if (lower >= 70) return 'tr-meter__fill tr-meter__fill--match';
  if (lower >= 40) return 'tr-meter__fill tr-meter__fill--partial';
  return 'tr-meter__fill tr-meter__fill--mismatch';
}

/** One investor row in the finder list, showing best fit label, score bar, and product summary (spec 059). */
export function InvestorRow({ item, active, filters, selectedProduct }: Props) {
  const card = item.card as Record<string, unknown>;
  const bestFit = (item as DiscoveryItem & { best_fit?: PartnerBestFit | null }).best_fit ?? null;
  const subtype = typeof card.subtype === 'string' && card.subtype ? card.subtype : undefined;
  const availability = typeof card.availability_label === 'string' && card.availability_label ? t(card.availability_label) : undefined;
  const lower = bestFit ? Math.min(100, Math.max(0, Number(score(bestFit.fit.lower, 'lower')))) : 0;

  return (
    <li
      id={`hasil-${item.subject_id}`}
      tabIndex={-1}
      className="tr-listrow"
      aria-current={active ? 'true' : undefined}>
      <div className="tr-stack">
        <NextLink
          className="tr-link tr-sys-type-body-strong"
          href={`${finderHref(filters, selectedProduct, item.subject_id)}#detail`}>
          {item.title}
        </NextLink>
        <span className="tr-muted tr-sys-type-support">
          {[subtype, availability].filter(Boolean).join(' · ')}
          {item.saved ? t(' · Disimpan') : ''}
        </span>
        {bestFit ? (
          <div className="tr-stack">
            <div className="tr-row">
              <Status tone={fitTone(bestFit)} icon={null} label={t(bestFit.label)} />
              <span className="tr-muted tr-sys-type-support">
                {`${score(bestFit.fit.lower, 'lower')}–${score(bestFit.fit.upper, 'upper')}`}
              </span>
            </div>
            <div className="tr-meter" aria-hidden="true">
              <div className={barFillClass(bestFit)} style={{ width: `${lower}%` }} />
            </div>
            {!selectedProduct ? (
              <span className="tr-muted tr-sys-type-support">
                {bestFit.matching_products
                  ? `${t('Terbaik: {product}', { product: bestFit.invention_title })} · ${t('{n} produk cocok', { n: bestFit.matching_products })}`
                  : t('Terbaik: {product}', { product: bestFit.invention_title })}
              </span>
            ) : null}
          </div>
        ) : null}
      </div>
    </li>
  );
}

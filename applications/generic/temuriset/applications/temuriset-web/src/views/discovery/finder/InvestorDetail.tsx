'use client';

import NextLink from 'next/link';
import { useCallback, useEffect, useState } from 'react';

import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { FinancialScope } from '@/components/tr/FinancialScope';
import { Status } from '@/components/tr/Status';
import { fetchPartnerFit, type FitItem, type MyProduct } from '@/features/discovery/fit';
import { ItemActions } from '@/features/discovery/ItemActions';
import type { DiscoveryItem } from '@/features/discovery/model';
import { t } from '@/features/i18n/t';
import { scopeProps, type StoredRange } from '@/features/intake/model';
import { FitTable } from '@/views/discovery/finder/FitTable';

type Props = {
  item: DiscoveryItem;
  actingPartyId: string;
  products: MyProduct[];
  returnTo: string;
  initialFit?: FitItem[] | null;
};

function str(card: Record<string, unknown>, key: string): string | undefined {
  const value = card[key];
  return typeof value === 'string' && value ? value : undefined;
}

/** Right-hand investor detail pane: mandate summary + live product × mandate FitTable (spec 059). */
export function InvestorDetail({ item, actingPartyId, products, returnTo, initialFit = null }: Props) {
  const card = item.card as Record<string, unknown>;
  const opportunities = (card.opportunities as { id: string; title: string }[]) ?? [];
  const check = card.check_range as StoredRange | null;
  const hasProducts = products.length > 0;
  const hasMandates = opportunities.length > 0;

  const [fitItems, setFitItems] = useState<FitItem[] | null>(initialFit);
  const [loading, setLoading] = useState(initialFit === null && hasProducts && hasMandates);
  const [failure, setFailure] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!hasProducts || !hasMandates) return;
    setLoading(true);
    setFailure(null);
    try {
      setFitItems(await fetchPartnerFit(item.subject_id, actingPartyId));
    } catch (error) {
      setFailure(error instanceof ApiError ? error.message : t('Kecocokan produk belum dapat dimuat.'));
    } finally {
      setLoading(false);
    }
  }, [actingPartyId, hasMandates, hasProducts, item.subject_id]);

  useEffect(() => {
    if (initialFit !== null || !hasProducts || !hasMandates) return;
    let cancelled = false;
    void fetchPartnerFit(item.subject_id, actingPartyId)
      .then((items) => {
        if (!cancelled) {
          setFitItems(items);
          setFailure(null);
          setLoading(false);
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setFailure(error instanceof ApiError ? error.message : t('Kecocokan produk belum dapat dimuat.'));
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [actingPartyId, hasMandates, hasProducts, initialFit, item.subject_id]);

  return (
    <article className="tr-card">
      <div className="tr-card__body tr-stack">
        <h3 className="tr-sys-type-heading-sm">{item.title}</h3>
        {str(card, 'subtype') ? <p className="tr-muted tr-sys-type-support">{str(card, 'subtype')}</p> : null}
        <p className="tr-row">
          <Status tone="neutral" label={t(str(card, 'availability_label') ?? '')} />
          <span className="tr-tag tr-sys-type-support">{t(str(card, 'source_label') ?? '')}</span>
        </p>
        {str(card, 'thesis') ? <p>{str(card, 'thesis')}</p> : null}
        {check ? <FinancialScope {...scopeProps(check)} /> : null}
        {opportunities.length ? (
          <p>{t('Mandat aktif: {list}', { list: opportunities.map((opp) => opp.title).join('; ') })}</p>
        ) : null}
        <div className="tr-row">
          <NextLink className="tr-btn tr-btn--secondary" href={`/partners/${item.subject_id}`}>
            {t('Lihat profil mitra')}
          </NextLink>
          <ItemActions
            subjectType={item.subject_type}
            subjectId={item.subject_id}
            title={item.title}
            saved={item.saved}
            actingPartyId={actingPartyId}
          />
        </div>
        {!hasMandates ? (
          <Status tone="neutral" label={t('Investor ini belum membuka mandat. Simpan atau ikuti untuk kabar berikutnya.')} />
        ) : !hasProducts ? (
          <Status tone="neutral" label={t('Terbitkan inovasi terlebih dahulu untuk melihat kecocokan produk Anda.')} />
        ) : loading ? (
          <Status tone="neutral" label={t('Memuat kecocokan produk Anda…')} live />
        ) : failure ? (
          <Status tone="danger" label={t('Kecocokan produk belum dapat dimuat.')} live="alert">
            <p>{failure}</p>
            <Button onClick={() => void load()}>{t('Coba lagi')}</Button>
          </Status>
        ) : fitItems && fitItems.length ? (
          <FitTable items={fitItems} returnTo={returnTo} />
        ) : (
          <Status tone="neutral" label={t('Investor ini belum membuka mandat. Simpan atau ikuti untuk kabar berikutnya.')} />
        )}
      </div>
    </article>
  );
}

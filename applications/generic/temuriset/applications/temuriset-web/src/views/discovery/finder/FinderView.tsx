import NextLink from 'next/link';

import type { Me } from '@/api/client';
import { EmptyState } from '@/components/tr/EmptyState';
import { Icon } from '@/components/tr/Icon';
import { Screen } from '@/components/tr/Screen';
import { ContextBar } from '@/features/ContextBar';
import { finderHref, type FitItem, type MyProduct } from '@/features/discovery/fit';
import { FocusFromHash } from '@/features/discovery/FocusFromHash';
import {
  appliedFilters,
  discoverHref,
  FILTER_LABELS,
  filterCount,
  resultCount,
  RESULT_TYPES,
  SECTORS,
  type Discovery,
  type Filters,
} from '@/features/discovery/model';
import { t } from '@/features/i18n/t';
import { labelOf, STAGES } from '@/features/portfolio/model';
import { InvestorDetail } from '@/views/discovery/finder/InvestorDetail';
import { InvestorRow } from '@/views/discovery/finder/InvestorRow';
import { ProductPicker } from '@/views/discovery/finder/ProductPicker';
import { PROVENANCE } from '@/views/parts';

type Props = {
  me: Me;
  filters: Filters;
  page: Discovery;
  fundingOn: boolean;
  matchesHref: string | null;
  selected?: string;
  products: MyProduct[];
  selectedProduct?: string;
  initialFit?: FitItem[] | null;
};

/** Rebuilt inventor finder: product selector + fit-ranked investor list beside product × mandate detail (spec 059). */
export function FinderView({
  me,
  filters,
  page,
  fundingOn,
  matchesHref,
  selected,
  products,
  selectedProduct,
  initialFit = null,
}: Props) {
  const items = page.sections.flatMap((section) => section.items);
  const applied = appliedFilters(page.filters, (value) => labelOf(STAGES, value));
  const types = RESULT_TYPES.filter((item) => !item.capability || fundingOn);
  const chosen = items.find((item) => item.subject_id === selected);
  const open = chosen ?? items[0];
  const narrowing = filterCount(filters);
  const without = (name: string): Filters =>
    Object.fromEntries(applied.filter((filter) => filter.name !== name).map((filter) => [filter.name, filter.value])) as Filters;
  const currentUrl = finderHref(filters, selectedProduct, open?.subject_id);

  return (
    <Screen
      persona="inovator"
      current="temukan"
      title="Temukan Investor/Mitra"
      subtitle={t('Hasil disusun menurut kecocokan produk Anda, bukan menurut popularitas.')}
      provenance={PROVENANCE}
      context={<ContextBar me={me} />}>
      <nav aria-label={t('Jenis hasil')} className="tr-row">
        {types.map((item) => (
          <NextLink
            key={item.value}
            className={`tr-btn ${item.value === 'partners' ? 'tr-btn--primary' : 'tr-btn--secondary'}`}
            aria-current={item.value === 'partners' ? 'page' : undefined}
            href={item.value === 'partners' ? finderHref(filters, selectedProduct) : discoverHref(item.value, filters)}>
            {t(item.label)}
          </NextLink>
        ))}
      </nav>
      {matchesHref ? (
        <p>
          <NextLink className="tr-link" href={matchesHref}>
            {t('Lihat kecocokan untuk kebutuhan Anda')}
          </NextLink>
        </p>
      ) : null}
      <form method="get" action="/discover" className="tr-panel tr-stack" role="search" aria-label={t('Cari dan saring')}>
        <input type="hidden" name="type" value="partners" />
        <div className="tr-toolbar">
          <ProductPicker
            products={products}
            selectedProduct={selectedProduct}
            filters={filters}
            selectedPartner={selected}
          />
          <div className="tr-field">
            <label htmlFor="filter-q" className="tr-sys-type-label">
              {t('Kata kunci')}
            </label>
            <p id="filter-q-hint" className="tr-muted tr-sys-type-support">
              {t('Bahasa Indonesia atau Inggris, misalnya "filter air" atau "water filter".')}
            </p>
            <input
              id="filter-q"
              name="q"
              type="search"
              className="tr-input"
              defaultValue={filters.q ?? ''}
              aria-describedby="filter-q-hint"
            />
          </div>
          <button type="submit" className="tr-btn tr-btn--primary">
            {t('Cari')}
          </button>
        </div>
        <details className="tr-disclosure">
          <summary className="tr-disclosure__toggle tr-sys-type-label">
            <Icon name="right" className="tr-disclosure__chev" />
            <span>{narrowing ? t('Filter ({n})', { n: narrowing }) : t('Filter')}</span>
          </summary>
          <div className="tr-disclosure__body tr-stack">
            <div className="tr-field">
              <label htmlFor="filter-sector" className="tr-sys-type-label">
                {t('Sektor')}
              </label>
              <select id="filter-sector" name="sector" className="tr-input tr-select" defaultValue={filters.sector ?? ''}>
                <option value="">{t('Semua sektor')}</option>
                {SECTORS.map((sector) => (
                  <option key={sector} value={sector}>
                    {t(sector)}
                  </option>
                ))}
              </select>
            </div>
            <div className="tr-field">
              <label htmlFor="filter-stage" className="tr-sys-type-label">
                {t('Tahap')}
              </label>
              <select id="filter-stage" name="stage" className="tr-input tr-select" defaultValue={filters.stage ?? ''}>
                <option value="">{t('Semua tahap')}</option>
                {STAGES.map((stage) => (
                  <option key={stage.value} value={stage.value}>
                    {t(stage.label)}
                  </option>
                ))}
              </select>
            </div>
            <label className="tr-row">
              <input type="checkbox" name="saved" value="true" defaultChecked={filters.saved === 'true'} />
              <span>{t('Hanya yang saya simpan')}</span>
            </label>
            <div className="tr-row">
              <button type="submit" className="tr-btn tr-btn--secondary">
                {t('Terapkan filter')}
              </button>
            </div>
          </div>
        </details>
      </form>
      {applied.length ? (
        <div className="tr-row">
          <ul className="tr-chips" aria-label={t('Filter aktif')}>
            {applied.map((filter) => (
              <li key={filter.name} className="tr-chip tr-sys-type-support-strong">
                <span>{filter.text}</span>
                <NextLink
                  className="tr-chip__remove"
                  href={finderHref(without(filter.name), selectedProduct)}
                  aria-label={t('Hapus filter {name}', { name: filter.text })}>
                  <Icon name="close" size="small" />
                </NextLink>
              </li>
            ))}
          </ul>
          <NextLink className="tr-link" href={finderHref({}, selectedProduct)}>
            {t('Hapus semua filter')}
          </NextLink>
        </div>
      ) : null}
      {items.length && open ? (
        <div className={chosen ? 'tr-listdetail has-selected' : 'tr-listdetail'}>
          <FocusFromHash key={selected ?? ''} />
          <div className="tr-listdetail__list tr-stack">
            <p className="tr-muted" role="status">
              {resultCount(page.total_estimate)}
            </p>
            {page.sections
              .filter((section) => section.items.length)
              .map((section) => (
                <section key={section.id} className="tr-stack" aria-labelledby={`bagian-${section.id}`}>
                  <h2 id={`bagian-${section.id}`} className="tr-sys-type-heading-sm">
                    {t(section.title)}
                  </h2>
                  <ul className="tr-list">
                    {section.items.map((item) => (
                      <InvestorRow
                        key={item.subject_id}
                        item={item}
                        active={item.subject_id === open.subject_id}
                        filters={filters}
                        selectedProduct={selectedProduct}
                      />
                    ))}
                  </ul>
                </section>
              ))}
          </div>
          <section
            id="detail"
            tabIndex={-1}
            className="tr-listdetail__detail tr-stack"
            aria-label={t('Rincian: {title}', { title: open.title })}>
            <p className="tr-listdetail__back">
              <NextLink className="tr-link" href={`${finderHref(filters, selectedProduct)}#hasil-${open.subject_id}`}>
                {t('Kembali ke hasil')}
              </NextLink>
            </p>
            <InvestorDetail
              key={open.subject_id}
              item={open}
              actingPartyId={me.active_party_id}
              products={products}
              returnTo={currentUrl}
              initialFit={initialFit}
            />
          </section>
        </div>
      ) : (
        <EmptyState
          icon="search"
          title={applied.length ? t('Tidak ada hasil untuk filter ini') : t('Belum ada yang diterbitkan di sini')}
          action={
            applied.length ? (
              <>
                <NextLink className="tr-btn tr-btn--primary" href={finderHref({}, selectedProduct)}>
                  {t('Hapus semua filter')}
                </NextLink>
                {page.relaxation && page.relaxation.remove !== 'all' ? (
                  <NextLink
                    className="tr-btn tr-btn--secondary"
                    href={finderHref({ ...filters, [page.relaxation.remove]: undefined }, selectedProduct)}>
                    {t('{label} ({n} hasil)', {
                      label: t(page.relaxation.label),
                      n: page.relaxation.total_estimate,
                    })}
                  </NextLink>
                ) : null}
              </>
            ) : undefined
          }>
          {applied.length
            ? t('Filter aktif: {list}. Syarat tidak dilonggarkan tanpa pilihan Anda.', {
                list: applied
                  .map((filter) => (filter.name === 'saved' ? t(FILTER_LABELS.saved) : `${filter.label} "${filter.value}"`))
                  .join(', '),
              })
            : t('Hasil muncul setelah pemiliknya menerbitkan profil atau inovasi.')}
        </EmptyState>
      )}
    </Screen>
  );
}

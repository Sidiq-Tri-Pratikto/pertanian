import NextLink from 'next/link';

import type { Me } from '@/api/client';
import { EmptyState } from '@/components/tr/EmptyState';
import { FinancialScope } from '@/components/tr/FinancialScope';
import { FundingRequestCard } from '@/components/tr/FundingRequestCard';
import { Icon } from '@/components/tr/Icon';
import { InventionCard } from '@/components/tr/InventionCard';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import { TktBadge } from '@/components/tr/TktBadge';
import { ContextBar } from '@/features/ContextBar';
import type { FitItem, MyProduct } from '@/features/discovery/fit';
import { ItemActions } from '@/features/discovery/ItemActions';
import { FocusFromHash } from '@/features/discovery/FocusFromHash';
import { appliedFilters, discoverHref, FILTER_LABELS, filterCount, reasonText, resultCount, RESULT_TYPES, SECTORS, type Discovery, type DiscoveryItem, type Filters, type ResultType } from '@/features/discovery/model';
import { scopeProps, type StoredRange } from '@/features/intake/model';
import { readPersona } from '@/features/persona';
import { labelOf, STAGES } from '@/features/portfolio/model';
import { FinderView } from '@/views/discovery/finder/FinderView';
import { PROVENANCE } from '@/views/parts';
import { t } from '@/features/i18n/t';

type Card = Record<string, unknown>;

function text(card: Card, key: string): string | undefined {
  const value = card[key];
  return typeof value === 'string' && value ? value : undefined;
}

function ResultCard({ item, actingPartyId }: { item: DiscoveryItem; actingPartyId: string }) {
  const card = item.card as Card;
  const actions = <ItemActions subjectType={item.subject_type} subjectId={item.subject_id} title={item.title} saved={item.saved} actingPartyId={actingPartyId} />;
  if (item.subject_type === 'INVENTION') {
    const stageText = text(card, 'stage') ? labelOf(STAGES, text(card, 'stage') as string) : undefined;
    const tktLevel = typeof card.tkt_level === 'number' ? card.tkt_level : null;
    return (
      <InventionCard
        title={item.title}
        category={text(card, 'sector')}
        manager={text(card, 'managing_party_name')}
        problem={text(card, 'summary')}
        maturity={stageText}
        facts={tktLevel ? <TktBadge level={tktLevel} stageLabel={stageText} showMeta /> : undefined}
        reasons={item.reasons.map(reasonText)}
        action={
          <>
            <NextLink className="tr-btn tr-btn--primary" href={`/inventions/${item.subject_id}`}>
              {t('Lihat inovasi')}
            </NextLink>
            {actions}
          </>
        }
      />
    );
  }
  if (item.subject_type === 'FUNDING_REQUEST') {
    const inventions = (card.inventions as { invention_id: string; title: string }[]) ?? [];
    return (
      <FundingRequestCard
        company={item.title}
        stage={text(card, 'financing_stage')}
        purpose={text(card, 'intended_use')}
        currency={text(card, 'currency')}
        target={text(card, 'target_amount')}
        desiredMin={text(card, 'desired_min')}
        desiredMax={text(card, 'desired_max')}
        inventions={inventions.map((invention) => (
          <NextLink key={invention.invention_id} className="tr-link" href={`/inventions/${invention.invention_id}`}>
            {invention.title}
          </NextLink>
        ))}
        reasons={item.reasons.map(reasonText)}
        action={actions}
      />
    );
  }
  const opportunities = (card.opportunities as { id: string; title: string }[]) ?? [];
  const check = card.check_range as StoredRange | null;
  return (
    <article className="tr-card">
      <div className="tr-card__body tr-stack">
        <h3 className="tr-sys-type-heading-sm">{item.title}</h3>
        {text(card, 'subtype') ? <p className="tr-muted tr-sys-type-support">{text(card, 'subtype')}</p> : null}
        <p className="tr-row">
          <Status tone="neutral" label={t(text(card, 'availability_label') ?? '')} />
          <span className="tr-tag tr-sys-type-support">{t(text(card, 'source_label') ?? '')}</span>
        </p>
        {text(card, 'thesis') ? <p>{text(card, 'thesis')}</p> : null}
        {check ? <FinancialScope {...scopeProps(check)} /> : null}
        {opportunities.length ? <p>{t('Mandat aktif: {list}', { list: opportunities.map((opportunity) => opportunity.title).join('; ') })}</p> : null}
        {item.reasons.length ? (
          <ul className="tr-reasons">
            {item.reasons.map((reason) => (
              <li key={reason}>{reasonText(reason)}</li>
            ))}
          </ul>
        ) : null}
        <div className="tr-row">
          <NextLink className="tr-btn tr-btn--primary" href={`/partners/${item.subject_id}`}>
            {t('Lihat profil mitra')}
          </NextLink>
          {actions}
        </div>
      </div>
    </article>
  );
}

/** One compact line per result: the name, one deciding fact and a saved mark. The full card opens beside it. */
function rowFacts(item: DiscoveryItem): string {
  const card = item.card as Card;
  if (item.subject_type === 'INVENTION') {
    const sector = text(card, 'sector');
    const stage = text(card, 'stage');
    const tktLevel = typeof card.tkt_level === 'number' ? `TKT ${card.tkt_level}` : undefined;
    return [sector ? t(sector) : undefined, stage ? t(labelOf(STAGES, stage)) : undefined, tktLevel].filter(Boolean).join(' · ');
  }
  if (item.subject_type === 'FUNDING_REQUEST') {
    const inventions = (card.inventions as { title: string }[] | undefined) ?? [];
    return inventions.length ? t('Pendanaan perusahaan untuk {list}', { list: inventions.map((invention) => invention.title).join(', ') }) : t('Pendanaan perusahaan');
  }
  return [text(card, 'subtype'), text(card, 'availability_label')].filter(Boolean).join(' · ');
}

type Props = {
  me: Me;
  type: ResultType;
  filters: Filters;
  page: Discovery;
  fundingOn: boolean;
  matchesHref: string | null;
  selected?: string;
  products?: MyProduct[];
  selectedProduct?: string;
  initialFit?: FitItem[] | null;
};

/**
 * S03: separate result types, a search toolbar with filters behind "Filter (n)", removable chips, and a compact list
 * beside one open result. Everything lives in the address, so Back returns to the same search and the same result.
 */
export function DiscoverView({
  me,
  type,
  filters,
  page,
  fundingOn,
  matchesHref,
  selected,
  products,
  selectedProduct,
  initialFit,
}: Props) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  if (persona === 'inovator' && type === 'partners' && products !== undefined) {
    return (
      <FinderView
        me={me}
        filters={filters}
        page={page}
        fundingOn={fundingOn}
        matchesHref={matchesHref}
        selected={selected}
        products={products}
        selectedProduct={selectedProduct}
        initialFit={initialFit}
      />
    );
  }
  const items = page.sections.flatMap((section) => section.items);
  const applied = appliedFilters(page.filters, (value) => labelOf(STAGES, value));
  const types = RESULT_TYPES.filter((item) => !item.capability || fundingOn);
  const chosen = items.find((item) => item.subject_id === selected);
  const open = chosen ?? items[0];
  const narrowing = filterCount(filters);
  const without = (name: string): Filters => Object.fromEntries(applied.filter((filter) => filter.name !== name).map((filter) => [filter.name, filter.value])) as Filters;
  return (
    <Screen
      persona={persona}
      current={persona === 'mitra' ? 'jelajahi' : 'temukan'}
      title={persona === 'mitra' ? 'Jelajahi' : 'Temukan Investor/Mitra'}
      subtitle={t('Hasil disusun menurut profil Anda dan tanggal terbit, bukan menurut popularitas.')}
      provenance={PROVENANCE}
      context={<ContextBar me={me} />}>
      <nav aria-label={t('Jenis hasil')} className="tr-row">
        {types.map((item) => (
          <NextLink key={item.value} className={`tr-btn ${item.value === type ? 'tr-btn--primary' : 'tr-btn--secondary'}`} aria-current={item.value === type ? 'page' : undefined} href={discoverHref(item.value, filters)}>
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
        <input type="hidden" name="type" value={type} />
        <div className="tr-toolbar">
          <div className="tr-field">
            <label htmlFor="filter-q" className="tr-sys-type-label">
              {t('Kata kunci')}
            </label>
            <p id="filter-q-hint" className="tr-muted tr-sys-type-support">
              {t('Bahasa Indonesia atau Inggris, misalnya "filter air" atau "water filter".')}
            </p>
            <input id="filter-q" name="q" type="search" className="tr-input" defaultValue={filters.q ?? ''} aria-describedby="filter-q-hint" />
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
            {type === 'inventions' ? (
              <div className="tr-field">
                <label htmlFor="filter-min-tkt" className="tr-sys-type-label">
                  {t('TKT minimum')}
                </label>
                <select id="filter-min-tkt" name="min_tkt" className="tr-input tr-select" defaultValue={filters.min_tkt ?? ''}>
                  <option value="">{t('Semua')}</option>
                  {[3, 4, 5, 6, 7, 8, 9].map((level) => (
                    <option key={level} value={String(level)}>
                      {t('TKT {n} ke atas', { n: level })}
                    </option>
                  ))}
                </select>
              </div>
            ) : null}
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
                <NextLink className="tr-chip__remove" href={discoverHref(type, without(filter.name))} aria-label={t('Hapus filter {name}', { name: filter.text })}>
                  <Icon name="close" size="small" />
                </NextLink>
              </li>
            ))}
          </ul>
          <NextLink className="tr-link" href={discoverHref(type)}>
            {t('Hapus semua filter')}
          </NextLink>
        </div>
      ) : null}
      {items.length && open ? (
        <div className={chosen ? 'tr-listdetail has-selected' : 'tr-listdetail'}>
          <FocusFromHash key={selected ?? ''} />
          <div className="tr-listdetail__list tr-stack">
            <p className="tr-muted" role="status">{resultCount(page.total_estimate)}</p>
            {page.sections
              .filter((section) => section.items.length)
              .map((section) => (
                <section key={section.id} className="tr-stack" aria-labelledby={`bagian-${section.id}`}>
                  <h2 id={`bagian-${section.id}`} className="tr-sys-type-heading-sm">
                    {t(section.title)}
                  </h2>
                  <ul className="tr-list">
                    {section.items.map((item) => (
                      <li key={item.subject_id} id={`hasil-${item.subject_id}`} tabIndex={-1} className="tr-listrow" aria-current={item.subject_id === open.subject_id ? 'true' : undefined}>
                        <NextLink className="tr-link tr-sys-type-body-strong" href={`${discoverHref(type, filters, item.subject_id)}#detail`}>
                          {item.title}
                        </NextLink>
                        <span className="tr-muted tr-sys-type-support">
                          {rowFacts(item)}
                          {item.saved ? t(' · Disimpan') : ''}
                        </span>
                      </li>
                    ))}
                  </ul>
                </section>
              ))}
            {page.next_cursor ? (
              <p>
                <NextLink className="tr-link" href={`${discoverHref(type, filters)}&cursor=${encodeURIComponent(page.next_cursor)}`}>
                  {t('Hasil berikutnya')}
                </NextLink>
              </p>
            ) : null}
          </div>
          <section id="detail" tabIndex={-1} className="tr-listdetail__detail tr-stack" aria-label={t('Rincian: {title}', { title: open.title })}>
            <p className="tr-listdetail__back">
              <NextLink className="tr-link" href={`${discoverHref(type, filters)}#hasil-${open.subject_id}`}>
                {t('Kembali ke hasil')}
              </NextLink>
            </p>
            <ResultCard item={open} actingPartyId={me.active_party_id} />
          </section>
        </div>
      ) : (
        <EmptyState
          icon="search"
          title={applied.length ? t('Tidak ada hasil untuk filter ini') : t('Belum ada yang diterbitkan di sini')}
          action={
            applied.length ? (
              <>
                <NextLink className="tr-btn tr-btn--primary" href={discoverHref(type)}>
                  {t('Hapus semua filter')}
                </NextLink>
                {page.relaxation && page.relaxation.remove !== 'all' ? (
                  <NextLink className="tr-btn tr-btn--secondary" href={discoverHref(type, { ...filters, [page.relaxation.remove]: undefined })}>
                    {t('{label} ({n} hasil)', { label: t(page.relaxation.label), n: page.relaxation.total_estimate })}
                  </NextLink>
                ) : null}
              </>
            ) : undefined
          }>
          {applied.length
            ? `${t('Filter aktif: {list}. Syarat tidak dilonggarkan tanpa pilihan Anda.', { list: applied.map((filter) => (filter.name === 'saved' ? t(FILTER_LABELS.saved) : `${filter.label} "${filter.value}"`)).join(', ') })}${filters.min_tkt ? ` ${t('Inovasi yang belum mengisi TKT tidak ditampilkan saat filter TKT minimum aktif.')}` : ''}`
            : t('Hasil muncul setelah pemiliknya menerbitkan profil atau inovasi.')}
        </EmptyState>
      )}
    </Screen>
  );
}

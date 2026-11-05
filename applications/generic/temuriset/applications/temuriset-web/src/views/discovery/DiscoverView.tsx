import NextLink from 'next/link';

import type { Me } from '@/api/client';
import { EmptyState } from '@/components/tr/EmptyState';
import { FinancialScope } from '@/components/tr/FinancialScope';
import { FundingRequestCard } from '@/components/tr/FundingRequestCard';
import { InventionCard } from '@/components/tr/InventionCard';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import { ContextBar } from '@/features/ContextBar';
import { ItemActions } from '@/features/discovery/ItemActions';
import { discoverHref, RESULT_TYPES, SECTORS, type Discovery, type DiscoveryItem, type Filters, type ResultType } from '@/features/discovery/model';
import { scopeProps, type StoredRange } from '@/features/intake/model';
import { readPersona } from '@/features/persona';
import { labelOf, STAGES } from '@/features/portfolio/model';
import { PROVENANCE } from '@/views/parts';

const FILTER_LABELS: Record<string, string> = { q: 'Kata kunci', sector: 'Sektor', stage: 'Tahap', saved: 'Hanya yang disimpan' };

type Card = Record<string, unknown>;

function text(card: Card, key: string): string | undefined {
  const value = card[key];
  return typeof value === 'string' && value ? value : undefined;
}

function ResultCard({ item, actingPartyId }: { item: DiscoveryItem; actingPartyId: string }) {
  const card = item.card as Card;
  const actions = <ItemActions subjectType={item.subject_type} subjectId={item.subject_id} title={item.title} saved={item.saved} actingPartyId={actingPartyId} />;
  if (item.subject_type === 'INVENTION') {
    return (
      <InventionCard
        title={item.title}
        category={text(card, 'sector')}
        manager={text(card, 'managing_party_name')}
        problem={text(card, 'summary')}
        maturity={text(card, 'stage') ? labelOf(STAGES, text(card, 'stage') as string) : undefined}
        reasons={item.reasons}
        action={
          <>
            <NextLink className="tr-btn tr-btn--primary" href={`/inventions/${item.subject_id}`}>
              Lihat inovasi
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
        reasons={item.reasons}
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
          <Status tone="neutral" label={text(card, 'availability_label') ?? ''} />
          <span className="tr-tag tr-sys-type-support">{text(card, 'source_label')}</span>
        </p>
        {text(card, 'thesis') ? <p>{text(card, 'thesis')}</p> : null}
        {check ? <FinancialScope {...scopeProps(check)} /> : null}
        {opportunities.length ? <p>{`Mandat aktif: ${opportunities.map((opportunity) => opportunity.title).join('; ')}`}</p> : null}
        {item.reasons.length ? (
          <ul className="tr-reasons">
            {item.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        ) : null}
        <div className="tr-row">
          <NextLink className="tr-btn tr-btn--primary" href={`/partners/${item.subject_id}`}>
            Lihat profil mitra
          </NextLink>
          {actions}
        </div>
      </div>
    </article>
  );
}

type Props = { me: Me; type: ResultType; filters: Filters; page: Discovery; fundingOn: boolean; matchesHref: string | null };

/** S03: separate result types, filters in the address, sections that never rank by activity. */
export function DiscoverView({ me, type, filters, page, fundingOn, matchesHref }: Props) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  const items = page.sections.flatMap((section) => section.items);
  const active = Object.entries(page.filters).filter(([name]) => name in FILTER_LABELS);
  const types = RESULT_TYPES.filter((item) => !item.capability || fundingOn);
  return (
    <Screen
      persona={persona}
      current={persona === 'mitra' ? 'jelajahi' : 'temukan'}
      title={persona === 'mitra' ? 'Jelajahi' : 'Temukan Investor/Mitra'}
      subtitle="Hasil disusun menurut profil Anda dan tanggal terbit, bukan menurut popularitas."
      provenance={PROVENANCE}
      context={<ContextBar me={me} />}>
      <nav aria-label="Jenis hasil" className="tr-row">
        {types.map((item) => (
          <NextLink key={item.value} className={`tr-btn ${item.value === type ? 'tr-btn--primary' : 'tr-btn--secondary'}`} aria-current={item.value === type ? 'page' : undefined} href={discoverHref(item.value, filters)}>
            {item.label}
          </NextLink>
        ))}
      </nav>
      {matchesHref ? (
        <p>
          <NextLink className="tr-link" href={matchesHref}>
            Lihat kecocokan untuk kebutuhan Anda
          </NextLink>
        </p>
      ) : null}
      <form method="get" action="/discover" className="tr-panel tr-stack" role="search" aria-label="Cari dan saring">
        <input type="hidden" name="type" value={type} />
        <div className="tr-field">
          <label htmlFor="filter-q" className="tr-sys-type-label">
            Kata kunci
          </label>
          <p id="filter-q-hint" className="tr-muted tr-sys-type-support">
            Bahasa Indonesia atau Inggris, misalnya &quot;filter air&quot; atau &quot;water filter&quot;.
          </p>
          <input id="filter-q" name="q" type="search" className="tr-input" defaultValue={filters.q ?? ''} aria-describedby="filter-q-hint" />
        </div>
        <div className="tr-field">
          <label htmlFor="filter-sector" className="tr-sys-type-label">
            Sektor
          </label>
          <select id="filter-sector" name="sector" className="tr-input tr-select" defaultValue={filters.sector ?? ''}>
            <option value="">Semua sektor</option>
            {SECTORS.map((sector) => (
              <option key={sector} value={sector}>
                {sector}
              </option>
            ))}
          </select>
        </div>
        <div className="tr-field">
          <label htmlFor="filter-stage" className="tr-sys-type-label">
            Tahap
          </label>
          <select id="filter-stage" name="stage" className="tr-input tr-select" defaultValue={filters.stage ?? ''}>
            <option value="">Semua tahap</option>
            {STAGES.map((stage) => (
              <option key={stage.value} value={stage.value}>
                {stage.label}
              </option>
            ))}
          </select>
        </div>
        <label className="tr-row">
          <input type="checkbox" name="saved" value="true" defaultChecked={filters.saved === 'true'} />
          <span>Hanya yang saya simpan</span>
        </label>
        <div className="tr-row">
          <button type="submit" className="tr-btn tr-btn--primary">
            Terapkan
          </button>
          {active.length ? (
            <NextLink className="tr-link" href={discoverHref(type)}>
              Hapus semua filter
            </NextLink>
          ) : null}
        </div>
      </form>
      {items.length ? (
        <>
          <p className="tr-muted" role="status">{`${page.total_estimate} hasil`}</p>
          {page.sections
            .filter((section) => section.items.length)
            .map((section) => (
              <section key={section.id} className="tr-stack" aria-labelledby={`bagian-${section.id}`}>
                <h2 id={`bagian-${section.id}`} className="tr-sys-type-heading-sm">
                  {section.title}
                </h2>
                <ul className="tr-grid">
                  {section.items.map((item) => (
                    <li key={item.subject_id}>
                      <ResultCard item={item} actingPartyId={me.active_party_id} />
                    </li>
                  ))}
                </ul>
              </section>
            ))}
          {page.next_cursor ? (
            <p>
              <NextLink className="tr-link" href={`${discoverHref(type, filters)}&cursor=${encodeURIComponent(page.next_cursor)}`}>
                Hasil berikutnya
              </NextLink>
            </p>
          ) : null}
        </>
      ) : (
        <EmptyState
          icon="search"
          title={active.length ? 'Tidak ada hasil untuk filter ini' : 'Belum ada yang diterbitkan di sini'}
          action={
            active.length ? (
              <>
                <NextLink className="tr-btn tr-btn--primary" href={discoverHref(type)}>
                  Hapus semua filter
                </NextLink>
                {page.relaxation && page.relaxation.remove !== 'all' ? (
                  <NextLink className="tr-btn tr-btn--secondary" href={discoverHref(type, { ...filters, [page.relaxation.remove]: undefined })}>
                    {`${page.relaxation.label} (${page.relaxation.total_estimate} hasil)`}
                  </NextLink>
                ) : null}
              </>
            ) : undefined
          }>
          {active.length
            ? `Filter aktif: ${active.map(([name, value]) => (name === 'saved' ? FILTER_LABELS[name] : `${FILTER_LABELS[name]} "${String(value)}"`)).join(', ')}. Syarat tidak dilonggarkan tanpa pilihan Anda.`
            : 'Hasil muncul setelah pemiliknya menerbitkan profil atau inovasi.'}
        </EmptyState>
      )}
    </Screen>
  );
}

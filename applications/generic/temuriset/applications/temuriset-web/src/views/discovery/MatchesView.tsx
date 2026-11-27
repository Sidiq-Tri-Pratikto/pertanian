'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

import type { Me } from '@/api/client';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Disclosure } from '@/components/tr/Disclosure';
import { EmptyState } from '@/components/tr/EmptyState';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import { ContextBar } from '@/features/ContextBar';
import { runMatch } from '@/features/discovery/api';
import type { MatchResult, MatchRun, MatchSourceRef } from '@/features/discovery/model';
import { ExternalRoute } from '@/features/intake/ExternalRoute';
import { readPersona } from '@/features/persona';
import { labelTone, MatchCard } from '@/views/discovery/MatchCard';
import { PROVENANCE } from '@/views/parts';
import { t } from '@/features/i18n/t';

/**
 * Investor finder: a compact list of recommended mandates beside the open one. On a phone the list and the open match
 * take turns, and t('Kembali ke daftar') puts focus back on the row the person left.
 */
function MatchList({ results, source }: { results: MatchResult[]; source: MatchSourceRef }) {
  const [chosen, setChosen] = useState<string | null>(null);
  const detail = useRef<HTMLDivElement>(null);
  const open = results.find((result) => result.opportunity_id === chosen) ?? results[0];

  function choose(id: string) {
    setChosen(id);
    requestAnimationFrame(() => detail.current?.focus());
  }

  function back() {
    const id = open.opportunity_id;
    setChosen(null);
    requestAnimationFrame(() => document.getElementById(`baris-${id}`)?.focus());
  }

  return (
    <div className={chosen ? 'tr-listdetail has-selected' : 'tr-listdetail'}>
      <ul className="tr-list tr-listdetail__list">
        {results.map((result) => (
          <li key={result.opportunity_id} className="tr-listrow" aria-current={result.opportunity_id === open.opportunity_id ? 'true' : undefined}>
            <button id={`baris-${result.opportunity_id}`} type="button" className="tr-rowbutton" onClick={() => choose(result.opportunity_id)}>
              <span className="tr-sys-type-body-strong">{result.title}</span>
              <span className="tr-muted tr-sys-type-support">{result.partner}</span>
            </button>
            <span>
              <Status tone={labelTone(result)} icon={null} label={t(result.label)} />
            </span>
          </li>
        ))}
      </ul>
      <div ref={detail} tabIndex={-1} className="tr-listdetail__detail tr-stack" aria-label={t('Rincian: {title}', { title: open.title })} role="region">
        <p className="tr-listdetail__back">
          <button type="button" className="tr-link tr-linkbutton" onClick={back}>
            {t('Kembali ke daftar')}
          </button>
        </p>
        <MatchCard result={open} source={source} />
      </div>
    </div>
  );
}

export type ExternalPartner = { id: string; name: string; url: string };

type Props = { me: Me; source: MatchSourceRef; externals: ExternalPartner[] };

/** S10 for one source: runs matching, shows recommended targets, then what is not recommended and why. */
export function MatchesView({ me, source, externals }: Props) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  const [run, setRun] = useState<MatchRun | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const started = useRef(false);

  const load = useCallback(async () => {
    setFailure(null);
    try {
      setRun(await runMatch(source, me.active_party_id));
    } catch (error) {
      setFailure(error instanceof ApiError ? error.message : t('Kecocokan belum dapat dihitung. Coba lagi.'));
    }
  }, [source, me.active_party_id]);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    void load();
  }, [load]);

  return (
    <Screen
      persona={persona}
      current="temukan"
      title={t('Kecocokan')}
      subtitle={run ? t('Untuk {title}, versi {n}', { title: run.source.title, n: run.source.version }) : undefined}
      provenance={PROVENANCE}
      context={<ContextBar me={me} />}>
      {failure ? (
        <Status tone="danger" label={t('Kecocokan belum dihitung')} live="alert">
          <p>{failure}</p>
          <Button onClick={() => void load()}>{t('Coba lagi')}</Button>
        </Status>
      ) : null}
      {run?.retrieval?.fallback_reason ? (
        <Status tone="neutral" label={t('Pencarian eksperimental tidak tersedia')} live>
          <p>{t('Kecocokan dihitung dengan kata kunci dan aturan yang berlaku.')}</p>
        </Status>
      ) : null}
      {!run && !failure ? <Status tone="neutral" label={t('Menghitung kecocokan')} live /> : null}
      {run ? (
        <>
          <section className="tr-stack" aria-labelledby="direkomendasikan">
            <h2 id="direkomendasikan" className="tr-sys-type-heading-sm">
              {t('Mandat yang sesuai')}
            </h2>
            {run.results.length ? (
              <MatchList results={run.results} source={source} />
            ) : (
              <EmptyState icon="search" title={t('Belum ada mandat yang sesuai')}>
                {t('Tidak ada mandat aktif yang relevan dan memenuhi syarat masuk untuk kebutuhan ini.')}
              </EmptyState>
            )}
          </section>
          {run.excluded.length ? (
            <Disclosure label={t('Mandat tidak direkomendasikan ({n})', { n: run.excluded.length })}>
              <p className="tr-muted">{t('Mandat ini tidak cocok, atau belum ada sinyal relevansi dengan kebutuhan Anda.')}</p>
              <ul className="tr-stack">
                {run.excluded.map((result) => (
                  <li key={result.opportunity_id}>
                    <MatchCard result={result} source={source} />
                  </li>
                ))}
              </ul>
            </Disclosure>
          ) : null}
        </>
      ) : null}
      {externals.length ? (
        <section className="tr-stack" aria-labelledby="formulir-mitra">
          <h2 id="formulir-mitra" className="tr-sys-type-heading-sm">
            {t('Mitra dengan formulir sendiri')}
          </h2>
          <ul className="tr-stack">
            {externals.map((partner) => (
              <li key={partner.id} className="tr-panel tr-stack">
                <h3 className="tr-sys-type-label">{partner.name}</h3>
                <ExternalRoute partyId={partner.id} actingPartyId={me.active_party_id} url={partner.url} record />
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </Screen>
  );
}

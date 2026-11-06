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
import type { MatchRun, MatchSourceRef } from '@/features/discovery/model';
import { ExternalRoute } from '@/features/intake/ExternalRoute';
import { readPersona } from '@/features/persona';
import { MatchCard } from '@/views/discovery/MatchCard';
import { PROVENANCE } from '@/views/parts';

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
      setFailure(error instanceof ApiError ? error.message : 'Kecocokan belum dapat dihitung. Coba lagi.');
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
      title="Kecocokan"
      subtitle={run ? `Untuk ${run.source.title}, versi ${run.source.version}` : undefined}
      provenance={PROVENANCE}
      context={<ContextBar me={me} />}>
      {failure ? (
        <Status tone="danger" label="Kecocokan belum dihitung" live="alert">
          <p>{failure}</p>
          <Button onClick={() => void load()}>Coba lagi</Button>
        </Status>
      ) : null}
      {!run && !failure ? <Status tone="neutral" label="Menghitung kecocokan" live /> : null}
      {run ? (
        <>
          <section className="tr-stack" aria-labelledby="direkomendasikan">
            <h2 id="direkomendasikan" className="tr-sys-type-heading-sm">
              Mandat yang sesuai
            </h2>
            {run.results.length ? (
              <ul className="tr-stack">
                {run.results.map((result) => (
                  <li key={result.opportunity_id}>
                    <MatchCard result={result} source={source} />
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState icon="search" title="Belum ada mandat yang sesuai">
                Tidak ada mandat aktif yang relevan dan memenuhi syarat masuk untuk kebutuhan ini.
              </EmptyState>
            )}
          </section>
          {run.excluded.length ? (
            <Disclosure label={`Mandat tidak direkomendasikan (${run.excluded.length})`}>
              <p className="tr-muted">Mandat ini tidak cocok, atau belum ada sinyal relevansi dengan kebutuhan Anda.</p>
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
            Mitra dengan formulir sendiri
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

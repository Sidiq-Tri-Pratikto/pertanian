'use client';

import NextLink from 'next/link';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useRef, useState } from 'react';

import { newIdempotencyKey, type Me } from '@/api/client';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Checkbox } from '@/components/tr/Checkbox';
import { ErrorSummary } from '@/components/tr/ErrorSummary';
import { RequirementRow } from '@/components/tr/RequirementRow';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import { TextArea } from '@/components/tr/TextArea';
import { VersionConflict } from '@/components/tr/VersionConflict';
import { ContextBar } from '@/features/ContextBar';
import { matchesHref, READINESS, type MatchSourceRef } from '@/features/discovery/model';
import { AVAILABILITY_REASON } from '@/features/intake/model';
import { readPersona } from '@/features/persona';
import { runPreflight, submitPitch } from '@/features/pitches/api';
import { missingFiles, SOURCE_KIND, type Preflight } from '@/features/pitches/model';
import { keepsKey, stateOf, type SubmitState } from '@/features/pitches/submit-state';
import { PROVENANCE } from '@/views/parts';

const BRIEF_LIMIT = 10000;
const REVIEW: Record<string, string> = {
  PROVIDED_UNREVIEWED: 'Isinya belum diperiksa',
  REVIEWED_SUPPORTED: 'Sudah diperiksa',
  REVIEWED_UNSUPPORTED: 'Diperiksa, tidak mendukung',
  NEEDS_CLARIFICATION: 'Perlu klarifikasi',
};

type Props = { me: Me; source: MatchSourceRef; targetId: string };

/** S11: everything that would be sent, the files to share and the brief, then one deliberate send (UX-08, UX-17). */
export function PreflightView({ me, source, targetId }: Props) {
  const router = useRouter();
  const persona = readPersona(me.account.persona) ?? 'inovator';
  const [preflight, setPreflight] = useState<Preflight | null>(null);
  const [loadFailure, setLoadFailure] = useState<string | null>(null);
  const [brief, setBrief] = useState<string | null>(null);
  const [chosen, setChosen] = useState<string[]>([]);
  const [state, setState] = useState<SubmitState>({ kind: 'idle' });
  const [attempt, setAttempt] = useState(0);
  const [missing, setMissing] = useState<string[]>([]);
  // One key per intent, made when the page renders and kept across retries until a final answer (FR-002).
  const key = useRef(newIdempotencyKey());
  const started = useRef(false);

  const check = useCallback(async () => {
    setLoadFailure(null);
    try {
      const fresh = await runPreflight(source, targetId, me.active_party_id);
      setPreflight(fresh);
      // A brief the person already edited survives a fresh check (AC34).
      setBrief((current) => current ?? fresh.brief.text);
      setChosen((current) => current.filter((id) => fresh.shareable_files.some((file) => file.version_id === id)));
      setState({ kind: 'idle' });
      key.current = newIdempotencyKey();
    } catch (error) {
      setLoadFailure(ApiError.from(error).message);
    }
  }, [source, targetId, me.active_party_id]);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    void check();
  }, [check]);

  async function send() {
    if (!preflight || brief === null) return;
    const gaps = missingFiles(preflight, chosen);
    if (gaps.length) {
      setMissing(gaps.map((gap) => `Pilih berkas untuk syarat “${gap.label}”.`));
      setAttempt((value) => value + 1);
      return;
    }
    setMissing([]);
    setState({ kind: 'sending' });
    const files = preflight.shareable_files.filter((file) => chosen.includes(file.version_id)).map((file) => ({ document_id: file.document_id, version: file.version }));
    try {
      const sent = await submitPitch({ acting_party_id: me.active_party_id, preflight_token: preflight.token, brief, files }, key.current);
      setState({ kind: 'sent', pitchId: sent.pitch_id });
      router.push(`/pitches/${sent.pitch_id}?terkirim=1`);
    } catch (error) {
      const next = stateOf(error);
      if (!keepsKey(next)) key.current = newIdempotencyKey();
      setState(next);
    }
  }

  const shell = {
    persona,
    current: 'temukan',
    provenance: PROVENANCE,
    context: <ContextBar me={me} />,
    back: (
      <NextLink className="tr-link" href={matchesHref(source)}>
        Kembali ke kecocokan
      </NextLink>
    ),
  };

  if (!preflight) {
    return (
      <Screen {...shell} title="Periksa sebelum mengirim">
        {loadFailure ? (
          <Status tone="danger" label="Pemeriksaan belum dapat dijalankan" live="alert">
            <p>{loadFailure}</p>
            <Button onClick={() => void check()}>Coba lagi</Button>
          </Status>
        ) : (
          <Status tone="neutral" label="Memeriksa pitching" live />
        )}
      </Screen>
    );
  }

  const ready = preflight.readiness === 'READY_TO_SUBMIT';
  const available = preflight.availability.available;
  const blockedReason = !ready
    ? `Belum siap dikirim: ${preflight.gap?.reason ?? READINESS[preflight.readiness]}`
    : !available && preflight.availability.reason
      ? AVAILABILITY_REASON[preflight.availability.reason]
      : preflight.duplicate_pitch_id
        ? 'Pitching untuk mandat ini sudah ada.'
        : null;
  const recipient = preflight.recipient.name;
  const sender = preflight.sender.name;
  const errors = missing.map((message) => ({ fieldId: 'berkas-pilihan', message }));
  return (
    <Screen {...shell} title="Periksa sebelum mengirim" subtitle={`${preflight.source.title} kepada ${recipient}`}>
      {errors.length ? <ErrorSummary errors={errors} focusKey={attempt} /> : null}
      <section className="tr-panel tr-stack" aria-labelledby="ringkasan-kirim">
        <h2 id="ringkasan-kirim" className="tr-sys-type-heading-sm">
          Yang akan dikirim
        </h2>
        <p>
          <Status tone={ready ? 'neutral' : preflight.readiness === 'BLOCKED_FOR_THIS_TARGET' ? 'danger' : 'warning'} icon={null} label={READINESS[preflight.readiness]} />
        </p>
        <dl className="tr-facts">
          <div>
            <dt className="tr-sys-type-support-strong">Penerima</dt>
            <dd>{`${recipient} · ${preflight.opportunity.title}, versi ${preflight.opportunity.version}`}</dd>
          </div>
          <div>
            <dt className="tr-sys-type-support-strong">Pengirim</dt>
            <dd>{sender}</dd>
          </div>
          <div>
            <dt className="tr-sys-type-support-strong">Kebutuhan</dt>
            <dd>{`${SOURCE_KIND[preflight.source.type]}: ${preflight.source.title}, versi ${preflight.source.version}`}</dd>
          </div>
          <div>
            <dt className="tr-sys-type-support-strong">Inovasi</dt>
            <dd>{preflight.inventions.map((invention) => `${invention.title}, versi ${invention.version}`).join('; ')}</dd>
          </div>
        </dl>
        {preflight.duplicate_pitch_id ? (
          <Status tone="warning" label="Pitching untuk mandat ini sudah ada">
            <p>
              <NextLink className="tr-link" href={`/pitches/${preflight.duplicate_pitch_id}`}>
                Buka pitching yang ada
              </NextLink>
            </p>
          </Status>
        ) : null}
      </section>
      <section className="tr-stack" aria-labelledby="syarat-kirim">
        <h2 id="syarat-kirim" className="tr-sys-type-heading-sm">
          Syarat mandat
        </h2>
        <ul className="tr-stack">
          {preflight.rows.map((row) => (
            <RequirementRow key={row.requirement_id} label={row.label} result={row.result} stage={row.applies_at} mandatory={row.mandatory} mode={row.verification_mode} reason={row.reason} headingLevel={3} />
          ))}
        </ul>
      </section>
      <fieldset id="berkas-pilihan" className="tr-stack" tabIndex={-1}>
        <legend className="tr-sys-type-heading-sm">Berkas yang dibagikan</legend>
        <p className="tr-muted">{`Hanya versi yang Anda centang yang dapat diunduh ${recipient}. Akses dapat dicabut nanti, tetapi salinan yang sudah diunduh tidak dapat ditarik.`}</p>
        {preflight.shareable_files.length ? (
          preflight.shareable_files.map((file) => (
            <Checkbox
              key={file.version_id}
              id={`berkas-${file.version_id}`}
              label={`${file.title}, versi ${file.version}`}
              hint={`Berkas tersedia · ${REVIEW[file.review_state] ?? file.review_state}`}
              checked={chosen.includes(file.version_id)}
              onChange={(on) => setChosen((current) => (on ? [...current, file.version_id] : current.filter((id) => id !== file.version_id)))}
            />
          ))
        ) : (
          <p className="tr-muted">Belum ada berkas yang dapat dibagikan untuk inovasi ini.</p>
        )}
      </fieldset>
      <TextArea id="brief-pitching" label="Brief pitching" hint="Disusun dari fakta yang Anda nyatakan. Anda dapat mengubahnya sebelum mengirim." value={brief ?? ''} onChange={setBrief} rows={12} limit={BRIEF_LIMIT} />
      {state.kind === 'stale' ? (
        <VersionConflict what={`${state.reason} Periksa ulang sebelum mengirim.`} draft={brief} onRefresh={() => void check()} refreshLabel="Periksa ulang" />
      ) : null}
      {state.kind === 'lost' ? (
        <Status tone="warning" label="Status pengiriman belum diketahui" live="alert">
          <p>Jawaban layanan tidak sampai. Mengirim lagi aman: pitching yang sama tidak akan terkirim dua kali.</p>
          <Button intent="primary" onClick={() => void send()}>
            Coba kirim lagi
          </Button>
        </Status>
      ) : null}
      {state.kind === 'duplicate' ? (
        <Status tone="warning" label="Pitching ini sudah ada" live="alert">
          <p>
            <NextLink className="tr-link" href={`/pitches/${state.pitchId}`}>
              Buka pitching yang ada
            </NextLink>
          </p>
        </Status>
      ) : null}
      {state.kind === 'not_ready' || state.kind === 'failed' ? (
        <Status tone="danger" label="Pitching belum terkirim" live="alert">
          <p>{state.message}</p>
          {state.kind === 'not_ready' && state.requirement ? <p>{`Syarat: ${state.requirement}`}</p> : null}
          {state.kind === 'failed' && state.requestId ? <p className="tr-muted tr-sys-type-support">{`ID referensi: ${state.requestId}`}</p> : null}
        </Status>
      ) : null}
      <section className="tr-panel tr-stack" aria-labelledby="efek-kirim">
        <h2 id="efek-kirim" className="tr-sys-type-heading-sm">
          Yang terjadi saat Anda mengirim
        </h2>
        <p>{`${sender} mengirim brief ini kepada ${recipient}, beserta akses unduh ke ${chosen.length} berkas yang dicentang. Kebutuhan dan inovasi dibekukan pada versi di atas; perubahan nanti tidak mengubah pitching ini.`}</p>
        <div className="tr-row">
          <Button intent="primary" icon="arrow" busy={state.kind === 'sending'} busyLabel="Mengirim…" disabledReason={blockedReason} onClick={() => void send()}>
            {`Kirim pitching kepada ${recipient}`}
          </Button>
        </div>
      </section>
    </Screen>
  );
}

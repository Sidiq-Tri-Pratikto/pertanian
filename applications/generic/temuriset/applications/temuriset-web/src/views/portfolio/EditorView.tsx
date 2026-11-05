'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useReducer, useRef, useState, type ReactNode } from 'react';

import { newIdempotencyKey, type Me } from '@/api/client';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { ContextSwitcher } from '@/components/tr/ContextSwitcher';
import { ErrorSummary } from '@/components/tr/ErrorSummary';
import { FactSource } from '@/components/tr/FactSource';
import { InventionCard } from '@/components/tr/InventionCard';
import { SaveState } from '@/components/tr/SaveState';
import { Screen } from '@/components/tr/Screen';
import { Select } from '@/components/tr/Select';
import { Status } from '@/components/tr/Status';
import { Steps } from '@/components/tr/Steps';
import { TextArea } from '@/components/tr/TextArea';
import { TextField } from '@/components/tr/TextField';
import { VersionConflict } from '@/components/tr/VersionConflict';
import { ContextBar, contextOptions } from '@/features/ContextBar';
import { readPersona } from '@/features/persona';
import { publishInvention, readInvention, saveDraft } from '@/features/portfolio/api';
import {
  draftRequest,
  EMPTY_CLAIM,
  EMPTY_FACT,
  FIELD_ID,
  FIELD_STEP,
  initialState,
  reduce,
  type DraftValues,
} from '@/features/portfolio/editor-state';
import { CLAIM_KINDS, CLAIM_STATUSES, labelOf, PROVENANCES, STAGES, TIMINGS, type Invention } from '@/features/portfolio/model';
import { PROVENANCE } from '@/views/parts';

const STEPS = [
  { id: '1', label: 'Dasar' },
  { id: '2', label: 'Yang sudah ada dan bukti' },
  { id: '3', label: 'Dukungan dan cakupan keuangan' },
  { id: '4', label: 'Pratinjau publik' },
];

type EditorViewProps = {
  me: Me;
  invention: Invention;
  initialStep: number;
  /** Step 2's document area; spec 012 fills it. */
  documents?: ReactNode;
};

/**
 * S05: four steps. Values survive step changes, Back, failed saves and stale versions (UX-03). Every save sends
 * `expected_version` and an idempotency key; a retry of the same save reuses its key.
 */
export function EditorView({ me, invention, initialStep, documents }: EditorViewProps) {
  const router = useRouter();
  const persona = readPersona(me.account.persona) ?? 'inovator';
  const [state, dispatch] = useReducer(reduce, invention, initialState);
  const [step, setStep] = useState(Math.min(Math.max(initialStep, 1), 4));
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [summaryKey, setSummaryKey] = useState(0);
  const [failure, setFailure] = useState<string | null>(null);
  const [publishing, setPublishing] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const moved = useRef(false);
  const publishKey = useRef<string | null>(null);
  const values = state.values;
  const nextNumber = invention.draft?.number ?? (invention.published ? invention.published.number + 1 : 1);

  useEffect(() => {
    if (moved.current) heading.current?.focus();
    moved.current = false;
  }, [step]);

  /** Changes step; focus moves to the new heading unless an error summary is about to take it. */
  function goTo(next: number, focusHeading = true) {
    moved.current = focusHeading;
    setStep(next);
    window.history.replaceState(null, '', `?step=${next}`);
  }

  function edit(patch: Partial<DraftValues>) {
    publishKey.current = null;
    dispatch({ type: 'edit', values: { ...values, ...patch } });
  }

  /** Saves the draft; returns the new invention version, or null after a failure or conflict. */
  async function save(): Promise<number | null> {
    const key = state.pendingKey ?? newIdempotencyKey();
    dispatch({ type: 'save', key });
    try {
      const saved = await saveDraft(invention.id, draftRequest(values, state.version, me.active_party_id), key);
      dispatch({ type: 'saved', version: saved.version });
      return saved.version;
    } catch (error) {
      const apiError = ApiError.from(error);
      if (apiError.code === 'STALE_VERSION') dispatch({ type: 'conflict', currentVersion: apiError.currentVersion ?? 0 });
      else dispatch({ type: 'failed' });
      return null;
    }
  }

  async function saveAndContinue() {
    if ((await save()) !== null) goTo(step + 1);
  }

  async function reload() {
    try {
      dispatch({ type: 'reloaded', invention: await readInvention(invention.id) });
    } catch {
      dispatch({ type: 'failed' });
    }
  }

  async function publish() {
    if (publishing) return;
    setPublishing(true);
    setFailure(null);
    const version = state.status === 'saved' ? state.version : await save();
    if (version === null) {
      setPublishing(false);
      return;
    }
    publishKey.current ??= newIdempotencyKey();
    try {
      const result = await publishInvention(invention.id, me.active_party_id, version, publishKey.current);
      router.push(`/inventions/${invention.id}?terbit=${result.version}`);
      router.refresh();
    } catch (error) {
      const apiError = ApiError.from(error);
      setPublishing(false);
      publishKey.current = null;
      if (apiError.code === 'VALIDATION_FAILED' && apiError.details.length) {
        const found = Object.fromEntries(apiError.details.map((detail) => [String(detail.loc[1]), detail.msg]));
        setErrors(found);
        setSummaryKey((count) => count + 1);
        goTo(Math.min(...Object.keys(found).map((field) => FIELD_STEP[field] ?? 1)), false);
      } else {
        setFailure(apiError.message);
        setSummaryKey((count) => count + 1);
      }
    }
  }

  const summary = Object.entries(errors).map(([field, message]) => ({ fieldId: FIELD_ID[field] ?? field, message }));
  const current = STEPS[step - 1];

  return (
    <Screen
      persona={persona}
      current={persona === 'inovator' ? 'inovasi' : undefined}
      title={values.title || 'Inovasi tanpa judul'}
      subtitle="Simpan kapan saja; aturan terbit hanya berlaku saat menerbitkan."
      provenance={PROVENANCE}
      context={<ContextBar me={me} />}>
      <Steps steps={STEPS} current={String(step)} onSelect={(id) => goTo(Number(id))} />
      <SaveState state={state.status} onRetry={save} />
      {state.status === 'conflict' ? (
        <VersionConflict
          what="Draf ini sudah disimpan dari tab atau perangkat lain sejak Anda membukanya."
          currentVersion={state.currentVersion ? String(state.currentVersion) : undefined}
          draft={values.title || values.summary || 'Isian Anda masih ada di halaman ini.'}
          onRefresh={reload}
        />
      ) : null}
      {summary.length || failure ? (
        <ErrorSummary errors={summary} focusKey={summaryKey}>
          {failure}
        </ErrorSummary>
      ) : null}
      <section className="tr-panel tr-stack" aria-labelledby="judul-langkah">
        <h2 id="judul-langkah" ref={heading} tabIndex={-1} className="tr-sys-type-heading-md">
          {current.label}
        </h2>
        {step === 1 ? <BasicsStep values={values} errors={errors} edit={edit} /> : null}
        {step === 2 ? <EvidenceStep values={values} errors={errors} edit={edit} hasDocuments={Boolean(documents)} /> : null}
        {/* Kept mounted on every step, so a transfer continues while the person moves on. */}
        {documents ? (
          <div hidden={step !== 2} className="tr-stack">
            <h3 className="tr-sys-type-heading-sm">Dokumen bukti</h3>
            {documents}
          </div>
        ) : null}
        {step === 3 ? (
          <Status tone="neutral" label="Segera hadir">
            <p>Kebutuhan dukungan dan cakupan keuangan akan diisi di langkah ini. Tidak ada yang perlu diisi sekarang.</p>
          </Status>
        ) : null}
        {step === 4 ? <PreviewStep values={values} manager={me} number={nextNumber} /> : null}
        <div className="tr-row">
          {step > 1 ? (
            <Button icon="left" onClick={() => goTo(step - 1)}>
              Kembali
            </Button>
          ) : null}
          {step < 4 ? (
            <Button intent="primary" icon="arrow" busy={state.status === 'saving'} busyLabel="Menyimpan…" onClick={saveAndContinue}>
              Simpan dan lanjutkan
            </Button>
          ) : (
            <>
              <ContextSwitcher readOnly value={me.active_party_id} options={contextOptions(me)} actionLabel="Diterbitkan atas nama" />
              <Button intent="primary" busy={publishing} busyLabel="Menerbitkan…" onClick={publish}>
                {`Terbitkan versi ${nextNumber}`}
              </Button>
            </>
          )}
        </div>
      </section>
    </Screen>
  );
}

type StepProps = { values: DraftValues; errors: Record<string, string>; edit: (patch: Partial<DraftValues>) => void };

function BasicsStep({ values, errors, edit }: StepProps) {
  return (
    <div className="tr-stack">
      <TextField id="judul" label="Judul" hint="5 sampai 120 karakter." value={values.title} onChange={(title) => edit({ title })} error={errors.title} required />
      <TextArea id="ringkasan" label="Ringkasan" limit={350} rows={3} value={values.summary} onChange={(summary) => edit({ summary })} error={errors.summary} />
      <TextArea id="masalah" label="Masalah yang diselesaikan" value={values.problem} onChange={(problem) => edit({ problem })} error={errors.problem} required />
      <TextArea id="solusi" label="Solusi saat ini" value={values.solution} onChange={(solution) => edit({ solution })} error={errors.solution} required />
      <TextField id="pengguna" label="Siapa penggunanya" value={values.intended_users} onChange={(intended_users) => edit({ intended_users })} error={errors.intended_users} required />
      <TextField id="sektor" label="Sektor" value={values.sector} onChange={(sector) => edit({ sector })} />
      <Select id="tahap" label="Tahap inovasi" value={values.stage} onChange={(stage) => edit({ stage })} options={STAGES} error={errors.stage} required />
      <TextField id="kata-kunci" label="Kata kunci" hint="Pisahkan dengan koma." value={values.keywords} onChange={(keywords) => edit({ keywords })} />
    </div>
  );
}

function EvidenceStep({ values, errors, edit, hasDocuments }: StepProps & { hasDocuments: boolean }) {
  function setFact(index: number, patch: Partial<DraftValues['facts'][number]>) {
    edit({ facts: values.facts.map((fact, position) => (position === index ? { ...fact, ...patch } : fact)) });
  }
  function setClaim(index: number, patch: Partial<DraftValues['claims'][number]>) {
    edit({ claims: values.claims.map((claim, position) => (position === index ? { ...claim, ...patch } : claim)) });
  }
  const facts = values.facts.length ? values.facts : [];
  return (
    <div className="tr-stack">
      <h3 className="tr-sys-type-heading-sm">Fakta</h3>
      <p className="tr-muted">Pisahkan yang sudah ada saat ini dari yang direncanakan, dan sebutkan siapa yang menyatakannya.</p>
      {errors.facts ? (
        <Status tone="danger" icon="alert" label={errors.facts} />
      ) : null}
      {facts.map((fact, index) => (
        <fieldset key={index} className="tr-fieldset tr-stack">
          <legend className="tr-field__label tr-sys-type-label">{`Fakta ${index + 1}`}</legend>
          <TextField id={`fakta-${index}-label`} label="Apa yang diukur" value={fact.label} onChange={(label) => setFact(index, { label })} />
          <TextField id={`fakta-${index}-nilai`} label="Nilai" value={fact.value} onChange={(value) => setFact(index, { value })} />
          <TextField id={`fakta-${index}-satuan`} label="Satuan" value={fact.unit ?? ''} onChange={(unit) => setFact(index, { unit })} />
          <Select id={`fakta-${index}-waktu`} label="Kapan" value={fact.timing} onChange={(timing) => setFact(index, { timing: timing as typeof fact.timing })} options={TIMINGS} emptyLabel={null} />
          <Select id={`fakta-${index}-sumber`} label="Sumber" value={fact.provenance ?? 'SELF_DECLARED'} onChange={(provenance) => setFact(index, { provenance: provenance as typeof fact.provenance })} options={PROVENANCES} emptyLabel={null} />
          <div className="tr-row">
            <Button onClick={() => edit({ facts: values.facts.filter((_, position) => position !== index) })}>
              Hapus fakta<span className="tr-sr">{` ${index + 1}`}</span>
            </Button>
          </div>
        </fieldset>
      ))}
      <div className="tr-row">
        <Button icon="check" onClick={() => edit({ facts: [...values.facts, { ...EMPTY_FACT }] })}>
          Tambah fakta
        </Button>
      </div>
      <h3 className="tr-sys-type-heading-sm">Orang dan hak</h3>
      <p className="tr-muted">Klaim bukan sertifikat. Pencipta, pemegang hak, dan kewenangan bertindak dicatat terpisah.</p>
      {values.claims.map((claim, index) => (
        <fieldset key={index} className="tr-fieldset tr-stack">
          <legend className="tr-field__label tr-sys-type-label">{`Klaim ${index + 1}`}</legend>
          <Select id={`klaim-${index}-jenis`} label="Jenis" value={claim.kind} onChange={(kind) => setClaim(index, { kind: kind as typeof claim.kind })} options={CLAIM_KINDS} emptyLabel={null} />
          <TextField id={`klaim-${index}-nama`} label="Nama" value={claim.subject_name} onChange={(subject_name) => setClaim(index, { subject_name })} />
          <TextField id={`klaim-${index}-cakupan`} label="Cakupan" value={claim.scope ?? ''} onChange={(scope) => setClaim(index, { scope })} />
          <Select id={`klaim-${index}-status`} label="Status" value={claim.status ?? 'asserted'} onChange={(status) => setClaim(index, { status: status as typeof claim.status })} options={CLAIM_STATUSES} emptyLabel={null} />
          <TextField id={`klaim-${index}-sumber`} label="Sumber" value={claim.source ?? ''} onChange={(source) => setClaim(index, { source })} />
          <div className="tr-row">
            <Button onClick={() => edit({ claims: values.claims.filter((_, position) => position !== index) })}>
              Hapus klaim<span className="tr-sr">{` ${index + 1}`}</span>
            </Button>
          </div>
        </fieldset>
      ))}
      <div className="tr-row">
        <Button onClick={() => edit({ claims: [...values.claims, { ...EMPTY_CLAIM }] })}>Tambah klaim</Button>
      </div>
      {hasDocuments ? null : (
        <>
          <h3 className="tr-sys-type-heading-sm">Dokumen bukti</h3>
          <Status tone="neutral" label="Segera hadir">
            <p>Dokumen bukti dapat diunggah di langkah ini segera. Dokumen selalu privat sampai Anda membagikannya.</p>
          </Status>
        </>
      )}
      <TextArea
        id="catatan"
        label="Catatan pribadi"
        hint="Tidak pernah ditampilkan kepada siapa pun dan tidak ikut terbit."
        value={values.private_notes}
        onChange={(private_notes) => edit({ private_notes })}
        rows={3}
      />
    </div>
  );
}

function PreviewStep({ values, manager, number }: { values: DraftValues; manager: Me; number: number }) {
  const facts = values.facts.filter((fact) => fact.label && fact.value);
  return (
    <div className="tr-stack">
      <p>Ini yang akan dilihat pengguna lain setelah terbit.</p>
      <InventionCard
        title={values.title || 'Inovasi tanpa judul'}
        category={values.sector}
        manager={`Dikelola ${manager.organizations?.find((item) => item.party_id === manager.active_party_id)?.name ?? manager.account.display_name}`}
        problem={values.problem}
        solution={values.solution}
        maturity={labelOf(STAGES, values.stage)}
        facts={
          facts.length ? (
            <ul className="tr-stack">
              {facts.map((fact, index) => (
                <li key={index}>
                  {`${fact.label}: `}
                  <FactSource value={`${fact.value} ${fact.unit ?? ''}`.trim()} timing={fact.timing} provenance={fact.provenance ?? undefined} />
                </li>
              ))}
            </ul>
          ) : null
        }
      />
      <section className="tr-stack" aria-labelledby="tetap-privat">
        <h3 id="tetap-privat" className="tr-sys-type-heading-sm">
          Yang tetap privat
        </h3>
        <ul className="tr-reasons">
          <li>Catatan pribadi</li>
          <li>Dokumen bukti, kecuali yang Anda bagikan per pitching</li>
          <li>Draf perubahan berikutnya</li>
        </ul>
      </section>
      <section className="tr-stack" aria-labelledby="akibat-terbit">
        <h3 id="akibat-terbit" className="tr-sys-type-heading-sm">
          Akibat menerbitkan
        </h3>
        <p>{`Versi ${number} dapat dilihat semua pengguna yang masuk. Versi ini tidak berubah lagi; perubahan berikutnya menjadi draf baru.`}</p>
      </section>
    </div>
  );
}

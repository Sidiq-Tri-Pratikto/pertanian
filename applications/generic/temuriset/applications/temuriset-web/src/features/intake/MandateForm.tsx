'use client';

import NextLink from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';

import { newIdempotencyKey } from '@/api/client';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Checkbox, CheckboxGroup } from '@/components/tr/Checkbox';
import { ErrorSummary } from '@/components/tr/ErrorSummary';
import { FinancialScope } from '@/components/tr/FinancialScope';
import { RequirementRow } from '@/components/tr/RequirementRow';
import { SaveState } from '@/components/tr/SaveState';
import { Select } from '@/components/tr/Select';
import { TextArea } from '@/components/tr/TextArea';
import { TextField } from '@/components/tr/TextField';
import { VersionConflict } from '@/components/tr/VersionConflict';
import { moveMandate, readMandate, saveMandate } from '@/features/intake/api';
import {
  APPLIES_AT,
  DOCUMENT_KINDS,
  RELATIONSHIP_FORMS,
  REQUIREMENT_KINDS,
  VERIFICATION_MODES,
  rangeBody,
  rangeValues,
  scopeProps,
  splitList,
  type Financial,
  type Mandate,
  type RangeValues,
} from '@/features/intake/model';
import { rangeErrorIds, RangeFields } from '@/features/intake/RangeFields';
import { fieldErrors } from '@/features/needs/model';
import { labelOf, STAGES } from '@/features/portfolio/model';
import { MandateReview } from '@/views/intake/MandateReview';

type Row = {
  rowId: number;
  label: string;
  field: string;
  operator: string;
  value: unknown;
  mandatory: boolean;
  applies_at: string;
  verification_mode: string;
  visibility: string;
  reason: string;
};

type Values = {
  title: string;
  outcome: string;
  included: string;
  excluded: string;
  support: string;
  timing: string;
  accepted_stages: string[];
  relationship_forms: string[];
  sectors: string;
  keywords: string;
  range: RangeValues;
  scope: string;
  noncash: string;
  terms: string;
  requirements: Row[];
};

type NewRow = {
  kind: string;
  label: string;
  reason: string;
  applies_at: string;
  verification_mode: string;
  stages: string[];
  relationship: string;
  document: string;
  feature: string;
};

const EMPTY_NEW_ROW: NewRow = {
  kind: 'narrative',
  label: '',
  reason: '',
  applies_at: 'SUBMISSION',
  verification_mode: 'DECLARATION',
  stages: [],
  relationship: 'PROJECT',
  document: 'function',
  feature: '',
};

const IDS: Record<string, string> = {
  ...rangeErrorIds('financial', 'm'),
  financial: 'm-subject',
  title: 'm-title',
  outcome: 'm-outcome',
  included: 'm-included',
  excluded: 'm-excluded',
  support: 'm-support',
  timing: 'm-timing',
  accepted_stages: 'm-stages',
  relationship_forms: 'm-forms',
  partner_profile: 'm-profile',
};

function initialValues(mandate: Mandate): Values {
  return {
    title: mandate.title,
    outcome: mandate.outcome,
    included: mandate.included,
    excluded: mandate.excluded,
    support: mandate.support,
    timing: mandate.timing,
    accepted_stages: [...mandate.accepted_stages],
    relationship_forms: [...mandate.relationship_forms],
    sectors: mandate.sectors.join(', '),
    keywords: mandate.keywords.join(', '),
    range: rangeValues(mandate.financial, 'partner'),
    scope: mandate.financial?.scope ?? '',
    noncash: mandate.financial?.noncash ?? '',
    terms: mandate.financial?.terms ?? '',
    requirements: mandate.requirements.map(({ label, field, operator, value, mandatory, applies_at, verification_mode, visibility, reason }, rowId) => ({
      rowId,
      label,
      field,
      operator,
      value,
      mandatory,
      applies_at,
      verification_mode,
      visibility,
      reason,
    })),
  };
}

function financialBody(values: Values) {
  const stated = values.range.min.trim() || values.range.max.trim() || values.range.unknown_reason || values.noncash.trim() || values.terms.trim() || values.scope.trim();
  return stated ? { ...rangeBody(values.range), scope: values.scope, noncash: values.noncash, terms: values.terms } : null;
}

function bodyOf(values: Values, mandate: Mandate, actingPartyId: string) {
  return {
    acting_party_id: actingPartyId,
    expected_version: mandate.version,
    title: values.title,
    outcome: values.outcome,
    included: values.included,
    excluded: values.excluded,
    support: values.support,
    timing: values.timing,
    accepted_stages: values.accepted_stages,
    relationship_forms: values.relationship_forms,
    sectors: splitList(values.sectors),
    keywords: splitList(values.keywords),
    financial: financialBody(values),
    // No control sets the closing time yet, so a save keeps what is stored.
    closes_at: mandate.closes_at,
    requirements: values.requirements.map(({ label, field, operator, value, mandatory, applies_at, verification_mode, visibility, reason }) => ({
      label,
      field,
      operator,
      value,
      mandatory,
      applies_at,
      verification_mode,
      visibility,
      reason,
    })),
  };
}

/** Turns the add-a-requirement fields into the typed row the service validates, or says what is missing. */
function typedRow(row: NewRow): { field: string; operator: string; value: unknown; mandatory: boolean } | string {
  switch (row.kind) {
    case 'stage':
      return row.stages.length ? { field: 'stage', operator: 'in_set', value: row.stages, mandatory: true } : 'Pilih tahap yang dipersyaratkan.';
    case 'relationship':
      return { field: 'relationship', operator: 'equals', value: row.relationship, mandatory: true };
    case 'document':
      return { field: `document:${row.document}`, operator: 'exists', value: true, mandatory: true };
    case 'feature': {
      const name = row.feature.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
      return name ? { field: `feature:${name}`, operator: 'equals', value: 'CURRENT', mandatory: true } : 'Isi nama fitur.';
    }
    case 'budget':
    case 'contribution':
      return { field: row.kind, operator: 'range_overlap', value: null, mandatory: true };
    case 'authority':
      return { field: 'authority', operator: 'equals', value: 'REVIEWED', mandatory: true };
    case 'entity':
      return { field: 'entity', operator: 'equals', value: 'IDENTIFIED', mandatory: true };
    default:
      return { field: 'narrative', operator: 'manual_review', value: null, mandatory: false };
  }
}

const MANUAL_REVIEW_TAG = <span className="tr-tag tr-sys-type-support">Ditinjau manual</span>;

type Props = { mandate: Mandate; actingPartyId: string };

/** S09: edit, review, then activate. Reviewing saves nothing; every failure keeps what the person typed. */
export function MandateForm({ mandate: initial, actingPartyId }: Props) {
  const router = useRouter();
  const [mandate, setMandate] = useState(initial);
  const [values, setValues] = useState(() => initialValues(initial));
  const [newRow, setNewRow] = useState(EMPTY_NEW_ROW);
  const [newRowError, setNewRowError] = useState<string | null>(null);
  const [reviewing, setReviewing] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [failure, setFailure] = useState<ApiError | null>(null);
  const [conflict, setConflict] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'failed'>('idle');
  const [activating, setActivating] = useState(false);
  // The content is already saved and only activation is left, so a retry must not create another version.
  const [staged, setStaged] = useState(false);
  const [saveKey, setSaveKey] = useState(newIdempotencyKey);
  const moveKey = useRef<string | null>(null);
  const nextRowId = useRef(initial.requirements.length);
  const reviewHeading = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    if (reviewing) reviewHeading.current?.focus();
  }, [reviewing]);

  function change(patch: Partial<Values>) {
    setValues((current) => ({ ...current, ...patch }));
    setSaveState((current) => (current === 'saved' ? 'idle' : current));
    setStaged(false);
    setSaveKey(newIdempotencyKey());
  }
  const edit = (field: 'title' | 'outcome' | 'included' | 'excluded' | 'support' | 'timing' | 'sectors' | 'keywords' | 'scope' | 'noncash' | 'terms') => (value: string) => change({ [field]: value });
  const toggle = (field: 'accepted_stages' | 'relationship_forms', value: string) => (checked: boolean) =>
    change({ [field]: checked ? [...values[field], value] : values[field].filter((item) => item !== value) });
  const editRow = (rowId: number, patch: Partial<Row>) => change({ requirements: values.requirements.map((row) => (row.rowId === rowId ? { ...row, ...patch } : row)) });

  function addRow() {
    if (!newRow.label.trim()) {
      setNewRowError('Isi nama syarat.');
      return;
    }
    const typed = typedRow(newRow);
    if (typeof typed === 'string') {
      setNewRowError(typed);
      return;
    }
    const row: Row = {
      rowId: nextRowId.current,
      label: newRow.label.trim(),
      ...typed,
      applies_at: newRow.applies_at,
      verification_mode: newRow.verification_mode,
      visibility: 'PUBLIC',
      reason: newRow.reason,
    };
    nextRowId.current += 1;
    change({ requirements: [...values.requirements, row] });
    setNewRow(EMPTY_NEW_ROW);
    setNewRowError(null);
  }

  function fail(error: unknown) {
    const apiError = ApiError.from(error);
    // Only a request that may not have arrived is retried with the same key; anything the service refused is not.
    if (!apiError.recovery.retryable) {
      setSaveKey(newIdempotencyKey());
      moveKey.current = null;
    }
    if (apiError.code === 'STALE_VERSION') {
      setConflict(true);
      setFailure(null);
      setErrors({});
      return;
    }
    const rowIds = Object.fromEntries(values.requirements.map((_, index) => [`requirements.${index}`, `m-req-reason-${index}`]));
    const found = apiError.code === 'VALIDATION_FAILED' ? fieldErrors(apiError, { ...IDS, ...rowIds }) : {};
    setErrors(found);
    setFailure(apiError);
    if (Object.keys(found).length) setReviewing(false);
    setAttempt((current) => current + 1);
  }

  async function saveDraft() {
    if (saveState === 'saving') return;
    setSaveState('saving');
    try {
      setMandate(await saveMandate(mandate.id, bodyOf(values, mandate, actingPartyId), saveKey));
      setSaveKey(newIdempotencyKey());
      setErrors({});
      setFailure(null);
      setConflict(false);
      setSaveState('saved');
    } catch (error) {
      fail(error);
      setSaveState('failed');
    }
  }

  async function activate() {
    if (activating) return;
    setActivating(true);
    setFailure(null);
    try {
      let current = mandate;
      if (!staged) {
        current = await saveMandate(mandate.id, bodyOf(values, mandate, actingPartyId), saveKey);
        setSaveKey(newIdempotencyKey());
        setMandate(current);
        setStaged(current.status !== 'ACTIVE');
      }
      if (current.status !== 'ACTIVE') {
        moveKey.current ??= newIdempotencyKey();
        await moveMandate(current.id, 'activate', actingPartyId, current.version, moveKey.current);
        moveKey.current = null;
      }
      router.push(`/opportunities?aktif=${current.number}`);
    } catch (error) {
      fail(error);
      setActivating(false);
    }
  }

  async function useLatest() {
    try {
      setMandate(await readMandate(mandate.id));
      setConflict(false);
      setStaged(false);
      setFailure(null);
      setSaveKey(newIdempotencyKey());
      moveKey.current = null;
    } catch (error) {
      setFailure(ApiError.from(error));
      setAttempt((current) => current + 1);
    }
  }

  const summary = Object.entries(errors).map(([fieldId, message]) => ({ fieldId, message }));
  const nextNumber = staged || mandate.status === 'DRAFT' ? mandate.number : mandate.number + 1;
  const financial = financialBody(values);
  return (
    <div className="tr-stack">
      {failure ? (
        <ErrorSummary errors={summary} focusKey={attempt} title={failure.code === 'VALIDATION_FAILED' ? undefined : 'Mandat belum tersimpan'}>
          {summary.length ? null : `${failure.message} Kode rujukan: ${failure.requestId ?? '-'}.`}
        </ErrorSummary>
      ) : null}
      {conflict ? (
        <VersionConflict what="Mandat ini sudah diubah di tempat lain. Isian Anda belum hilang." draft={values.title} onRefresh={useLatest} refreshLabel="Pakai versi terbaru, pertahankan isian saya" />
      ) : null}
      {errors['m-profile'] ? (
        <p id="m-profile" tabIndex={-1}>
          <NextLink className="tr-link" href={`/partners/${mandate.partner_party_id}`}>
            Buka profil mitra
          </NextLink>
        </p>
      ) : null}
      {reviewing ? (
        <section className="tr-stack" aria-labelledby="tinjau-mandat">
          <h2 id="tinjau-mandat" ref={reviewHeading} tabIndex={-1} className="tr-sys-type-heading-sm">
            Tinjau mandat
          </h2>
          <div className="tr-panel">
            <MandateReview
              values={{
                title: values.title,
                outcome: values.outcome,
                included: values.included,
                excluded: values.excluded,
                support: values.support,
                stages: values.accepted_stages.map((stage) => labelOf(STAGES, stage)).join(', '),
                forms: values.relationship_forms.map((form) => labelOf(RELATIONSHIP_FORMS, form)).join(', '),
                timing: values.timing,
                financial: financial ? <FinancialScope compact {...scopeProps(financial as unknown as Financial)} /> : null,
                requirements: values.requirements.map((row) => row.label),
              }}
            />
          </div>
          <div className="tr-row">
            <Button intent="primary" icon="check" busy={activating} busyLabel="Mengaktifkan…" onClick={activate}>
              {`Aktifkan versi ${nextNumber}`}
            </Button>
            <Button onClick={() => setReviewing(false)}>Kembali mengubah</Button>
          </div>
        </section>
      ) : (
        <>
          <section className="tr-panel tr-stack" aria-labelledby="isi-mandat">
            <h2 id="isi-mandat" className="tr-sys-type-heading-sm">
              Isi mandat
            </h2>
            <TextField id="m-title" label="Judul mandat" value={values.title} onChange={edit('title')} error={errors['m-title']} />
            <TextArea id="m-outcome" label="Hasil yang dicari" rows={2} value={values.outcome} onChange={edit('outcome')} error={errors['m-outcome']} />
            <TextArea id="m-included" label="Termasuk" rows={2} value={values.included} onChange={edit('included')} error={errors['m-included']} />
            <TextArea id="m-excluded" label="Tidak termasuk" rows={2} value={values.excluded} onChange={edit('excluded')} error={errors['m-excluded']} />
            <TextField id="m-support" label="Dukungan yang ditawarkan" value={values.support} onChange={edit('support')} error={errors['m-support']} />
            <TextField id="m-timing" label="Waktu penerimaan" hint="Misalnya: Dibuka sampai 31 Desember 2026." value={values.timing} onChange={edit('timing')} error={errors['m-timing']} />
            <CheckboxGroup id="m-stages" legend="Tahap yang diterima" error={errors['m-stages']}>
              {STAGES.map((stage) => (
                <Checkbox key={stage.value} label={stage.label} checked={values.accepted_stages.includes(stage.value)} onChange={toggle('accepted_stages', stage.value)} />
              ))}
            </CheckboxGroup>
            <CheckboxGroup id="m-forms" legend="Bentuk kerja sama" error={errors['m-forms']}>
              {RELATIONSHIP_FORMS.map((form) => (
                <Checkbox key={form.value} label={form.label} checked={values.relationship_forms.includes(form.value)} onChange={toggle('relationship_forms', form.value)} />
              ))}
            </CheckboxGroup>
            <TextField label="Sektor" hint="Pisahkan dengan koma." value={values.sectors} onChange={edit('sectors')} />
            <TextField label="Kata kunci" hint="Pisahkan dengan koma." value={values.keywords} onChange={edit('keywords')} />
          </section>
          <section className="tr-panel tr-stack" aria-labelledby="keuangan-mandat">
            <h2 id="keuangan-mandat" className="tr-sys-type-heading-sm">
              Dasar keuangan
            </h2>
            <p className="tr-muted">Isi kisaran, dukungan nontunai atau ketentuan. Belum ditentukan tidak pernah dianggap nol.</p>
            <RangeFields prefix="m" subjectLabel="Dasar keuangan" values={values.range} onChange={(field, value) => change({ range: { ...values.range, [field]: value } })} errors={errors} />
            <TextField label="Cakupan" hint="Misalnya: biaya pilot enam bulan." value={values.scope} onChange={edit('scope')} />
            <TextField label="Dukungan nontunai" value={values.noncash} onChange={edit('noncash')} />
            <TextField label="Ketentuan" hint="Misalnya: ketentuan lisensi." value={values.terms} onChange={edit('terms')} />
          </section>
          <section className="tr-stack" aria-labelledby="syarat-mandat">
            <h2 id="syarat-mandat" className="tr-sys-type-heading-sm">
              Syarat
            </h2>
            <p className="tr-muted">Syarat wajib terlihat oleh pengirim beserta alasannya. Tidak ada syarat tersembunyi yang menolak otomatis.</p>
            {values.requirements.map((row, index) => (
              <div key={row.rowId} className="tr-panel tr-stack" data-requirement>
                <ul>
                  <RequirementRow
                    headingLevel={3}
                    label={row.label}
                    result="NOT_APPLICABLE"
                    stage={row.applies_at}
                    mandatory={row.mandatory}
                    mode={row.verification_mode}
                    action={row.operator === 'manual_review' ? MANUAL_REVIEW_TAG : undefined}
                  />
                </ul>
                <Select label={`Tahap berlaku: ${row.label}`} value={row.applies_at} onChange={(value) => editRow(row.rowId, { applies_at: value })} options={APPLIES_AT} emptyLabel={null} />
                <Select label={`Cara pemeriksaan: ${row.label}`} value={row.verification_mode} onChange={(value) => editRow(row.rowId, { verification_mode: value })} options={VERIFICATION_MODES} emptyLabel={null} />
                <TextArea id={`m-req-reason-${index}`} label={`Alasan: ${row.label}`} rows={2} value={row.reason} onChange={(value) => editRow(row.rowId, { reason: value })} error={errors[`m-req-reason-${index}`]} />
                <div className="tr-row">
                  <Button onClick={() => change({ requirements: values.requirements.filter((item) => item.rowId !== row.rowId) })}>{`Hapus syarat ${row.label}`}</Button>
                </div>
              </div>
            ))}
            <div className="tr-panel tr-stack">
              <Select label="Jenis syarat" value={newRow.kind} onChange={(kind) => setNewRow({ ...newRow, kind })} options={REQUIREMENT_KINDS} emptyLabel={null} />
              <TextField label="Syarat baru" hint="Syarat naratif tanpa pemetaan ditinjau manual dan tidak menolak otomatis." value={newRow.label} onChange={(label) => setNewRow({ ...newRow, label })} error={newRowError} />
              {newRow.kind === 'stage' ? (
                <CheckboxGroup id="m-new-stages" legend="Tahap yang dipersyaratkan">
                  {STAGES.map((stage) => (
                    <Checkbox
                      key={stage.value}
                      label={stage.label}
                      checked={newRow.stages.includes(stage.value)}
                      onChange={(checked) => setNewRow({ ...newRow, stages: checked ? [...newRow.stages, stage.value] : newRow.stages.filter((item) => item !== stage.value) })}
                    />
                  ))}
                </CheckboxGroup>
              ) : null}
              {newRow.kind === 'relationship' ? <Select label="Bentuk yang dipersyaratkan" value={newRow.relationship} onChange={(relationship) => setNewRow({ ...newRow, relationship })} options={RELATIONSHIP_FORMS} emptyLabel={null} /> : null}
              {newRow.kind === 'document' ? <Select label="Jenis berkas" value={newRow.document} onChange={(document) => setNewRow({ ...newRow, document })} options={DOCUMENT_KINDS} emptyLabel={null} /> : null}
              {newRow.kind === 'feature' ? <TextField label="Nama fitur" hint="Fitur yang harus sudah berjalan, bukan rencana." value={newRow.feature} onChange={(feature) => setNewRow({ ...newRow, feature })} /> : null}
              <TextArea label="Alasan syarat baru" rows={2} value={newRow.reason} onChange={(reason) => setNewRow({ ...newRow, reason })} />
              <Select label="Tahap berlaku" value={newRow.applies_at} onChange={(applies_at) => setNewRow({ ...newRow, applies_at })} options={APPLIES_AT} emptyLabel={null} />
              <Select label="Cara pemeriksaan" value={newRow.verification_mode} onChange={(verification_mode) => setNewRow({ ...newRow, verification_mode })} options={VERIFICATION_MODES} emptyLabel={null} />
              <div className="tr-row">
                <Button onClick={addRow}>Tambah syarat</Button>
              </div>
            </div>
          </section>
          {saveState !== 'idle' ? <SaveState state={saveState === 'failed' && conflict ? 'conflict' : saveState} onRetry={saveDraft} /> : null}
          <div className="tr-row">
            <Button intent="primary" icon="arrow" onClick={() => setReviewing(true)}>
              Tinjau mandat
            </Button>
            {mandate.status === 'DRAFT' ? (
              <Button icon="check" busy={saveState === 'saving'} busyLabel="Menyimpan…" onClick={saveDraft}>
                Simpan draf
              </Button>
            ) : null}
          </div>
        </>
      )}
    </div>
  );
}

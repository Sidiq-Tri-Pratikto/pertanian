'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { newIdempotencyKey } from '@/api/client';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Checkbox, CheckboxGroup } from '@/components/tr/Checkbox';
import { ErrorSummary } from '@/components/tr/ErrorSummary';
import { SaveState } from '@/components/tr/SaveState';
import { Select } from '@/components/tr/Select';
import { TextArea } from '@/components/tr/TextArea';
import { TextField } from '@/components/tr/TextField';
import { moveSupportRequest, saveSupportRequest } from '@/features/needs/api';
import { BASES, CURRENCIES, fieldErrors, SUPPORT_FORMS, UNKNOWN_REASONS, type SupportRequest } from '@/features/needs/model';

// Where each service field error is shown.
const IDS: Record<string, string> = {
  outcome: 'sr-outcome',
  support_forms: 'sr-forms',
  months: 'sr-months',
  'budget.min': 'sr-min',
  'budget.max': 'sr-max',
  'budget.currency': 'sr-currency',
  'budget.unknown_reason': 'sr-unknown',
  'budget.lines_explanation': 'sr-min',
  'budget.lines': 'sr-min',
};
const ORDER = ['sr-outcome', 'sr-forms', 'sr-months', 'sr-min', 'sr-max', 'sr-currency', 'sr-unknown'];

type Values = {
  outcome: string;
  support_forms: string[];
  scope: string;
  months: string;
  region: string;
  accepts_partial: boolean;
  accepts_noncash: boolean;
  noncash_description: string;
  min: string;
  max: string;
  currency: string;
  basis: string;
  period: string;
  budget_scope: string;
  assumptions: string;
  unknown_reason: string;
};

function initialValues(request: SupportRequest): Values {
  const budget = request.budget;
  return {
    outcome: request.outcome,
    support_forms: [...request.support_forms],
    scope: request.scope,
    months: request.months == null ? '' : String(request.months),
    region: request.region,
    accepts_partial: request.accepts_partial,
    accepts_noncash: request.accepts_noncash,
    noncash_description: request.noncash_description,
    // Stored money comes back as "20000.0000"; the field shows the digits the person typed, without padding.
    min: budget?.min ? budget.min.replace(/\.?0+$/, '') : '',
    max: budget?.max ? budget.max.replace(/\.?0+$/, '') : '',
    currency: budget?.currency ?? '',
    basis: budget?.basis ?? 'total_period',
    period: budget?.period ?? '',
    budget_scope: budget?.scope ?? '',
    assumptions: budget?.assumptions ?? '',
    unknown_reason: budget?.unknown_reason ?? '',
  };
}

function bodyOf(values: Values, request: SupportRequest, actingPartyId: string) {
  const touched = Boolean(request.budget || values.min || values.max || values.currency || values.unknown_reason);
  const budget = request.budget;
  return {
    acting_party_id: actingPartyId,
    expected_version: request.version,
    outcome: values.outcome,
    support_forms: values.support_forms,
    relationship_form: request.relationship_form,
    scope: values.scope,
    months: /^\d+$/.test(values.months.trim()) ? Number(values.months.trim()) : null,
    region: values.region,
    accepts_partial: values.accepts_partial,
    accepts_noncash: values.accepts_noncash,
    noncash_description: values.noncash_description,
    budget: touched
      ? {
          min: values.min.trim() || null,
          max: values.max.trim() || null,
          currency: values.currency || null,
          basis: values.basis,
          period: values.period,
          scope: values.budget_scope,
          estimated_on: budget?.estimated_on ?? null,
          assumptions: values.assumptions,
          unknown_reason: values.unknown_reason || null,
          financial: budget?.financial ?? true,
          lines: (budget?.lines ?? []).map(({ label, quantity, unit_cost, explanation }) => ({ label, quantity, unit_cost, explanation })),
          lines_explanation: budget?.lines_explanation ?? '',
        }
      : null,
  };
}

type Props = {
  request: SupportRequest;
  actingPartyId: string;
  /** A same-site path to go back to after saving, such as the match it was opened from. */
  returnTo?: string | null;
};

/** S06 form: outcome, forms of support and the budget. A failed save keeps every value and the last saved version. */
export function SupportForm({ request: initial, actingPartyId, returnTo }: Props) {
  const router = useRouter();
  const [request, setRequest] = useState(initial);
  const [values, setValues] = useState(() => initialValues(initial));
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [failure, setFailure] = useState<ApiError | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<'idle' | 'saving' | 'saved' | 'failed'>('idle');
  const [key, setKey] = useState(newIdempotencyKey);
  const edit = <Field extends keyof Values>(field: Field) => (value: Values[Field]) => {
    setValues((current) => ({ ...current, [field]: value }));
    setState((current) => (current === 'saved' ? 'idle' : current));
  };

  function fail(error: unknown) {
    const apiError = ApiError.from(error);
    setErrors(apiError.code === 'VALIDATION_FAILED' ? fieldErrors(apiError, IDS) : {});
    setFailure(apiError);
    // Only a request that may not have arrived is retried with the same key; anything the service refused is not.
    if (!apiError.recovery.retryable) setKey(newIdempotencyKey());
    setAttempt((current) => current + 1);
    setState('failed');
  }

  async function save() {
    if (state === 'saving') return;
    setState('saving');
    try {
      const saved = await saveSupportRequest(request.id, bodyOf(values, request, actingPartyId), key);
      setRequest(saved);
      setErrors({});
      setFailure(null);
      setKey(newIdempotencyKey());
      setState('saved');
      if (returnTo) router.push(returnTo);
      else router.refresh();
    } catch (error) {
      fail(error);
    }
  }

  async function activate() {
    try {
      const moved = await moveSupportRequest(request.id, 'activate', actingPartyId, request.version);
      setRequest(moved);
      setFailure(null);
      setErrors({});
      router.refresh();
    } catch (error) {
      fail(error);
    }
  }

  const summary = ORDER.filter((id) => errors[id]).map((id) => ({ fieldId: id, message: errors[id] }));
  const closed = request.status === 'CLOSED' || request.status === 'EXPIRED';
  return (
    <div className="tr-stack">
      {failure ? (
        <ErrorSummary errors={summary} focusKey={attempt} title={failure.code === 'VALIDATION_FAILED' ? undefined : 'Kebutuhan belum tersimpan'}>
          {summary.length ? null : `${failure.message} Kode rujukan: ${failure.requestId ?? '-'}.`}
        </ErrorSummary>
      ) : null}
      <section className="tr-panel tr-stack" aria-labelledby="sr-hasil">
        <h2 id="sr-hasil" className="tr-sys-type-heading-sm">
          Hasil dan bentuk dukungan
        </h2>
        <TextField id="sr-outcome" label="Hasil yang ingin dicapai" hint="Misalnya: Validasi prototipe enam bulan." value={values.outcome} onChange={edit('outcome')} error={errors['sr-outcome']} />
        <CheckboxGroup id="sr-forms" legend="Bentuk dukungan" error={errors['sr-forms']}>
          {SUPPORT_FORMS.map((form) => (
            <Checkbox
              key={form.value}
              label={form.label}
              checked={values.support_forms.includes(form.value)}
              onChange={(checked) =>
                edit('support_forms')(checked ? [...values.support_forms, form.value] : values.support_forms.filter((value) => value !== form.value))
              }
            />
          ))}
        </CheckboxGroup>
        <TextArea label="Cakupan pekerjaan" value={values.scope} onChange={edit('scope')} rows={3} />
        <TextField id="sr-months" label="Durasi (bulan)" type="text" inputMode="numeric" value={values.months} onChange={edit('months')} error={errors['sr-months']} />
        <TextField label="Wilayah" value={values.region} onChange={edit('region')} />
        <Checkbox label="Menerima dukungan sebagian" checked={values.accepts_partial} onChange={edit('accepts_partial')} />
        <Checkbox label="Menerima dukungan nontunai" checked={values.accepts_noncash} onChange={edit('accepts_noncash')} />
        {values.accepts_noncash ? <TextArea label="Dukungan nontunai yang dicari" value={values.noncash_description} onChange={edit('noncash_description')} rows={2} /> : null}
      </section>
      <section className="tr-panel tr-stack" aria-labelledby="sr-biaya">
        <h2 id="sr-biaya" className="tr-sys-type-heading-sm">
          Kisaran biaya
        </h2>
        <p className="tr-muted">Kosongkan biaya minimum dan maksimum bila belum diketahui, lalu pilih alasannya. Belum ditentukan tidak pernah dianggap nol.</p>
        <Select id="sr-currency" label="Mata uang" value={values.currency} onChange={edit('currency')} options={CURRENCIES} error={errors['sr-currency']} />
        <TextField id="sr-min" label="Biaya minimum" type="decimal" hint="Angka tanpa titik ribuan, misalnya 20000." value={values.min} onChange={edit('min')} error={errors['sr-min']} />
        <TextField id="sr-max" label="Biaya maksimum" type="decimal" value={values.max} onChange={edit('max')} error={errors['sr-max']} />
        <Select label="Dasar perhitungan" value={values.basis} onChange={edit('basis')} options={BASES} emptyLabel={null} />
        <TextField label="Periode" hint="Misalnya: 6 bulan." value={values.period} onChange={edit('period')} />
        <TextField label="Cakupan biaya" hint="Misalnya: biaya pilot enam bulan." value={values.budget_scope} onChange={edit('budget_scope')} />
        <TextArea label="Asumsi" value={values.assumptions} onChange={edit('assumptions')} rows={2} />
        <Select id="sr-unknown" label="Bila kisaran belum diketahui" value={values.unknown_reason} onChange={edit('unknown_reason')} options={UNKNOWN_REASONS} emptyLabel="Kisaran sudah diketahui" error={errors['sr-unknown']} />
      </section>
      {state !== 'idle' ? <SaveState state={state === 'failed' && failure?.code === 'STALE_VERSION' ? 'conflict' : state} onRetry={save} /> : null}
      <div className="tr-row">
        <Button intent="primary" icon="check" busy={state === 'saving'} busyLabel="Menyimpan…" onClick={save} disabledReason={closed ? 'Kebutuhan ini sudah ditutup.' : undefined}>
          Simpan kebutuhan
        </Button>
        {request.status === 'DRAFT' || request.status === 'PAUSED' ? (
          <Button icon="arrow" onClick={activate}>
            Aktifkan kebutuhan
          </Button>
        ) : null}
      </div>
    </div>
  );
}

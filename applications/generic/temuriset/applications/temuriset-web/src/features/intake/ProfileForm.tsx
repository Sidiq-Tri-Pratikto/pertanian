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
import { savePartnerProfile } from '@/features/intake/api';
import { CONTACT_ROUTES, INTAKE_CHOICES, RELATIONSHIP_FORMS, rangeBody, rangeValues, splitList, type PartnerProfile, type RangeValues } from '@/features/intake/model';
import { rangeErrorIds, RangeFields } from '@/features/intake/RangeFields';
import { fieldErrors } from '@/features/needs/model';
import { STAGES } from '@/features/portfolio/model';

const IDS: Record<string, string> = {
  ...rangeErrorIds('check_range', 'p'),
  external_url: 'p-url',
  intake_from: 'p-from',
  intake_until: 'p-until',
};

type Values = {
  subtype: string;
  thesis: string;
  sectors: string;
  stages: string[];
  regions: string;
  support_forms: string;
  relationship_forms: string[];
  review_expectations: string;
  range: RangeValues;
  intake_status: string;
  intake_from: string;
  intake_until: string;
  contact_route: string;
  external_url: string;
};

function initialValues(profile: PartnerProfile | null): Values {
  const stored = profile?.availability.intake_status;
  return {
    subtype: profile?.subtype ?? '',
    thesis: profile?.thesis ?? '',
    sectors: profile?.sectors.join(', ') ?? '',
    stages: [...(profile?.stages ?? [])],
    regions: profile?.regions.join(', ') ?? '',
    support_forms: profile?.support_forms.join(', ') ?? '',
    relationship_forms: [...(profile?.relationship_forms ?? [])],
    review_expectations: profile?.review_expectations ?? '',
    range: rangeValues(profile?.check_range, 'investorCheck'),
    // An unconfirmed entry never becomes an open intake unless its owner says so.
    intake_status: !profile || stored === 'OPEN' ? 'OPEN' : 'CLOSED',
    intake_from: profile?.availability.intake_from ?? '',
    intake_until: profile?.availability.intake_until ?? '',
    contact_route: profile?.contact_route ?? 'IN_APP',
    external_url: profile?.external_url ?? '',
  };
}

function bodyOf(values: Values, version: number | null, actingPartyId: string) {
  const { min, max, unknown_reason: unknown } = values.range;
  return {
    acting_party_id: actingPartyId,
    expected_version: version,
    subtype: values.subtype,
    thesis: values.thesis,
    sectors: splitList(values.sectors),
    stages: values.stages,
    regions: splitList(values.regions),
    support_forms: splitList(values.support_forms),
    relationship_forms: values.relationship_forms,
    review_expectations: values.review_expectations,
    check_range: min.trim() || max.trim() || unknown ? rangeBody(values.range) : null,
    intake_status: values.intake_status,
    intake_from: values.intake_from.trim() || null,
    intake_until: values.intake_until.trim() || null,
    contact_route: values.contact_route,
    external_url: values.contact_route === 'EXTERNAL' ? values.external_url.trim() || null : null,
  };
}

type Props = { profile: PartnerProfile | null; partyId: string; actingPartyId: string };

/** S08 form: what a partner states about itself. A failed save keeps every value. */
export function ProfileForm({ profile, partyId, actingPartyId }: Props) {
  const router = useRouter();
  const [values, setValues] = useState(() => initialValues(profile));
  const [version, setVersion] = useState(profile?.version ?? null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [failure, setFailure] = useState<ApiError | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<'idle' | 'saving' | 'saved' | 'failed'>('idle');
  const [key, setKey] = useState(newIdempotencyKey);
  const edit = <Field extends keyof Values>(field: Field) => (value: Values[Field]) => {
    setValues((current) => ({ ...current, [field]: value }));
    setState((current) => (current === 'saved' ? 'idle' : current));
  };
  const toggle = (field: 'stages' | 'relationship_forms', value: string) => (checked: boolean) =>
    edit(field)(checked ? [...values[field], value] : values[field].filter((item) => item !== value));

  async function save() {
    if (state === 'saving') return;
    setState('saving');
    try {
      const saved = await savePartnerProfile(partyId, bodyOf(values, version, actingPartyId), key);
      setVersion(saved.version);
      setErrors({});
      setFailure(null);
      setKey(newIdempotencyKey());
      setState('saved');
      router.refresh();
    } catch (error) {
      const apiError = ApiError.from(error);
      setErrors(apiError.code === 'VALIDATION_FAILED' ? fieldErrors(apiError, IDS) : {});
      setFailure(apiError);
      // Only a request that may not have arrived is retried with the same key; anything the service refused is not.
      if (!apiError.recovery.retryable) setKey(newIdempotencyKey());
      setAttempt((current) => current + 1);
      setState('failed');
    }
  }

  const summary = Object.entries(errors).map(([fieldId, message]) => ({ fieldId, message }));
  return (
    <div id="profil-mitra" className="tr-stack">
      {failure ? (
        <ErrorSummary errors={summary} focusKey={attempt} title={failure.code === 'VALIDATION_FAILED' ? undefined : 'Profil belum tersimpan'}>
          {summary.length ? null : `${failure.message} Kode rujukan: ${failure.requestId ?? '-'}.`}
        </ErrorSummary>
      ) : null}
      <TextField label="Jenis mitra" hint="Misalnya: Mitra validasi prototipe." value={values.subtype} onChange={edit('subtype')} />
      <TextArea label="Minat umum" value={values.thesis} onChange={edit('thesis')} rows={3} />
      <TextField label="Sektor" hint="Pisahkan dengan koma." value={values.sectors} onChange={edit('sectors')} />
      <CheckboxGroup id="p-stages" legend="Tahap yang diterima">
        {STAGES.map((stage) => (
          <Checkbox key={stage.value} label={stage.label} checked={values.stages.includes(stage.value)} onChange={toggle('stages', stage.value)} />
        ))}
      </CheckboxGroup>
      <TextField label="Wilayah" hint="Pisahkan dengan koma." value={values.regions} onChange={edit('regions')} />
      <TextField label="Bentuk dukungan" hint="Pisahkan dengan koma." value={values.support_forms} onChange={edit('support_forms')} />
      <CheckboxGroup id="p-forms" legend="Bentuk kerja sama">
        {RELATIONSHIP_FORMS.map((form) => (
          <Checkbox key={form.value} label={form.label} checked={values.relationship_forms.includes(form.value)} onChange={toggle('relationship_forms', form.value)} />
        ))}
      </CheckboxGroup>
      <TextArea label="Ekspektasi peninjauan" value={values.review_expectations} onChange={edit('review_expectations')} rows={2} />
      <p className="tr-muted">Isi kisaran hanya bila Anda bersedia menyatakannya. Belum ditentukan tidak pernah dianggap nol.</p>
      <RangeFields prefix="p" subjectLabel="Jenis kisaran" values={values.range} onChange={(field, value) => edit('range')({ ...values.range, [field]: value })} errors={errors} />
      <Select label="Penerimaan saat ini" value={values.intake_status} onChange={edit('intake_status')} options={INTAKE_CHOICES} emptyLabel={null} />
      <TextField id="p-from" label="Penerimaan dibuka sejak" hint="Format: TTTT-BB-HH. Boleh dikosongkan." value={values.intake_from} onChange={edit('intake_from')} error={errors['p-from']} />
      <TextField id="p-until" label="Penerimaan dibuka sampai" hint="Format: TTTT-BB-HH. Boleh dikosongkan." value={values.intake_until} onChange={edit('intake_until')} error={errors['p-until']} />
      <Select label="Jalur kontak" value={values.contact_route} onChange={edit('contact_route')} options={CONTACT_ROUTES} emptyLabel={null} />
      {values.contact_route === 'EXTERNAL' ? <TextField id="p-url" label="Alamat formulir" value={values.external_url} onChange={edit('external_url')} error={errors['p-url']} /> : null}
      {state !== 'idle' ? <SaveState state={state === 'failed' && failure?.code === 'STALE_VERSION' ? 'conflict' : state} onRetry={save} /> : null}
      <div className="tr-row">
        <Button intent="primary" icon="check" busy={state === 'saving'} busyLabel="Menyimpan…" onClick={save}>
          Simpan profil
        </Button>
      </div>
    </div>
  );
}

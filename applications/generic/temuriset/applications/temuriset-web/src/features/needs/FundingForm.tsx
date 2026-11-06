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
import { declareEntity, saveFundingRequest } from '@/features/needs/api';
import { CURRENCIES, FINANCING_FORMS, FINANCING_STAGES, fieldErrors, type FundingRequest, type LegalEntity } from '@/features/needs/model';

const NEW_ENTITY = 'baru';
const IDS: Record<string, string> = {
  legal_entity_id: 'fr-entity',
  name: 'fr-entity-name',
  currency: 'fr-currency',
  target_amount: 'fr-target',
  desired_min: 'fr-min',
  desired_max: 'fr-max',
  invention_ids: 'fr-inventions',
};
const ORDER = ['fr-entity', 'fr-entity-name', 'fr-currency', 'fr-target', 'fr-min', 'fr-max', 'fr-inventions'];

function digits(value: string | null | undefined): string {
  return value ? value.replace(/\.?0+$/, '') : '';
}

type Props = {
  request: FundingRequest;
  entities: LegalEntity[];
  /** Published inventions the acting party manages. */
  inventions: { id: string; title: string }[];
  actingPartyId: string;
};

/** S07 editor: one raise, its company, its own target and contribution range, and the inventions it develops. */
export function FundingForm({ request, entities, inventions, actingPartyId }: Props) {
  const router = useRouter();
  const [values, setValues] = useState({
    subject: request.subject_type as string,
    entity: request.legal_entity?.id ?? (entities[0]?.id ?? NEW_ENTITY),
    entity_name: '',
    jurisdiction: '',
    registration: '',
    proposed_name: request.proposed_name,
    stage: request.financing_stage ?? '',
    form: request.financing_form ?? '',
    currency: request.currency ?? '',
    target: digits(request.target_amount),
    min: digits(request.desired_min),
    max: digits(request.desired_max),
    partial: request.accepts_partial,
    syndicated: request.accepts_syndicated,
    use: request.intended_use,
    timing: request.timing,
    inventions: request.inventions.map((item) => item.invention_id),
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [failure, setFailure] = useState<ApiError | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<'idle' | 'saving' | 'saved' | 'failed'>('idle');
  const [key, setKey] = useState(newIdempotencyKey);
  const edit = <Field extends keyof typeof values>(field: Field) => (value: (typeof values)[Field]) => setValues((current) => ({ ...current, [field]: value }));

  async function save() {
    if (state === 'saving') return;
    setState('saving');
    try {
      let entityId: string | null = null;
      if (values.subject === 'EXISTING_ENTITY') {
        if (values.entity === NEW_ENTITY) {
          entityId = (await declareEntity(actingPartyId, values.entity_name, values.jurisdiction, values.registration)).id;
          setValues((current) => ({ ...current, entity: entityId! }));
        } else {
          entityId = values.entity;
        }
      }
      await saveFundingRequest(
        request.id,
        {
          acting_party_id: actingPartyId,
          expected_version: request.version,
          subject_type: values.subject,
          legal_entity_id: entityId,
          proposed_name: values.subject === 'PROPOSED_ENTITY' ? values.proposed_name : '',
          financing_stage: values.stage || null,
          financing_form: values.form || null,
          currency: values.currency || null,
          target_amount: values.target.trim() || null,
          desired_min: values.min.trim() || null,
          desired_max: values.max.trim() || null,
          accepts_partial: values.partial,
          accepts_syndicated: values.syndicated,
          intended_use: values.use,
          timing: values.timing,
          invention_ids: values.inventions,
        },
        key,
      );
      setState('saved');
      router.push(`/funding-requests/${request.id}`);
      router.refresh();
    } catch (error) {
      const apiError = ApiError.from(error);
      setErrors(apiError.code === 'VALIDATION_FAILED' ? fieldErrors(apiError, IDS) : {});
      setFailure(apiError);
      if (!apiError.recovery.retryable) setKey(newIdempotencyKey());
      setAttempt((current) => current + 1);
      setState('failed');
    }
  }

  const summary = ORDER.filter((id) => errors[id]).map((id) => ({ fieldId: id, message: errors[id] }));
  const entityOptions = [...entities.map((entity) => ({ value: entity.id, label: `${entity.name} (dinyatakan sendiri)` })), { value: NEW_ENTITY, label: 'Badan hukum lain' }];
  return (
    <div className="tr-stack">
      {failure ? (
        <ErrorSummary errors={summary} focusKey={attempt} title={failure.code === 'VALIDATION_FAILED' ? undefined : 'Pendanaan belum tersimpan'}>
          {summary.length ? null : `${failure.message} Kode rujukan: ${failure.requestId ?? '-'}.`}
        </ErrorSummary>
      ) : null}
      <section className="tr-panel tr-stack" aria-labelledby="fr-perusahaan">
        <h2 id="fr-perusahaan" className="tr-sys-type-heading-sm">
          Perusahaan
        </h2>
        <Select
          label="Status perusahaan"
          value={values.subject}
          onChange={edit('subject')}
          emptyLabel={null}
          options={[
            { value: 'EXISTING_ENTITY', label: 'Sudah berbadan hukum' },
            { value: 'PROPOSED_ENTITY', label: 'Perusahaan belum didirikan' },
          ]}
        />
        {values.subject === 'EXISTING_ENTITY' ? (
          <>
            <Select id="fr-entity" label="Badan hukum" value={values.entity} onChange={edit('entity')} emptyLabel={null} options={entityOptions} error={errors['fr-entity']} />
            {values.entity === NEW_ENTITY ? (
              <>
                <TextField id="fr-entity-name" label="Nama badan hukum" value={values.entity_name} onChange={edit('entity_name')} error={errors['fr-entity-name']} />
                <TextField label="Yurisdiksi" value={values.jurisdiction} onChange={edit('jurisdiction')} />
                <TextField label="Nomor registrasi" hint="Dicatat sebagai pernyataan Anda; pemeriksaan ditampilkan terpisah." value={values.registration} onChange={edit('registration')} />
              </>
            ) : null}
          </>
        ) : (
          <TextField label="Nama rencana perusahaan" hint="Ditampilkan dengan label Perusahaan belum didirikan." value={values.proposed_name} onChange={edit('proposed_name')} />
        )}
        <Select label="Tahap pendanaan perusahaan" hint="Terpisah dari tahap tiap inovasi." value={values.stage} onChange={edit('stage')} options={FINANCING_STAGES} />
        <Select label="Bentuk pendanaan" value={values.form} onChange={edit('form')} options={FINANCING_FORMS} />
      </section>
      <section className="tr-panel tr-stack" aria-labelledby="fr-jumlah">
        <h2 id="fr-jumlah" className="tr-sys-type-heading-sm">
          Target dan kontribusi
        </h2>
        <p className="tr-muted">Target Pendanaan milik putaran ini, bukan milik tiap inovasi. Tidak ada valuasi atau persentase kepemilikan yang dihitung.</p>
        <Select id="fr-currency" label="Mata uang" value={values.currency} onChange={edit('currency')} options={CURRENCIES} error={errors['fr-currency']} />
        <TextField id="fr-target" label="Target Pendanaan" type="decimal" hint="Angka tanpa titik ribuan, misalnya 500000." value={values.target} onChange={edit('target')} error={errors['fr-target']} />
        <TextField id="fr-min" label="Kontribusi per investor, batas bawah" type="decimal" value={values.min} onChange={edit('min')} error={errors['fr-min']} />
        <TextField id="fr-max" label="Kontribusi per investor, batas atas" type="decimal" value={values.max} onChange={edit('max')} error={errors['fr-max']} />
        <Checkbox label="Menerima pendanaan sebagian" checked={values.partial} onChange={edit('partial')} />
        <Checkbox label="Menerima pendanaan bersama investor lain" checked={values.syndicated} onChange={edit('syndicated')} />
        <TextArea label="Tujuan penggunaan dana" value={values.use} onChange={edit('use')} rows={3} />
        <TextField label="Waktu" hint="Misalnya: Dibuka sampai Maret 2027." value={values.timing} onChange={edit('timing')} />
      </section>
      <CheckboxGroup id="fr-inventions" legend="Inovasi yang dikembangkan" hint="Hanya inovasi yang sudah terbit. Jumlah pendanaan tidak disalin ke inovasi." error={errors['fr-inventions']}>
        {inventions.length ? (
          inventions.map((invention) => (
            <Checkbox
              key={invention.id}
              label={invention.title}
              checked={values.inventions.includes(invention.id)}
              onChange={(checked) => edit('inventions')(checked ? [...values.inventions, invention.id] : values.inventions.filter((id) => id !== invention.id))}
            />
          ))
        ) : (
          <p className="tr-muted">Belum ada inovasi yang terbit.</p>
        )}
      </CheckboxGroup>
      {state !== 'idle' ? <SaveState state={state === 'failed' && failure?.code === 'STALE_VERSION' ? 'conflict' : state} onRetry={save} /> : null}
      <div className="tr-row">
        <Button intent="primary" icon="check" busy={state === 'saving'} busyLabel="Menyimpan…" onClick={save}>
          Simpan pendanaan
        </Button>
      </div>
    </div>
  );
}

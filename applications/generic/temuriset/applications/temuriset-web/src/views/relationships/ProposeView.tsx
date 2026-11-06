'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState, type FormEvent } from 'react';

import type { Me } from '@/api/client';
import { Button } from '@/components/tr/Button';
import { Checkbox, CheckboxGroup } from '@/components/tr/Checkbox';
import { ErrorSummary } from '@/components/tr/ErrorSummary';
import { Screen } from '@/components/tr/Screen';
import { Select } from '@/components/tr/Select';
import { ContextBar } from '@/features/ContextBar';
import { readPersona } from '@/features/persona';
import { FIELD_LABEL, TYPE_LABEL, toggleField, type PartnershipKind, type PublicField, type Values } from '@/features/relationships/model';
import { RelationshipError } from '@/features/relationships/RelationshipError';
import { CeilingFields, RelationshipFields } from '@/features/relationships/RelationshipFields';
import { useRelationshipAction } from '@/features/relationships/useRelationshipAction';
import { PROVENANCE } from '@/views/parts';

export function ProposeView({ me, pitchId, types }: { me: Me; pitchId: string; types: PartnershipKind[] }) {
  const router = useRouter();
  const [kind, setKind] = useState<PartnershipKind>('PROJECT');
  const [values, setValues] = useState<Values>({ name: '', scope: '', start_date: '' });
  const [ceiling, setCeiling] = useState<PublicField[]>(['name', 'type', 'scope', 'date', 'amount']);
  const [subset, setSubset] = useState<PublicField[]>([]);
  const [invalid, setInvalid] = useState(0);
  const action = useRelationshipAction();
  const blockedEquity = !types.includes('EQUITY');

  function changeKind(value: string) {
    if (value === 'PROJECT' || value === 'LICENSE' || (value === 'EQUITY' && !blockedEquity)) {
      setKind(value);
      if (value !== 'EQUITY') {
        setValues((previous) => ({ ...previous, percent: null, percent_date: null }));
        setCeiling((previous) => previous.filter((field) => field !== 'percent'));
        setSubset((previous) => previous.filter((field) => field !== 'percent'));
      }
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!ceiling.length) {
      setInvalid((count) => count + 1);
      return;
    }
    setInvalid(0);
    const record = await action.run(`/api/v1/pitches/${pitchId}/partnerships`, {
      acting_party_id: me.active_party_id, type: kind, values, ceiling, subset,
    });
    if (record) router.replace(`/partnerships/${record.id}`);
  }

  return (
    <Screen persona={readPersona(me.account.persona) ?? 'inovator'} title="Usulkan ringkasan Kerja Sama" provenance={PROVENANCE}
      context={<ContextBar me={me} />} back={<Link className="tr-link" href={`/pitches/${pitchId}`}>Kembali ke ruang pitching</Link>}>
      <form className="tr-section" onSubmit={submit}>
        {action.error ? <RelationshipError error={action.error} prefix="usul" /> : null}
        {invalid ? <ErrorSummary focusKey={invalid} errors={[{ fieldId: 'usul-ceiling', message: 'Pilih setidaknya satu batas data publik.' }]} /> : null}
        <section className="tr-panel tr-stack" aria-label="Isi ringkasan">
          <Select id="usul-type" label="Jenis Kerja Sama" value={kind} onChange={changeKind} emptyLabel={null}
            options={(Object.keys(TYPE_LABEL) as PartnershipKind[]).map((type) => ({
              value: type, label: TYPE_LABEL[type],
              disabledReason: types.includes(type) ? undefined : 'Perlu badan usaha yang sudah teridentifikasi',
            }))} />
          {blockedEquity ? <p className="tr-muted tr-sys-type-support">Ekuitas hanya bisa dicatat untuk badan usaha yang sudah teridentifikasi.</p> : null}
          <RelationshipFields kind={kind} values={values} onChange={setValues} prefix="usul" />
        </section>
        <section className="tr-panel tr-stack" aria-label="Izin publik">
          <CeilingFields id="usul-ceiling" kind={kind} fields={ceiling} onToggle={(field, checked) => {
            setCeiling((previous) => toggleField(previous, field, checked));
            if (!checked) setSubset((previous) => toggleField(previous, field, false));
          }} />
          <CheckboxGroup id="usul-subset" legend="Data yang Anda izinkan tampil" hint="Kosongkan jika Anda ingin menjaga semua data tetap privat.">
            {ceiling.map((field) => (
              <Checkbox key={field} label={FIELD_LABEL[field]} checked={subset.includes(field)} onChange={(checked) => setSubset((previous) => toggleField(previous, field, checked))} />
            ))}
          </CheckboxGroup>
        </section>
        <p>Anda mengonfirmasi versi 1 saat mengirim. Pihak lain perlu mengonfirmasi versi yang sama.</p>
        <div className="tr-row"><Button type="submit" intent="primary" busy={action.busy}>Kirim ringkasan versi 1</Button></div>
      </form>
    </Screen>
  );
}

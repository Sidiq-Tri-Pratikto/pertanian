'use client';

import { Checkbox, CheckboxGroup } from '@/components/tr/Checkbox';
import { TextArea } from '@/components/tr/TextArea';
import { TextField } from '@/components/tr/TextField';
import { FIELD_LABEL, FIELDS, type PartnershipKind, type PublicField, type Values } from '@/features/relationships/model';

type Props = {
  kind: PartnershipKind;
  values: Values;
  onChange: (values: Values) => void;
  prefix: string;
};

export function RelationshipFields({ kind, values, onChange, prefix }: Props) {
  function field(key: keyof Values, value: string) {
    const required = key === 'name' || key === 'scope' || key === 'start_date' || key === 'evidence';
    onChange({ ...values, [key]: required ? value : value || null });
  }

  return (
    <div className="tr-stack">
      <TextField id={`${prefix}-name`} label="Nama Kerja Sama" required value={values.name} onChange={(value) => field('name', value)} />
      <TextArea id={`${prefix}-scope`} label="Cakupan" required rows={3} limit={1000} value={values.scope} onChange={(value) => field('scope', value)} />
      <TextField id={`${prefix}-start_date`} label="Tanggal mulai" type="date" required value={values.start_date} onChange={(value) => field('start_date', value)} />
      <div className="tr-grid">
        <TextField id={`${prefix}-amount`} label="Jumlah dana" type="decimal" value={values.amount ?? ''} onChange={(value) => field('amount', value)} />
        <TextField id={`${prefix}-currency`} label="Mata uang (mis. IDR)" value={values.currency ?? ''} onChange={(value) => field('currency', value.toUpperCase())} />
      </div>
      {kind === 'EQUITY' ? <div className="tr-grid">
        <TextField id={`${prefix}-percent`} label="Persentase saham" type="decimal" value={values.percent ?? ''} onChange={(value) => field('percent', value)} />
        <TextField id={`${prefix}-percent_date`} label="Tanggal berlaku persentase" type="date" value={values.percent_date ?? ''} onChange={(value) => field('percent_date', value)} />
      </div> : null}
      <TextArea id={`${prefix}-evidence`} label="Catatan bukti (privat)" rows={2} limit={500} value={values.evidence ?? ''} onChange={(value) => field('evidence', value)} />
    </div>
  );
}

export function CeilingFields({ kind, fields, onToggle, id }: {
  kind: PartnershipKind; fields: PublicField[]; onToggle: (field: PublicField, selected: boolean) => void; id: string;
}) {
  return (
    <CheckboxGroup id={id} legend="Batas data yang boleh tampil di publik" hint="Setiap pihak tetap memilih izin sendiri.">
      {FIELDS.filter((field) => field !== 'percent' || kind === 'EQUITY').map((field) => (
        <Checkbox key={field} label={FIELD_LABEL[field]} checked={fields.includes(field)} onChange={(checked) => onToggle(field, checked)} />
      ))}
    </CheckboxGroup>
  );
}

'use client';

import { Select } from '@/components/tr/Select';
import { TextField } from '@/components/tr/TextField';
import { FINANCIAL_BASES, FINANCIAL_SUBJECTS, type RangeValues } from '@/features/intake/model';
import { CURRENCIES, UNKNOWN_REASONS } from '@/features/needs/model';

type RangeFieldsProps = {
  /** Prefix of each field's id, so error summaries can link to them. */
  prefix: string;
  subjectLabel: string;
  values: RangeValues;
  onChange: (field: keyof RangeValues, value: string) => void;
  errors: Record<string, string>;
};

/** The fields that say what an amount means: subject, currency, range, basis, period, or why it is unknown. */
export function RangeFields({ prefix, subjectLabel, values, onChange, errors }: RangeFieldsProps) {
  const set = (field: keyof RangeValues) => (value: string) => onChange(field, value);
  const error = (name: string) => errors[`${prefix}-${name}`];
  return (
    <>
      <Select id={`${prefix}-subject`} label={subjectLabel} value={values.subject} onChange={set('subject')} options={FINANCIAL_SUBJECTS} emptyLabel={null} error={error('subject')} />
      <Select id={`${prefix}-currency`} label="Mata uang" value={values.currency} onChange={set('currency')} options={CURRENCIES} error={error('currency')} />
      <TextField id={`${prefix}-min`} label="Jumlah minimum" type="decimal" hint="Angka tanpa titik ribuan, misalnya 20000." value={values.min} onChange={set('min')} error={error('min')} />
      <TextField id={`${prefix}-max`} label="Jumlah maksimum" type="decimal" value={values.max} onChange={set('max')} error={error('max')} />
      <Select id={`${prefix}-basis`} label="Dasar perhitungan" value={values.basis} onChange={set('basis')} options={FINANCIAL_BASES} emptyLabel={null} error={error('basis')} />
      <TextField id={`${prefix}-period`} label="Periode" hint="Misalnya: 6 bulan." value={values.period} onChange={set('period')} error={error('period')} />
      <TextField id={`${prefix}-months`} label="Jumlah bulan" hint="Untuk total satu periode." type="text" inputMode="numeric" value={values.months} onChange={set('months')} error={error('months')} />
      <Select id={`${prefix}-unknown`} label="Bila kisaran belum diketahui" value={values.unknown_reason} onChange={set('unknown_reason')} options={UNKNOWN_REASONS} emptyLabel="Kisaran sudah diketahui" error={error('unknown')} />
    </>
  );
}

/** Where each service error about a range is shown. */
export function rangeErrorIds(path: string, prefix: string): Record<string, string> {
  return {
    [`${path}.subject`]: `${prefix}-subject`,
    [`${path}.currency`]: `${prefix}-currency`,
    [`${path}.min`]: `${prefix}-min`,
    [`${path}.max`]: `${prefix}-max`,
    [`${path}.basis`]: `${prefix}-basis`,
    [`${path}.period`]: `${prefix}-period`,
    [`${path}.months`]: `${prefix}-months`,
    [`${path}.unknown_reason`]: `${prefix}-unknown`,
  };
}

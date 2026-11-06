/**
 * Indonesian money display from decimal strings, mirroring `TR.format` in the design-system bundle. Amounts are never
 * parsed into numbers: grouping works on the digits the service sent.
 */
export const UNKNOWN_AMOUNT = 'Belum ditentukan';
// The no-break space keeps a currency with its digits; a long range can still wrap after its dash.
const NBSP = ' ';

export function amount(value: string): string {
  let text = String(value);
  const negative = text.startsWith('-');
  if (negative) text = text.slice(1);
  const [whole, fraction = ''] = text.split('.');
  const trimmed = fraction.replace(/0+$/, '');
  return (negative ? '-' : '') + whole.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + (trimmed ? `,${trimmed}` : '');
}

export function money(currency: string | null | undefined, value: string | null | undefined): string {
  return value == null ? UNKNOWN_AMOUNT : `${currency ?? ''}${NBSP}${amount(value)}`;
}

export function range(currency: string | null | undefined, min: string | null | undefined, max: string | null | undefined): string {
  if (min == null && max == null) return UNKNOWN_AMOUNT;
  if (min == null) return `Hingga ${money(currency, max)}`;
  if (max == null) return `Mulai ${money(currency, min)}`;
  if (String(min) === String(max)) return money(currency, min);
  return `${currency ?? ''}${NBSP}${amount(min)}–${amount(max)}`;
}

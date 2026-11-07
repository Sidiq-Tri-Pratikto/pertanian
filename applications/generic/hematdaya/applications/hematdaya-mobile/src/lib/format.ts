/**
 * Indonesian display formatting from the service's decimal strings. Values are never parsed into floats:
 * the service is the one calculation authority, and this file only rearranges its digits.
 */

const MINUTE_SECONDS = 60;
const HOUR_SECONDS = 3600;
const MWH_DECIMALS = 6;

const MONTHS = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober',
  'November', 'Desember']; // prettier-ignore

/** `14700.5` → `14.700,5`: dots group thousands, a comma marks decimals. */
export function formatDecimal(value: string): string {
  const negative = value.startsWith('-');
  const [whole, fraction] = value.replace(/^[-+]/, '').split('.');
  const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return `${negative ? '−' : ''}${grouped}${fraction ? `,${fraction}` : ''}`;
}

/** `"14.700"` → `14,700 kWh`. */
export function formatKwh(value: string): string {
  return `${formatDecimal(value)} kWh`;
}

/** `"57.14"` → `57,14%`. */
export function formatPercent(value: string): string {
  return `${formatDecimal(value)}%`;
}

/** A coverage ratio `"0.714"` → `71,4%`, by moving the decimal point two places. */
export function formatRatio(value: string): string {
  const [whole, fraction = ''] = value.split('.');
  const padded = fraction.padEnd(2, '0');
  const integer = `${whole}${padded.slice(0, 2)}`.replace(/^0+(?=\d)/, '');
  const rest = padded.slice(2).replace(/0+$/, '');
  return `${integer}${rest ? `,${rest}` : ''}%`;
}

/** A source's interval: `1 jam`, `15 menit`, or `90 detik` when it is not a whole number of either. */
export function formatCadence(seconds: number): string {
  if (seconds % HOUR_SECONDS === 0) {
    return `${seconds / HOUR_SECONDS} jam`;
  }
  return seconds % MINUTE_SECONDS === 0 ? `${seconds / MINUTE_SECONDS} menit` : `${seconds} detik`;
}

/** A resolution in integer mWh, `1500` → `0,0015 kWh`, by moving the decimal point on the digits. */
export function formatResolution(mwh: number): string {
  const digits = String(mwh).padStart(MWH_DECIMALS + 1, '0');
  const whole = digits.slice(0, -MWH_DECIMALS);
  const fraction = digits.slice(-MWH_DECIMALS).replace(/0+$/, '');
  return formatKwh(fraction ? `${whole}.${fraction}` : whole);
}

export type AssetKind = 'device' | 'circuit' | 'group' | 'meter';

export const KIND_LABEL: Record<AssetKind, string> = {
  device: 'Perangkat',
  circuit: 'Sirkuit',
  group: 'Grup',
  meter: 'Meter lokasi',
};

/** What an asset is and where: `Perangkat · Dapur · Pendingin makanan`, leaving out what is absent. */
export function formatAssetMeta(kind: AssetKind, location: string | null, category: string | null): string {
  return [KIND_LABEL[kind], location, category].filter(Boolean).join(' · ');
}

function dateParts(isoDate: string): [number, number, number] {
  const [year, month, day] = isoDate.split('-').map(Number);
  return [year, month, day];
}

/** `2026-10-21` → `21 Oktober 2026`. */
export function formatDate(isoDate: string): string {
  const [year, month, day] = dateParts(isoDate);
  return `${day} ${MONTHS[month - 1]} ${year}`;
}

/** Inclusive local dates: `19–25 Oktober 2026`, `28 September – 25 Oktober 2026`, or a single day. */
export function formatDateRange(start: string, end: string): string {
  if (start === end) {
    return formatDate(start);
  }
  const [startYear, startMonth, startDay] = dateParts(start);
  const [endYear, endMonth, endDay] = dateParts(end);
  if (startYear === endYear && startMonth === endMonth) {
    return `${startDay}–${endDay} ${MONTHS[endMonth - 1]} ${endYear}`;
  }
  if (startYear === endYear) {
    return `${startDay} ${MONTHS[startMonth - 1]} – ${formatDate(end)}`;
  }
  return `${formatDate(start)} – ${formatDate(end)}`;
}

type LocalParts = { date: string; time: string };

/** The site-local date and `HH.MM` of a UTC instant. */
export function localParts(instant: string, timeZone: string): LocalParts {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat('en-CA', {
      timeZone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hourCycle: 'h23',
    })
      .formatToParts(new Date(instant))
      .map((part) => [part.type, part.value]),
  );
  return { date: `${parts.year}-${parts.month}-${parts.day}`, time: `${parts.hour}.${parts.minute}` };
}

/** `25 Oktober 2026 18.00` in the site's timezone. */
export function formatDateTime(instant: string, timeZone: string): string {
  const { date, time } = localParts(instant, timeZone);
  return `${formatDate(date)} ${time}`;
}

/** A gap: `22 Oktober 2026 14.00–16.00` within one local day, otherwise the local dates it spans. */
export function formatGap(start: string, end: string, timeZone: string): string {
  const from = localParts(start, timeZone);
  const to = localParts(end, timeZone);
  const last = localParts(new Date(Date.parse(end) - 1).toISOString(), timeZone);
  if (from.date === last.date) {
    return `${formatDate(from.date)} ${from.time}–${to.time === '00.00' ? '24.00' : to.time}`;
  }
  return formatDateRange(from.date, last.date);
}

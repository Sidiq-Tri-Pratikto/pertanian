import { getLocale } from '@/features/localization/locale';
import { currentCopy } from '@/features/localization/messages';
import { historyInstant, type HistoryResponse } from '@/api/client';
import type { HistoryPoint } from '@/components/hd/HDHistoryChart';
import { formatDate, formatDateRange, formatKwh, formatRatio, formatResolution } from '@/lib/format';

type Bucket = HistoryResponse['buckets'][number];

function clock(value: string): string {
  return getLocale() === 'en' ? value.replaceAll('.', ':') : value.replaceAll(':', '.');
}

function localInstantLabel(instant: string, formatter: Intl.DateTimeFormat): string {
  const parts = Object.fromEntries(formatter.formatToParts(new Date(historyInstant(instant))).map(({ type, value }) => [type, value]));
  const offset = parts.timeZoneName.slice(3) || '+00:00';
  const time = parts.second === '00' ? `${parts.hour}.${parts.minute}` : `${parts.hour}.${parts.minute}.${parts.second}`;
  return `${formatDate(`${parts.year}-${parts.month}-${parts.day}`)} ${clock(time)} (UTC${offset})`;
}

function bucketStartLabel(bucket: Bucket): string {
  const date = formatDate(bucket.local_date);
  return bucket.local_time === null ? date : `${date} ${clock(bucket.local_time)} (UTC${bucket.utc_offset})`;
}

function bucketQuality(bucket: Bucket, qualification: string): string {
  switch (bucket.state) {
    case 'measured':
      return currentCopy(`Terukur${qualification}`, `Measured${qualification}`);
    case 'partial':
      return currentCopy(`Data sebagian. Angka hanya mencakup bagian yang tercatat${qualification}.`, `Partial data. The figure covers only recorded readings${qualification}.`);
    case 'missing':
      return currentCopy(`Tidak ada data${qualification}`, `No data${qualification}`);
    case 'future':
      return currentCopy("Belum terjadi", "Future interval");
    default: {
      const reason = bucket.unavailable_reason === 'source_conflict'
        ? currentCopy("Sumber data bertentangan untuk interval ini", "Sources conflict for this interval")
        : bucket.unavailable_reason === 'insufficient_resolution'
          ? currentCopy("Resolusi pengukuran belum memadai untuk interval ini", "Measurement resolution is too low for this interval")
          : currentCopy("Data tidak tersedia untuk interval ini", "Data unavailable for this interval");
      return `${reason}${qualification}.`;
    }
  }
}

/** Format one confirmed response for the S06 plot, visible summary and exact data alternative. */
export function historyModel(history: HistoryResponse) {
  const { window, buckets } = history;
  const formatter = new Intl.DateTimeFormat('en-GB', {
    timeZone: window.timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hourCycle: 'h23',
    timeZoneName: 'longOffset',
  });
  const cutoff = historyInstant(window.effective_end);
  const through = currentCopy(`hingga ${localInstantLabel(window.effective_end, formatter)}`, `through ${localInstantLabel(window.effective_end, formatter)}`);
  const current = window.is_current
    ? cutoff === historyInstant(window.start) ? currentCopy("periode belum dimulai", "period has not started") : through
    : null;
  const periodLabel = [formatDateRange(window.start_date, window.end_date), window.timezone, current].filter(Boolean).join(' · ');
  const highestStart = historyInstant(history.highest_bucket?.start);
  let highestLabel: string | undefined;
  const hourly = history.bucket === 'hour';
  const dense = hourly || buckets.length > 7;
  const step = Math.ceil(buckets.length / 4);
  const repeatedTimes = new Set<string>();
  const localTimes = new Set<string>();
  for (const bucket of buckets) {
    if (bucket.local_time === null) continue;
    if (localTimes.has(bucket.local_time)) repeatedTimes.add(bucket.local_time);
    localTimes.add(bucket.local_time);
  }

  const gaps: { first: Bucket; last: Bucket }[] = [];
  const entries = buckets.map((bucket, index) => {
    if (bucket.state === 'missing') {
      if (buckets[index - 1]?.state === 'missing') gaps[gaps.length - 1].last = bucket;
      else gaps.push({ first: bucket, last: bucket });
    }
    const start = historyInstant(bucket.start);
    const qualification = start < cutoff && cutoff < historyInstant(bucket.end) ? ` ${through}` : '';
    const label = bucketStartLabel(bucket);
    const energy = bucket.energy_kwh === null ? '—' : formatKwh(bucket.energy_kwh) + qualification;
    const coverage = bucket.coverage === null ? '—' : formatRatio(bucket.coverage) + qualification;
    if (start === highestStart) highestLabel = `${label}, ${energy}`;

    const time = bucket.local_time === null ? null : clock(bucket.local_time);
    const repeated = bucket.local_time !== null && repeatedTimes.has(bucket.local_time);
    const axisLabel = repeated
      ? `${time} (UTC${bucket.utc_offset})`
      : !dense || index % step === 0 || index === buckets.length - 1
        ? time ?? label.split(' ')[0]
        : '';
    const point: HistoryPoint = {
      id: bucket.start, label: axisLabel, current: bucket.energy_kwh, state: bucket.state as HistoryPoint['state'],
    };
    return {
      point,
      row: {
        period: hourly ? `${label} – ${localInstantLabel(bucket.end, formatter)}` : label,
        energy,
        coverage,
        quality: bucketQuality(bucket, qualification),
      },
    };
  });

  const missingIntervals = gaps.map(({ first, last }) => {
    const elapsed = historyInstant(last.end) > cutoff;
    const end = elapsed ? window.effective_end : last.end;
    const range = hourly ? '' : currentCopy(`${formatDateRange(first.local_date, last.local_date)}, mulai `, `${formatDateRange(first.local_date, last.local_date)}, from `);
    return currentCopy(`Tidak ada data: ${range}${localInstantLabel(first.start, formatter)} ${elapsed ? 'hingga' : 'sampai sebelum'} ${localInstantLabel(end, formatter)}.`, `No data: ${range}${localInstantLabel(first.start, formatter)} ${elapsed ? 'through' : 'until'} ${localInstantLabel(end, formatter)}.`);
  });

  return {
    periodLabel,
    gapNote: missingIntervals.length ? missingIntervals.join(' ') : undefined,
    summary: highestLabel ? currentCopy(`Energi tercatat tertinggi: ${highestLabel}.`, `Highest recorded energy: ${highestLabel}.`) : currentCopy("Belum ada interval terukur lengkap untuk menentukan energi tertinggi.", "There are no complete intervals to compare yet."),
    rows: entries.map(({ row }) => row),
    points: entries.map(({ point }) => point),
    dense,
    origins: history.origins,
    resolution: history.resolution_mwh === null ? null : formatResolution(history.resolution_mwh),
  };
}

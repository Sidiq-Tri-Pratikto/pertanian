import type { components } from '@/api/schema.generated';

type History = components['schemas']['HistoryResponse'];
type Bucket = History['buckets'][number];

export const weekWindow: History['window'] = {
  start_date: '2026-10-19',
  end_date: '2026-10-25',
  timezone: 'Asia/Jakarta',
  start: '2026-10-18T17:00:00Z',
  end: '2026-10-25T17:00:00Z',
  effective_end: '2026-10-25T17:00:00Z',
  is_current: false,
};

export const mondayWindow: History['window'] = {
  ...weekWindow,
  end_date: '2026-10-19',
  end: '2026-10-19T17:00:00Z',
  effective_end: '2026-10-19T17:00:00Z',
};

export const measuredBucket = {
  energy_kwh: '1.200',
  state: 'measured',
  coverage: '1.000',
  unavailable_reason: null,
};

const HOUR_MS = 3_600_000;
const iso = (instant: number) => new Date(instant).toISOString();

export function hourlyHistory(window = mondayWindow): History {
  const start = Date.parse(window.start);
  const count = (Date.parse(window.end) - start) / HOUR_MS;
  const local = new Intl.DateTimeFormat('en-GB', {
    timeZone: window.timezone, hourCycle: 'h23', hour: '2-digit', minute: '2-digit', timeZoneName: 'longOffset',
  });
  const buckets: Bucket[] = Array.from({ length: count }, (_, index) => {
    const from = start + index * HOUR_MS;
    const parts = Object.fromEntries(local.formatToParts(from).map(({ type, value }) => [type, value]));
    return {
      ...measuredBucket,
      start: iso(from),
      end: iso(from + HOUR_MS),
      local_date: window.start_date,
      local_time: parts.hour + ':' + parts.minute,
      utc_offset: parts.timeZoneName.slice(3) || '+00:00',
    };
  });
  return { ...weeklyHistory(), bucket: 'hour', window, buckets, highest_bucket: { start: buckets[0].start } };
}

export function weeklyHistory(): History {
  const start = Date.parse(weekWindow.start);
  const dayMs = HOUR_MS * 24;
  const buckets: Bucket[] = Array.from({ length: 7 }, (_, index) => ({
    ...measuredBucket,
    start: iso(start + index * dayMs),
    end: iso(start + (index + 1) * dayMs),
    local_date: '2026-10-' + (19 + index),
    local_time: null,
    utc_offset: '+07:00',
  }));
  return {
    bucket: 'day',
    window: weekWindow,
    buckets,
    highest_bucket: { start: weekWindow.start },
    origins: ['simulated'],
    resolution_mwh: 1000,
    comparison_state: null,
  };
}

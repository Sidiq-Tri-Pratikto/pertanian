import { historyModel } from '@/features/assets/history-model';

import { hourlyHistory, mondayWindow, weeklyHistory } from './fixtures/history';

describe('asset history display', () => {
  it('uses the service tie-break and preserves exact weekly values, period and provenance', () => {
    const history = weeklyHistory();
    const model = historyModel(history);

    expect(model.periodLabel).toBe('19–25 Oktober 2026 · Asia/Jakarta');
    expect(model.summary).toBe('Energi tercatat tertinggi: 19 Oktober 2026, 1,200 kWh.');
    expect(model.rows.map((row) => row.energy)).toEqual(Array(7).fill('1,200 kWh'));
    expect(model.points.map((point) => point.current)).toEqual(Array(7).fill('1.200'));
    expect(model.origins).toEqual(['simulated']);
    expect(model.resolution).toBe('0,001 kWh');
  });

  it('trusts the exact selected instant even when another bucket has the same displayed energy', () => {
    const history = weeklyHistory();
    history.highest_bucket = { start: '2026-10-20T00:00:00+07:00' };

    expect(historyModel(history).summary).toBe('Energi tercatat tertinggi: 20 Oktober 2026, 1,200 kWh.');
  });

  it('can name a measured zero as highest', () => {
    const history = weeklyHistory();
    history.buckets = history.buckets.map((bucket) => ({ ...bucket, energy_kwh: '0.000' }));

    expect(historyModel(history).summary).toBe('Energi tercatat tertinggi: 19 Oktober 2026, 0,000 kWh.');
  });

  it('qualifies a measured current highest and its 100% coverage through the returned cutoff', () => {
    const history = hourlyHistory();
    history.window = { ...history.window, effective_end: '2026-10-18T17:30:00Z', is_current: true };
    const model = historyModel(history);

    expect(model.periodLabel).toBe('19 Oktober 2026 · Asia/Jakarta · hingga 19 Oktober 2026 00.30 (UTC+07:00)');
    expect(model.summary).toContain('1,200 kWh hingga 19 Oktober 2026 00.30 (UTC+07:00)');
    expect(model.rows[0]).toMatchObject({
      energy: '1,200 kWh hingga 19 Oktober 2026 00.30 (UTC+07:00)',
      coverage: '100% hingga 19 Oktober 2026 00.30 (UTC+07:00)',
    });
  });

  it.each([
    ['2026-03-29', '2026-03-28T23:00:00Z', '2026-03-29T22:00:00Z', 23],
    ['2026-10-25', '2026-10-24T22:00:00Z', '2026-10-25T23:00:00Z', 25],
  ])('uses all returned hours on %s and sparse, offset-distinct axis labels', (date, start, end, count) => {
    const history = hourlyHistory({
      ...mondayWindow, timezone: 'Europe/Amsterdam', start_date: date, end_date: date, start, end, effective_end: end,
    });
    const repeated = history.buckets.filter((bucket) => bucket.local_time === '02:00');
    if (count === 25) history.highest_bucket = { start: repeated[1].start };
    const model = historyModel(history);

    expect(model.rows).toHaveLength(count);
    expect(model.points.map((point) => point.id)).toEqual(history.buckets.map((bucket) => bucket.start));
    expect(model.points.filter((point) => point.label).length).toBeLessThan(8);
    if (count === 23) {
      expect(model.rows.every((row) => !row.period.includes('02.00'))).toBe(true);
      expect(model.points.filter((point) => point.label.startsWith('02.00'))).toHaveLength(0);
      expect(repeated).toHaveLength(0);
    } else {
      expect(model.points.map((point) => point.label)).toEqual(expect.arrayContaining(['02.00 (UTC+02:00)', '02.00 (UTC+01:00)']));
      expect(model.rows[2].period).toContain('02.00 (UTC+02:00)');
      expect(model.rows[3].period).toContain('02.00 (UTC+01:00)');
      expect(model.summary).toContain('25 Oktober 2026 02.00 (UTC+01:00)');
    }
  });
});

it('names the exact repeated-hour interval that lacks data', () => {
  const history = hourlyHistory({
    ...mondayWindow,
    timezone: 'Europe/Amsterdam',
    start_date: '2026-10-25',
    end_date: '2026-10-25',
    start: '2026-10-24T22:00:00Z',
    end: '2026-10-25T23:00:00Z',
    effective_end: '2026-10-25T23:00:00Z',
  });
  history.buckets[2] = { ...history.buckets[2], state: 'missing', energy_kwh: null, coverage: '0.000' };

  expect(historyModel(history).gapNote).toBe('Tidak ada data: 25 Oktober 2026 02.00 (UTC+02:00) sampai sebelum 25 Oktober 2026 02.00 (UTC+01:00).');
});

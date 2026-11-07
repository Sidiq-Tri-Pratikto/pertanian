import { formatDate, formatDateRange, formatDateTime, formatGap, formatKwh, formatPercent, formatRatio } from '@/lib/format';

describe('Indonesian formatting from decimal strings', () => {
  it.each([
    ['14.700', '14,700 kWh'],
    ['0.870', '0,870 kWh'],
    ['576.000', '576,000 kWh'],
    ['14700.500', '14.700,500 kWh'],
    ['-1.400', '−1,400 kWh'],
  ])('formats %s as %s', (value, expected) => {
    expect(formatKwh(value)).toBe(expected);
  });

  it.each([
    ['57.14', '57,14%'],
    ['0.00', '0,00%'],
  ])('formats share %s as %s', (value, expected) => {
    expect(formatPercent(value)).toBe(expected);
  });

  it.each([
    ['1.000', '100%'],
    ['0.714', '71,4%'],
    ['0.916', '91,6%'],
    ['0.000', '0%'],
    ['0.050', '5%'],
  ])('formats coverage %s as %s', (value, expected) => {
    expect(formatRatio(value)).toBe(expected);
  });

  it.each([
    ['2026-10-19', '2026-10-25', '19–25 Oktober 2026'],
    ['2026-09-28', '2026-10-25', '28 September – 25 Oktober 2026'],
    ['2026-10-21', '2026-10-21', '21 Oktober 2026'],
    ['2025-12-29', '2026-01-04', '29 Desember 2025 – 4 Januari 2026'],
  ])('formats %s to %s as %s', (start, end, expected) => {
    expect(formatDateRange(start, end)).toBe(expected);
  });

  it('formats instants and gaps in the site timezone', () => {
    expect(formatDate('2026-10-01')).toBe('1 Oktober 2026');
    expect(formatDateTime('2026-10-25T11:00:00Z', 'Asia/Jakarta')).toBe('25 Oktober 2026 18.00');
    expect(formatGap('2026-10-22T07:00:00Z', '2026-10-22T09:00:00Z', 'Asia/Jakarta')).toBe('22 Oktober 2026 14.00–16.00');
    expect(formatGap('2026-10-23T17:00:00Z', '2026-10-25T17:00:00Z', 'Asia/Jakarta')).toBe('24–25 Oktober 2026');
    expect(formatGap('2026-10-24T13:00:00Z', '2026-10-24T17:00:00Z', 'Asia/Jakarta')).toBe('24 Oktober 2026 20.00–24.00');
  });
});

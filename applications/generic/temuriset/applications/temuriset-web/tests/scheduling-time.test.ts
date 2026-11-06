import { fromLocalInput, longDate, slotTime, toLocalInput, zoneLabel } from '@/features/scheduling/time';

describe('time in each reader zone (AC49)', () => {
  const start = '2026-11-04T09:00:00Z';
  const end = '2026-11-04T10:00:00Z';

  it('shows one instant as 16.00 WIB, 17.00 WITA and 18.00 WIT', () => {
    expect(slotTime(start, end, 'Asia/Jakarta')).toBe('16.00–17.00 WIB (Asia/Jakarta)');
    expect(slotTime(start, end, 'Asia/Makassar')).toBe('17.00–18.00 WITA (Asia/Makassar)');
    expect(slotTime(start, end, 'Asia/Jayapura')).toBe('18.00–19.00 WIT (Asia/Jayapura)');
    expect(zoneLabel('Europe/Berlin')).toBe('Europe/Berlin');
    expect(longDate(start, 'Asia/Jakarta')).toBe('Rabu, 4 November 2026');
  });

  it('turns a wall-clock entry in the reader zone into the UTC instant and back', () => {
    expect(fromLocalInput('2026-11-04T16:00', 'Asia/Jakarta')).toBe('2026-11-04T09:00:00.000Z');
    expect(fromLocalInput('2026-11-04T17:00', 'Asia/Makassar')).toBe('2026-11-04T09:00:00.000Z');
    expect(toLocalInput(start, 'Asia/Jayapura')).toBe('2026-11-04T18:00');
    expect(fromLocalInput('2026-03-29T03:30', 'Europe/Berlin')).toBe('2026-03-29T01:30:00.000Z');
  });
});

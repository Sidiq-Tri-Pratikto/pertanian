import { TKT_DEFINITION, TKT_GROUPS, TKT_LEVELS, tktLabel, tktLevelOf } from '@/features/portfolio/tkt';

describe('TKT scale definitions (spec 055)', () => {
  it('defines nine ascending levels with Indonesian and English names, meanings and examples', () => {
    expect(TKT_LEVELS).toHaveLength(9);
    expect(TKT_LEVELS.map((item) => item.level)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9]);
    for (const item of TKT_LEVELS) {
      expect(item.name.length).toBeGreaterThan(0);
      expect(item.nameEn.length).toBeGreaterThan(0);
      expect(item.meaning.length).toBeGreaterThan(0);
      expect(item.meaningEn.length).toBeGreaterThan(0);
      expect(item.example.length).toBeGreaterThan(0);
      expect(item.exampleEn.length).toBeGreaterThan(0);
    }
    expect(TKT_DEFINITION).toContain('Permenristekdikti No. 42 Tahun 2016');
  });

  it('maps levels 1-3 to basic, 4-6 to applied, and 7-9 to development', () => {
    expect(TKT_GROUPS.map((group) => [group.id, group.min, group.max])).toEqual([
      ['basic', 1, 3],
      ['applied', 4, 6],
      ['development', 7, 9],
    ]);
    for (const item of TKT_LEVELS) {
      const group = TKT_GROUPS.find((entry) => entry.id === item.group);
      expect(group).toBeDefined();
      expect(item.level).toBeGreaterThanOrEqual(group!.min);
      expect(item.level).toBeLessThanOrEqual(group!.max);
    }
  });

  it('formats TKT labels with an optional stage label', () => {
    expect(tktLabel(6, 'Prototipe')).toBe('TKT 6 · Prototipe');
    expect(tktLabel(6)).toBe('TKT 6 · Prototipe teruji');
    expect(tktLevelOf(4)?.name).toBe('Uji laboratorium');
    expect(tktLevelOf(0)).toBeUndefined();
    expect(tktLevelOf(null)).toBeUndefined();
  });
});

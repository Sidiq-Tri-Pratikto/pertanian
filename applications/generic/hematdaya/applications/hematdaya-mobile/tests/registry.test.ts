import { existsSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

import { FEATURES, findFeature } from '@/features/registry';

const SPECS = join(__dirname, '../../../specs');
const SCREENS = Array.from({ length: 12 }, (_, index) => `S${String(index + 1).padStart(2, '0')}`);

describe('feature registry', () => {
  it('covers every screen in the product contract', () => {
    const covered = new Set(FEATURES.flatMap((feature) => feature.screens));

    expect(SCREENS.filter((screen) => !covered.has(screen))).toEqual([]);
  });

  it('has unique ids', () => {
    expect(new Set(FEATURES.map((feature) => feature.id)).size).toBe(FEATURES.length);
  });

  it('claims only what has shipped', () => {
    expect(FEATURES.filter((feature) => feature.status === 'available').map((feature) => feature.id)).toEqual([
      'demo',
      'ringkasan-energi',
      'kontributor',
      'saran',
      'bukti-saran',
    ]);
  });

  it('keeps spec numbers out of product copy', () => {
    const copy = FEATURES.flatMap((feature) => [feature.title, feature.summary, ...feature.points]).join(' ');

    expect(copy).not.toMatch(/\b\d{3}\b/);
  });

  it('links every feature to an existing spec folder', () => {
    const folders = existsSync(SPECS) ? readdirSync(SPECS) : [];
    const missing = FEATURES.flatMap((feature) => feature.specs).filter(
      (spec) => !folders.some((folder) => folder.startsWith(`${spec}-`)),
    );

    expect(missing).toEqual([]);
  });

  it('finds a feature by id and returns nothing otherwise', () => {
    expect(findFeature('demo')?.title).toBe('Data demo');
    expect(findFeature('tidak-ada')).toBeUndefined();
    expect(findFeature(undefined)).toBeUndefined();
  });
});

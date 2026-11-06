import { destinationFor } from '@/features/destinations';
import { NAV, homeFor, readPersona } from '@/features/persona';
import { findFeature } from '@/features/registry';

describe('persona and destinations', () => {
  it('accepts only the two public personas', () => {
    expect(readPersona('inovator')).toBe('inovator');
    expect(readPersona('mitra')).toBe('mitra');
    expect(readPersona('reviewer')).toBeNull();
    expect(readPersona(undefined)).toBeNull();
  });

  it('starts inventors at Beranda and partners at Jelajahi', () => {
    expect(homeFor('inovator')).toBe('/home');
    expect(homeFor('mitra')).toBe('/discover');
  });

  it('gives each persona five destinations, so the tab bar shows four plus Lainnya', () => {
    expect(NAV.inovator.map((item) => item.label)).toEqual([
      'Beranda',
      'Inovasi Saya',
      'Temukan Investor/Mitra',
      'Pitching dan Diskusi',
      'Profil',
    ]);
    expect(NAV.mitra.map((item) => item.label)).toEqual([
      'Jelajahi',
      'Kebutuhan/Mandat',
      'Pitching Masuk',
      'Diskusi dan Jadwal',
      'Profil',
    ]);
  });

  it('routes partner pitches to the incoming box unless discussions are asked for', () => {
    expect(destinationFor('pitches', 'mitra').title).toBe('Pitching Masuk');
    expect(destinationFor('pitches', 'mitra', 'diskusi').title).toBe('Diskusi dan Jadwal');
    expect(destinationFor('pitches', 'inovator', 'diskusi').title).toBe('Pitching dan Diskusi');
  });

  it('only lists features that exist in the registry', () => {
    const ids = (['home', 'inventions', 'discover', 'opportunities', 'pitches'] as const).flatMap((id) => [
      ...destinationFor(id, 'inovator').features,
      ...destinationFor(id, 'mitra', 'diskusi').features,
      ...destinationFor(id, 'mitra').features,
    ]);

    expect(ids.filter((id) => !findFeature(id))).toEqual([]);
  });
});

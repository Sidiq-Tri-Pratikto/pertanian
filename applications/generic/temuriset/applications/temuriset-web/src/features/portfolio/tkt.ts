/**
 * Single source of truth for Indonesia's nine-level technology readiness scale (TKT,
 * Permenristekdikti No. 42 Tahun 2016) across every TemuRiset screen (spec 055).
 *
 * Indonesian source strings stay data here; UI components translate them at render time with `t()`.
 */

export type TktGroupId = 'basic' | 'applied' | 'development';

export type TktGroup = {
  id: TktGroupId;
  min: number;
  max: number;
  label: string;
  labelEn: string;
};

export type TktLevel = {
  level: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9;
  name: string;
  nameEn: string;
  meaning: string;
  meaningEn: string;
  example: string;
  exampleEn: string;
  group: TktGroupId;
};

export const TKT_GROUPS: readonly TktGroup[] = [
  { id: 'basic', min: 1, max: 3, label: 'Riset dasar', labelEn: 'Basic research' },
  { id: 'applied', min: 4, max: 6, label: 'Riset terapan', labelEn: 'Applied research' },
  {
    id: 'development',
    min: 7,
    max: 9,
    label: 'Pengembangan dan komersialisasi',
    labelEn: 'Development and commercialization',
  },
];

export const TKT_LEVELS: readonly TktLevel[] = [
  {
    level: 1,
    name: 'Prinsip dasar',
    nameEn: 'Basic principles',
    meaning: 'Prinsip dasar teknologi sudah diteliti dan dilaporkan.',
    meaningEn: 'Basic principles of the technology have been observed and reported.',
    example: 'Kajian pustaka, laporan penelitian',
    exampleEn: 'Literature review, research report',
    group: 'basic',
  },
  {
    level: 2,
    name: 'Konsep teknologi',
    nameEn: 'Technology concept',
    meaning: 'Konsep dan kemungkinan penerapan teknologi sudah dirumuskan.',
    meaningEn: 'Technology concept and potential application have been formulated.',
    example: 'Rancangan konsep, analisis awal',
    exampleEn: 'Concept design, initial analysis',
    group: 'basic',
  },
  {
    level: 3,
    name: 'Bukti konsep',
    nameEn: 'Proof of concept',
    meaning: 'Fungsi utama terbukti secara analitis dan lewat percobaan awal.',
    meaningEn: 'Core function is proven analytically and through initial experiments.',
    example: 'Hasil percobaan, simulasi',
    exampleEn: 'Experiment results, simulation',
    group: 'basic',
  },
  {
    level: 4,
    name: 'Uji laboratorium',
    nameEn: 'Laboratory validation',
    meaning: 'Komponen atau sistem sudah divalidasi di laboratorium.',
    meaningEn: 'Component or system has been validated in a laboratory.',
    example: 'Laporan uji laboratorium',
    exampleEn: 'Laboratory test report',
    group: 'applied',
  },
  {
    level: 5,
    name: 'Uji lingkungan relevan',
    nameEn: 'Relevant-environment validation',
    meaning: 'Komponen atau sistem sudah divalidasi di lingkungan yang menyerupai kondisi nyata.',
    meaningEn: 'Component or system has been validated in an environment resembling real conditions.',
    example: 'Laporan uji lapangan terbatas',
    exampleEn: 'Limited field-test report',
    group: 'applied',
  },
  {
    level: 6,
    name: 'Prototipe teruji',
    nameEn: 'Tested prototype',
    meaning: 'Prototipe sudah didemonstrasikan di lingkungan yang relevan.',
    meaningEn: 'Prototype has been demonstrated in a relevant environment.',
    example: 'Foto atau video prototipe, laporan demonstrasi',
    exampleEn: 'Prototype photos or video, demonstration report',
    group: 'applied',
  },
  {
    level: 7,
    name: 'Prototipe di kondisi nyata',
    nameEn: 'Field-condition prototype',
    meaning: 'Prototipe sistem sudah didemonstrasikan di lingkungan sebenarnya.',
    meaningEn: 'System prototype has been demonstrated in an operational environment.',
    example: 'Laporan uji di lokasi pengguna',
    exampleEn: 'User-site test report',
    group: 'development',
  },
  {
    level: 8,
    name: 'Sistem lengkap teruji',
    nameEn: 'Qualified complete system',
    meaning: 'Sistem lengkap sudah memenuhi syarat melalui pengujian di lingkungan sebenarnya.',
    meaningEn: 'Complete system is qualified through testing in an operational environment.',
    example: 'Sertifikat uji, standar yang dipenuhi',
    exampleEn: 'Test certificates, standards met',
    group: 'development',
  },
  {
    level: 9,
    name: 'Terbukti beroperasi',
    nameEn: 'Proven in operation',
    meaning: 'Teknologi sudah terbukti lewat operasi atau penjualan yang berhasil.',
    meaningEn: 'Technology is proven through successful operations or commercial sales.',
    example: 'Bukti penjualan, laporan operasi',
    exampleEn: 'Sales proof, operational report',
    group: 'development',
  },
];

export const TKT_DEFINITION =
  'TKT (Tingkat Kesiapterapan Teknologi) menunjukkan seberapa siap teknologi diterapkan, dari 1 (prinsip dasar) sampai 9 (terbukti beroperasi). Skala ini mengikuti Permenristekdikti No. 42 Tahun 2016. Nilainya dinyatakan inovator, bukan hasil penilaian TemuRiset.';

export const TKT_DEFINITION_EN =
  'TKT (Technology Readiness Level) indicates how ready a technology is to apply, from 1 (basic principles) to 9 (proven in operation). This scale follows Permenristekdikti No. 42 of 2016. The level is stated by the inventor, not assessed by TemuRiset.';

/** Return the TKT level definition for a number 1–9, or undefined when out of range. */
export function tktLevelOf(level: number | null | undefined): TktLevel | undefined {
  return typeof level === 'number' ? TKT_LEVELS.find((item) => item.level === level) : undefined;
}

/** Format a compact TKT label such as "TKT 6 · Prototipe" or "TKT 6 · Prototipe teruji". */
export function tktLabel(level: number, stageLabel?: string | null): string {
  const detail = stageLabel?.trim() || tktLevelOf(level)?.name;
  return detail ? `TKT ${level} · ${detail}` : `TKT ${level}`;
}

const STAGE_TKT_RANGE: Record<string, readonly [number, number]> = {
  IDEA: [1, 3],
  PROTOTYPE: [3, 6],
  PILOT: [5, 7],
  WORKING: [6, 8],
  MARKET: [8, 9],
};

/** Expected TKT range [min, max] for an invention stage, or null when stage is empty/unknown (spec 056). */
export function expectedRange(stage: string | null | undefined): readonly [number, number] | null {
  return stage && stage in STAGE_TKT_RANGE ? STAGE_TKT_RANGE[stage] : null;
}

/**
 * Returns whether the chosen TKT level disagrees strongly with the invention's stage (outside expected range ± 1).
 * Always advisory: never blocks saving or publishing.
 */
export function mismatch(stage: string | null | undefined, level: number | null | undefined): 'above' | 'below' | null {
  if (typeof level !== 'number') return null;
  const range = expectedRange(stage);
  if (!range) return null;
  if (level > range[1] + 1) return 'above';
  if (level < range[0] - 1) return 'below';
  return null;
}

import type { ContextPreset } from '@/features/context-preset';

export type ImportExample = { id: string; label: string; file: string; text: string };

/** One reading per hour on 20 Oktober 2026, starting at `from`. */
function hourly(name: string, from: number, count: number, value: string | ((index: number) => string)): string[] {
  return Array.from(
    { length: count },
    (_, index) => `2026-10-20 ${String(from + index).padStart(2, '0')}:00,${name},${typeof value === 'function' ? value(index) : value}`,
  );
}

/**
 * The prototype's eight copyable examples, ported as data (`hematdaya-app.js`, `EXAMPLES`). Every file is dated
 * 20 Oktober 2026, before the `empty` workspace's clock, so its rows show once imported. The context changes
 * the asset names only.
 */
export function EXAMPLES(preset: ContextPreset): ImportExample[] {
  const [first, second] = preset === 'industry' || preset === 'business' ? ['Mesin Jahit', 'Lampu Gudang'] : ['Lampu Teras', 'Dispenser'];
  const header = 'timestamp,perangkat,energi_wh';
  return [
    {
      id: 'valid',
      label: 'Valid: dua perangkat, interval 1 jam',
      file: 'contoh-valid.csv',
      text: [header, ...hourly(first, 6, 6, '40'), ...hourly(second, 18, 6, '15')].join('\n') + '\n',
    },
    {
      id: 'two',
      label: '2 dari 10 baris tidak valid',
      file: 'contoh-2-salah.csv',
      text: [header, ...hourly('Router Kantor', 0, 10, (index) => (index === 3 ? 'dua' : index === 6 ? '-5' : '10'))].join('\n') + '\n',
    },
    {
      id: 'three',
      label: '3 dari 10 baris tidak valid (diblokir)',
      file: 'contoh-3-salah.csv',
      text:
        [header, ...hourly('Router Kantor', 0, 10, (index) => (index === 1 || index === 4 ? '-1' : index === 7 ? '' : '10'))].join('\n') + '\n',
    },
    {
      id: 'conflict',
      label: 'Nilai berbeda pada interval yang sama',
      file: 'contoh-konflik.csv',
      text: 'timestamp,perangkat,energi_wh\n2026-10-20 00:00,Pompa Sumur,120\n2026-10-20 01:00,Pompa Sumur,0\n2026-10-20 00:00,Pompa Sumur,150\n2026-10-20 02:00,Pompa Sumur,0\n',
    },
    {
      id: 'semi',
      label: 'Titik koma, koma desimal, nama berkutip',
      file: 'contoh-titik-koma.csv',
      text: '﻿waktu;alat;wh\n2026-10-20 07:00;"Lampu; Gudang";12,5\n2026-10-20 08:00;"Lampu; Gudang";12,5\n2026-10-20 09:00;"Lampu; Gudang";1.250,5\n',
    },
    {
      id: 'power',
      label: 'Daya rata-rata (power_w) dengan interval eksplisit',
      file: 'contoh-daya.csv',
      text: 'interval_start,interval_end,asset,power_w\n2026-10-20T08:00:00+07:00,2026-10-20T08:30:00+07:00,Pompa Air,100\n2026-10-20T08:30:00+07:00,2026-10-20T09:00:00+07:00,Pompa Air,0\n',
    },
    {
      id: 'counter',
      label: 'Penghitung kumulatif dengan reset',
      file: 'contoh-penghitung.csv',
      text: 'timestamp,perangkat,cumulative_wh\n2026-10-20 00:00,Mesin Cuci,100\n2026-10-20 01:00,Mesin Cuci,130\n2026-10-20 02:00,Mesin Cuci,5\n',
    },
    {
      id: 'one',
      label: 'Satu baris (interval wajib diisi)',
      file: 'contoh-satu-baris.csv',
      text: 'timestamp,asset,energy_wh\n2026-10-20 10:00,Pemanas Air,450\n',
    },
  ];
}

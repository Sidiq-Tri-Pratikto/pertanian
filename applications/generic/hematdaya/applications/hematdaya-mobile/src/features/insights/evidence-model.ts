import type { Insight } from '@/api/client';
import { formatDate, formatDateRange, formatKwh, formatRatio } from '@/lib/format';

/** The frozen evidence snapshot from 021, as far as the screens read it. Every number stays a decimal string. */
type Week = { start_date: string; end_date: string; mask_kwh: string | null; coverage: string | null; eligible: boolean };

export type Evidence = {
  asset: { name: string; scope_kind: string };
  period: { start_date: string; end_date: string; timezone: string };
  current: Week;
  historical: Week[];
  baseline_kwh: string;
  mad_kwh: string;
  delta_kwh: string;
  resolution_kwh: string;
  threshold_kwh: string;
  mask_coverage: string;
  series: { local_date: string; comparison_kwh: string | null; reference_kwh: string | null }[];
  rule?: string;
  origins?: string[];
};

const SCOPE_KINDS: Record<string, string> = {
  device: 'perangkat',
  group: 'grup',
  circuit: 'sirkuit',
  site_total: 'meter lokasi',
};

export type ChartPoint = { date: string; label: string; current: string | null; reference: string | null };

/** Display strings for the summary, evidence steps, calculation detail and chart. Nothing is recomputed here. */
export function evidenceModel(insight: Insight) {
  const evidence = insight.evidence as Evidence;
  const eligible = evidence.historical.filter((week) => week.eligible);
  const oldest = eligible[eligible.length - 1];
  const newest = eligible[0];
  const periodLabel = formatDateRange(evidence.period.start_date, evidence.period.end_date);
  const simulated = evidence.origins?.includes('simulated') ?? false;
  const current = evidence.current.mask_kwh ?? '0';

  return {
    title: insight.text.title,
    assetName: evidence.asset.name,
    periodLabel,
    timezone: evidence.period.timezone,
    origins: evidence.origins ?? [],
    comparisonLabel: oldest
      ? `Dibanding median ${eligible.length} minggu sebelumnya, ${formatDateRange(oldest.start_date, newest.end_date)}`
      : 'Tanpa periode pembanding',
    qualification: ['Memenuhi kriteria perubahan.', insight.text.pct_note, 'Penyebab belum diketahui.']
      .filter(Boolean)
      .join(' '),
    qualityScope: [
      `Cakupan: ${evidence.asset.name} (${SCOPE_KINDS[evidence.asset.scope_kind] ?? evidence.asset.scope_kind}).`,
      evidence.current.coverage ? `Kelengkapan data periode ini: ${formatRatio(evidence.current.coverage)}.` : null,
      `Waktu yang dibandingkan pada setiap minggu: ${formatRatio(evidence.mask_coverage)} periode.`,
      simulated ? 'Data simulasi untuk demo, bukan pengukuran dari perangkat nyata.' : null,
    ]
      .filter(Boolean)
      .join(' '),
    calculation: [
      { term: 'Periode ini (C)', value: formatKwh(current) },
      { term: 'Median pembanding (B)', value: formatKwh(evidence.baseline_kwh) },
      { term: 'Perhitungan', value: `C − B = ${formatKwh(current)} − ${formatKwh(evidence.baseline_kwh)} = ${formatKwh(evidence.delta_kwh)}` },
      { term: 'Sebaran pembanding (MAD)', value: formatKwh(evidence.mad_kwh) },
      { term: 'Resolusi pengukuran (r)', value: formatKwh(evidence.resolution_kwh) },
      { term: 'Ambang perubahan', value: formatKwh(evidence.threshold_kwh) },
      ...(evidence.rule ? [{ term: 'Aturan', value: evidence.rule }] : []),
      { term: 'Kebijakan', value: `${insight.policy.id} versi ${insight.policy.version}` },
    ],
    points: evidence.series.map<ChartPoint>((day) => ({
      date: formatDate(day.local_date),
      label: formatDate(day.local_date).split(' ')[0],
      current: day.comparison_kwh,
      reference: day.reference_kwh,
    })),
    chartSummary: `${evidence.asset.name} mencatat ${formatKwh(current)} pada ${periodLabel}, dibanding median ${formatKwh(evidence.baseline_kwh)} pada waktu yang sama di minggu-minggu sebelumnya.`,
  };
}

export type EvidenceModel = ReturnType<typeof evidenceModel>;

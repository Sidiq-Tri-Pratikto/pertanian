import { currentCopy } from '@/features/localization/messages';
import { getLocale, type Locale } from '@/features/localization/locale';
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

const EN_SCOPE_KINDS: Record<string, string> = {
  device: 'device', group: 'group', circuit: 'circuit', site_total: 'site meter',
};

function scopeKind(kind: string): string {
  return (getLocale() === 'en' ? EN_SCOPE_KINDS : SCOPE_KINDS)[kind] ?? kind;
}

export function insightCopy(insight: Insight, locale: Locale = getLocale()): Insight['text'] {
  const copy = insight.text_by_locale?.[locale];
  if (copy || locale === 'id') return copy ?? insight.text;
  const evidence = insight.evidence as Evidence;
  return {
    title: `Recorded energy changed for ${evidence.asset.name}`,
    observed: `Recorded energy for the period: ${formatKwh(evidence.current.mask_kwh ?? '0', locale)}.`,
    comparison: `Comparison median: ${formatKwh(evidence.baseline_kwh, locale)}.`,
    unknown: 'The cause of this change is unknown.',
    step: 'Review the readings and the times covered.',
    pct_note: null,
  };
}

export type ChartPoint = { date: string; label: string; current: string | null; reference: string | null };

/** Display strings for the summary, evidence steps, calculation detail and chart. Nothing is recomputed here. */
export function evidenceModel(insight: Insight, locale: Locale = getLocale()) {
  const copy = insightCopy(insight, locale);
  const evidence = insight.evidence as Evidence;
  const eligible = evidence.historical.filter((week) => week.eligible);
  const oldest = eligible[eligible.length - 1];
  const newest = eligible[0];
  const periodLabel = formatDateRange(evidence.period.start_date, evidence.period.end_date);
  const simulated = evidence.origins?.includes('simulated') ?? false;
  const current = evidence.current.mask_kwh ?? '0';

  return {
    title: copy.title,
    assetName: evidence.asset.name,
    periodLabel,
    timezone: evidence.period.timezone,
    origins: evidence.origins ?? [],
    comparisonLabel: oldest
      ? currentCopy(`Dibanding median ${eligible.length} minggu sebelumnya, ${formatDateRange(oldest.start_date, newest.end_date)}`, `Compared with the median from ${eligible.length} earlier weeks, ${formatDateRange(oldest.start_date, newest.end_date)}`)
      : currentCopy("Tanpa periode pembanding", "No comparison period"),
    qualification: [currentCopy("Memenuhi kriteria perubahan.", "The change met the insight rule."), copy.pct_note, currentCopy("Penyebab belum diketahui.", "The cause is unknown.")]
      .filter(Boolean)
      .join(' '),
    qualityScope: [
      currentCopy(`Cakupan: ${evidence.asset.name} (${scopeKind(evidence.asset.scope_kind)}).`, `Scope: ${evidence.asset.name} (${scopeKind(evidence.asset.scope_kind)}).`),
      evidence.current.coverage ? currentCopy(`Kelengkapan data periode ini: ${formatRatio(evidence.current.coverage)}.`, `Data coverage this period: ${formatRatio(evidence.current.coverage)}.`) : null,
      currentCopy(`Waktu yang dibandingkan pada setiap minggu: ${formatRatio(evidence.mask_coverage)} periode.`, `Share of each week used for the comparison: ${formatRatio(evidence.mask_coverage)}.`),
      simulated ? currentCopy("Data simulasi untuk demo, bukan pengukuran dari perangkat nyata.", "Demo readings are simulated.") : null,
    ]
      .filter(Boolean)
      .join(' '),
    calculation: [
      { term: currentCopy("Periode ini (C)", "This period (C)"), value: formatKwh(current) },
      { term: currentCopy("Median pembanding (B)", "Comparison median (B)"), value: formatKwh(evidence.baseline_kwh) },
      { term: currentCopy("Perhitungan", "Calculation"), value: `C − B = ${formatKwh(current)} − ${formatKwh(evidence.baseline_kwh)} = ${formatKwh(evidence.delta_kwh)}` },
      { term: currentCopy("Sebaran pembanding (MAD)", "Comparison spread (MAD)"), value: formatKwh(evidence.mad_kwh) },
      { term: currentCopy("Resolusi pengukuran (r)", "Measurement resolution (r)"), value: formatKwh(evidence.resolution_kwh) },
      { term: currentCopy("Ambang perubahan", "Change threshold"), value: formatKwh(evidence.threshold_kwh) },
      ...(evidence.rule ? [{ term: currentCopy("Aturan", "Rule"), value: evidence.rule }] : []),
      { term: currentCopy("Kebijakan", "Policy"), value: currentCopy(`${insight.policy.id} versi ${insight.policy.version}`, `${insight.policy.id} version ${insight.policy.version}`) },
    ],
    points: evidence.series.map<ChartPoint>((day) => ({
      date: formatDate(day.local_date),
      label: formatDate(day.local_date).split(' ')[0],
      current: day.comparison_kwh,
      reference: day.reference_kwh,
    })),
    chartSummary: currentCopy(`${evidence.asset.name} mencatat ${formatKwh(current)} pada ${periodLabel}, dibanding median ${formatKwh(evidence.baseline_kwh)} pada waktu yang sama di minggu-minggu sebelumnya.`, `${evidence.asset.name} recorded ${formatKwh(current)} in ${periodLabel}. The median for the same times in earlier weeks was ${formatKwh(evidence.baseline_kwh)}.`),
  };
}

export type EvidenceModel = ReturnType<typeof evidenceModel>;

import { scopeIssueCopy } from '@/features/scope/scope-copy';
import { currentCopy } from '@/features/localization/messages';
import type { Summary } from '@/api/client';
import { formatDateRange, formatDateTime, formatGap, formatKwh, formatRatio, localParts } from '@/lib/format';

export type MetricState = 'complete' | 'partial' | 'zero' | 'none' | 'conflict';

export type BerandaModel = {
  periodLabel: string;
  scopeLabel: string;
  timezone: string;
  state: MetricState;
  kwh: string | null;
  qualifier: string | null;
  /** Completeness alone, for the data-quality row. */
  completeness: string | null;
  gaps: string[];
  emptyDetail: string | null;
  issues: string[];
  ranking: { assetId: string; name: string; kwh: string; share: string | null; width: number; coverage: string }[];
  totalLabel: string | null;
  latest: string | null;
  origins: string[];
  allocated: boolean;
};

/**
 * The origins a screen names beside its numbers. Every demo workspace is simulated, so its tag stays even for a
 * period without readings.
 */
export function shownOrigins(origins: string[], scenarioId: string | undefined): string[] {
  return origins.length || scenarioId === 'empty' ? origins : ['simulated'];
}

/** Turn a summary into what S03 shows, in reading order. Every value comes from the service's strings. */
export function berandaModel(summary: Summary): BerandaModel {
  const { window, coverage, scope } = summary;
  const tz = window.timezone;
  const started = window.effective_end !== window.start;
  const running = window.is_current && started ? currentCopy(` · sampai ${localParts(window.effective_end, tz).time} (berjalan)`, ` · through ${localParts(window.effective_end, tz).time.replace('.', ':')} (in progress)`) : '';
  const gaps = summary.assets.flatMap((asset) =>
    asset.gaps.slice(0, 1).map((gap) => `${asset.name}: ${formatGap(gap.start, gap.end, tz)}`),
  );
  const minimum = coverage.minimum;
  let state: MetricState;
  let emptyDetail: string | null = null;
  if (summary.energy_unavailable_reason === 'scope_conflict') {
    state = 'conflict';
  } else if (summary.energy_kwh === null) {
    state = 'none';
    emptyDetail =
      window.effective_end === window.start
        ? currentCopy(`Periode ini belum dimulai pada waktu ${formatDateTime(window.effective_end, tz)}. Tidak ditampilkan sebagai 0 kWh.`, `This period starts after ${formatDateTime(window.effective_end, tz)}. Energy is unavailable.`)
        : summary.energy_unavailable_reason === 'insufficient_resolution'
          ? currentCopy("Resolusi data belum cukup untuk memecah periode ini. Tidak ditampilkan sebagai 0 kWh.", "The readings are too far apart to break down this period. Energy is unavailable.")
          : currentCopy("Belum ada pengukuran pada periode ini. Tidak ditampilkan sebagai 0 kWh.", "No readings for this period. Energy is unavailable.");
  } else if (minimum !== null && minimum !== '1.000') {
    state = 'partial';
  } else if (summary.energy_kwh === '0.000') {
    state = 'zero';
  } else {
    state = 'complete';
  }
  const completeness = minimum === null ? null : currentCopy(`Kelengkapan data: ${formatRatio(minimum)} periode`, `Data coverage: ${formatRatio(minimum)} of the period`);
  const qualifier =
    state === 'partial'
      ? currentCopy(`Sebagian data belum tersedia · ${completeness}`, `Some data is missing · ${completeness}`)
      : state === 'zero'
        ? currentCopy(`Nol terukur dengan data lengkap · ${completeness}`, `Measured zero with complete data · ${completeness}`)
        : state === 'complete'
          ? completeness
          : null;
  const counted = summary.assets.filter((asset) => asset.energy_kwh !== null);
  return {
    periodLabel: `${formatDateRange(window.start_date, window.end_date)}${running}`,
    scopeLabel: currentCopy(`Cakupan pengukuran: ${scope.included.length} perangkat`, `Devices in scope: ${scope.included.length}`),
    timezone: tz,
    state,
    kwh: summary.energy_kwh === null ? null : formatKwh(summary.energy_kwh),
    qualifier,
    completeness: minimum === null ? null : currentCopy(`${formatRatio(minimum)} periode`, `${formatRatio(minimum)} of the period`),
    gaps: state === 'partial' ? gaps.slice(0, 2) : gaps.slice(0, 3),
    emptyDetail,
    issues: scope.issues.map((issue) => scopeIssueCopy(issue, [...scope.included, ...scope.excluded])),
    ranking:
      state === 'conflict'
        ? []
        : counted.map((asset) => ({
            assetId: asset.asset_id,
            name: asset.name,
            kwh: formatKwh(asset.energy_kwh!),
            share: asset.share_percent,
            // Layout only: bar length may read the number; no displayed value comes from it.
            width: asset.share_percent === null ? 0 : Number(asset.share_percent),
            coverage: asset.coverage === null ? '' : formatRatio(asset.coverage),
          })),
    totalLabel: summary.energy_kwh === null ? null : formatKwh(summary.energy_kwh),
    latest: summary.latest_measurement_at ? formatDateTime(summary.latest_measurement_at, tz) : null,
    origins: summary.origins,
    allocated: coverage.allocated_estimate,
  };
}

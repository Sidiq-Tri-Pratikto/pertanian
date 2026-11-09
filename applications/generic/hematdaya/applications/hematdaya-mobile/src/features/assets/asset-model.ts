import { currentCopy } from '@/features/localization/messages';
import type { Asset, AssetDetail, AssetEnergy, ScopeKind, SourceFreshness, SourceOrigin, Summary, TransportStatus } from '@/api/client';
import { berandaModel, type BerandaModel } from '@/features/energy/beranda-model';
import {
  formatAssetMeta,
  formatCadence,
  formatDateTime,
  formatGap,
  formatKwh,
  formatRatio,
  formatResolution,
  type AssetKind,
} from '@/lib/format';

const KIND_BY_SCOPE: Record<ScopeKind, AssetKind> = { device: 'device', group: 'group', circuit: 'circuit', site_total: 'meter' };

const FULL_COVERAGE = '1.000';
const MEASURED_ZERO = '0.000';

export type AssetRowQuality = 'complete' | 'partial' | 'unavailable';

export type AssetRowModel = {
  assetId: string;
  name: string;
  kind: AssetKind;
  location: string | null;
  category: string | null;
  kwh: string | null;
  quality: AssetRowQuality;
  qualityLabel: string;
  /** One line per unresolved source. Never a sum. */
  sources: string[];
  stale: boolean;
};

function sourceLines(row: AssetEnergy | undefined): string[] {
  return (row?.conflict_sources ?? []).map((source) => `${source.label}: ${formatKwh(source.energy_kwh)}`);
}

function unavailableLabel(row: AssetEnergy): string {
  if (row.conflict_sources) {
    return currentCopy("Lebih dari satu sumber · nilai tidak dijumlahkan", "Multiple sources · no combined total");
  }
  if (row.energy_unavailable_reason === 'insufficient_resolution') {
    return currentCopy("Resolusi data belum cukup untuk periode ini", "Data resolution is too low for this period");
  }
  return row.energy_unavailable_reason === 'no_data' ? currentCopy("Belum ada data pada periode ini", "No data for this period yet") : currentCopy("Data belum tersedia", "Data unavailable");
}

function rowQuality(row: AssetEnergy): Pick<AssetRowModel, 'quality' | 'qualityLabel'> {
  if (row.conflict_sources || row.energy_kwh === null || row.coverage === null) {
    return { quality: 'unavailable', qualityLabel: unavailableLabel(row) };
  }
  if (row.coverage !== FULL_COVERAGE) {
    return { quality: 'partial', qualityLabel: currentCopy(`Kelengkapan data: ${formatRatio(row.coverage)} periode`, `Data coverage: ${formatRatio(row.coverage)} of the period`) };
  }
  return {
    quality: 'complete',
    qualityLabel: row.energy_kwh === MEASURED_ZERO ? currentCopy("Nol terukur dengan data lengkap", "Measured zero with complete data") : currentCopy(`Kelengkapan data: ${formatRatio(row.coverage)} periode`, `Data coverage: ${formatRatio(row.coverage)} of the period`),
  };
}

/** One S04 row from the summary's row, the asset's facts and the service's stale notices. Nothing is computed here. */
export function assetRowModel(row: AssetEnergy, asset: Asset | undefined, staleIds: ReadonlySet<string>): AssetRowModel {
  return {
    assetId: row.asset_id,
    name: asset?.name ?? row.name,
    kind: KIND_BY_SCOPE[row.scope_kind],
    location: asset?.location ?? null,
    category: asset?.category ?? null,
    kwh: row.energy_kwh === null || row.conflict_sources ? null : formatKwh(row.energy_kwh),
    ...rowQuality(row),
    sources: sourceLines(row),
    stale: staleIds.has(row.asset_id),
  };
}

/** Assets the service calls stale. The client never compares a timestamp with a cadence. */
export function staleAssetIds(sources: SourceFreshness[] | undefined): Set<string> {
  return new Set(sources?.filter((source) => source.state === 'stale').map((source) => source.asset_id));
}

function originLabels(): Record<SourceOrigin, string> {
  return {
  simulated: currentCopy('Simulasi', 'Simulated'),
  import: currentCopy('Impor CSV', 'CSV import'),
  dataset_replay: currentCopy('Putar ulang dataset', 'Dataset replay'),
  live: currentCopy('Langsung', 'Live'),
};
}

function transportLabels(): Record<TransportStatus, string | null> {
  return {
  none: null,
  simulated_live: currentCopy('Simulasi koneksi', 'Simulated connection'),
  live: currentCopy('Pengukuran langsung', 'Live metering'),
  historical: currentCopy('Data historis', 'Historical data'),
};
}

function detailScopeLabels(): Record<AssetKind, string> {
  return {
  device: currentCopy('Cakupan pengukuran: 1 perangkat (hanya beban yang diukur sumber ini)', 'Measurement scope: one device (the load this source measures)'),
  meter: currentCopy('Cakupan pengukuran: 1 meter lokasi', 'Measurement scope: one site meter'),
  group: currentCopy('Cakupan pengukuran: 1 grup', 'Measurement scope: one group'),
  circuit: currentCopy('Cakupan pengukuran: 1 sirkuit', 'Measurement scope: one circuit'),
};
}

export function assetScopeLabel(scope: ScopeKind): string {
  return detailScopeLabels()[KIND_BY_SCOPE[scope]];
}

/** Reachable even without a period summary. Only metadata is known. */
export function unrankedAssetRow(asset: Asset, archived: boolean): AssetRowModel {
  return {
    assetId: asset.id, name: asset.name, kind: KIND_BY_SCOPE[asset.scope_kind],
    location: asset.location, category: asset.category, kwh: null, quality: 'unavailable',
    qualityLabel: archived ? currentCopy("Diarsipkan · riwayat tetap tersimpan", "Archived · history retained") : currentCopy("Nilai periode ini belum tersedia", "Value unavailable for this period"),
    sources: [], stale: false,
  };
}

export function originLabel(origin: string): string {
  return originLabels()[origin as SourceOrigin] ?? origin;
}

export type SourceRow = {
  id: string;
  label: string;
  origin: string;
  interval: string;
  /** Null until the site's timezone is known, because a date without it would be wrong. */
  effective: string | null;
  role: string;
};

/** One entry per binding, past bindings included, because the service returns them. */
export function assetSourceRows(asset: AssetDetail | undefined, timezone: string | null): SourceRow[] {
  return (asset?.bindings ?? []).flatMap((binding) => {
    const source = asset?.sources.find((candidate) => candidate.id === binding.source_id);
    if (!source) {
      return [];
    }
    const transport = transportLabels()[source.transport_status];
    const start = timezone && currentCopy(`mulai ${formatDateTime(binding.effective_from, timezone)}`, `from ${formatDateTime(binding.effective_from, timezone)}`);
    const end = timezone && binding.effective_to ? currentCopy(` sampai ${formatDateTime(binding.effective_to, timezone)}`, ` through ${formatDateTime(binding.effective_to, timezone)}`) : '';
    return [
      {
        id: binding.id,
        label: source.label,
        origin: [originLabel(source.origin), transport].filter(Boolean).join(' · '),
        interval: [
          source.cadence_seconds === null ? currentCopy("interval tidak diketahui", "interval unknown") : formatCadence(source.cadence_seconds),
          source.resolution_mwh === null ? currentCopy("resolusi tidak diketahui", "resolution unknown") : currentCopy(`resolusi ${formatResolution(source.resolution_mwh)}`, `resolution ${formatResolution(source.resolution_mwh)}`),
        ].join(' · '),
        effective: start ? `${start}${end}` : null,
        role: binding.authoritative ? currentCopy("Sumber acuan", "Reference source") : currentCopy("Belum dipilih sebagai sumber acuan", "No reference source selected"),
      },
    ];
  });
}

export type AssetDetailModel = Pick<
  BerandaModel,
  'periodLabel' | 'timezone' | 'state' | 'kwh' | 'qualifier' | 'completeness' | 'emptyDetail' | 'latest' | 'allocated' | 'scopeLabel' | 'gaps' | 'issues'
> & {
  name: string;
  meta: string;
  /** One line per unresolved source. */
  sources: string[];
  sourceRows: SourceRow[];
  /** From the asset's sources, because a summary's `origins` is empty on a no-data period and on a conflict. */
  origins: string[];
};

/**
 * S06 from a one-asset summary. Its row is `assets[0]`. `share_percent` and `scope.excluded` are true for that
 * request and misleading on this screen, so neither is passed on.
 */
export function assetDetailModel(summary: Summary, asset: AssetDetail | undefined): AssetDetailModel {
  const base = berandaModel(summary);
  const row = summary.assets[0] as AssetEnergy | undefined;
  const kind = KIND_BY_SCOPE[row?.scope_kind ?? asset?.scope_kind ?? 'device'];
  return {
    periodLabel: base.periodLabel,
    timezone: base.timezone,
    state: row?.conflict_sources ? 'conflict' : base.state,
    kwh: base.kwh,
    qualifier: base.qualifier,
    completeness: base.completeness,
    emptyDetail: base.emptyDetail,
    latest: base.latest,
    allocated: base.allocated,
    scopeLabel: detailScopeLabels()[kind],
    gaps: (row?.gaps ?? []).map((gap) => formatGap(gap.start, gap.end, base.timezone)),
    issues: base.issues,
    name: asset?.name ?? row?.name ?? '',
    meta: formatAssetMeta(kind, asset?.location ?? null, asset?.category ?? null),
    sources: sourceLines(row),
    sourceRows: assetSourceRows(asset, base.timezone),
    origins: [...new Set((asset?.sources ?? []).map((source) => source.origin))],
  };
}

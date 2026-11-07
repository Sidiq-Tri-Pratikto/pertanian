import type { Asset, AssetDetail, AssetEnergy, InsightNotice, Summary } from '@/api/client';
import { assetDetailModel, assetRowModel, staleAssetIds } from '@/features/assets/asset-model';
import { shownOrigins } from '@/features/energy/beranda-model';

import recorded from './fixtures/assets.json';

// Recorded from the merged service at 6563a2f on 2026-11-07, as tests/perangkat.test.tsx says.
type Scenario = {
  summary: Summary;
  assets: { items: Asset[] };
  notices: InsightNotice[];
  details: Record<string, { asset: AssetDetail; summary: Summary }>;
};
const scenarios = recorded as unknown as Record<string, Scenario>;

function siteRow(scenario: string, name: string): { row: AssetEnergy; asset: Asset } {
  const { summary, assets } = scenarios[scenario];
  return {
    row: summary.assets.find((item) => item.name === name)!,
    asset: assets.items.find((item) => item.name === name)!,
  };
}

function detail(scenario: string, name: string, notices: InsightNotice[] = scenarios[scenario].notices) {
  const entry = scenarios[scenario].details[name];
  return assetDetailModel(entry.summary, entry.asset, notices);
}

const NONE = new Set<string>();

describe('assetRowModel', () => {
  it('shows a value with full coverage', () => {
    const { row, asset } = siteRow('h-base', 'Kulkas');

    expect(assetRowModel(row, asset, NONE)).toEqual({
      assetId: row.asset_id,
      name: 'Kulkas',
      kind: 'device',
      location: 'Dapur',
      category: 'Pendingin makanan',
      kwh: '8,400 kWh',
      quality: 'complete',
      qualityLabel: 'Kelengkapan data: 100% periode',
      sources: [],
      stale: false,
    });
  });

  it('shows partial coverage beside the value', () => {
    const { row, asset } = siteRow('h-learning-partial', 'Pompa Air');

    expect(assetRowModel(row, asset, NONE)).toMatchObject({
      kwh: '1,500 kWh',
      quality: 'partial',
      qualityLabel: 'Kelengkapan data: 71,4% periode',
    });
  });

  it('reads a measured zero differently from a gap', () => {
    const { row, asset } = siteRow('h-zero', 'Kulkas');

    expect(assetRowModel(row, asset, NONE)).toMatchObject({
      kwh: '0,000 kWh',
      quality: 'complete',
      qualityLabel: 'Nol terukur dengan data lengkap',
    });
  });

  it('never sums two sources, and gives one line per source', () => {
    const { row, asset } = siteRow('h-scope', 'Kulkas');

    expect(assetRowModel(row, asset, NONE)).toMatchObject({
      kwh: null,
      quality: 'unavailable',
      qualityLabel: 'Lebih dari satu sumber · nilai tidak dijumlahkan',
      sources: ['Colokan simulasi Kulkas (sumber kedua): 1,000 kWh', 'Sumber demo (simulasi): 1,000 kWh'],
    });
  });

  it.each([
    ['insufficient_resolution', 'Resolusi data belum cukup untuk periode ini'],
    ['no_data', 'Belum ada data pada periode ini'],
    ['future_reason', 'Data belum tersedia'],
  ])('gives a null value with reason %s no zero', (reason, label) => {
    const { row, asset } = siteRow('h-base', 'Kulkas');
    const crafted = { ...row, energy_kwh: null, coverage: null, energy_unavailable_reason: reason };

    expect(assetRowModel(crafted, asset, NONE)).toMatchObject({ kwh: null, quality: 'unavailable', qualityLabel: label });
  });

  it.each([
    ['device', 'device'],
    ['group', 'group'],
    ['circuit', 'circuit'],
    ['site_total', 'meter'],
  ] as const)('maps scope kind %s to %s', (scopeKind, kind) => {
    const { row, asset } = siteRow('h-base', 'Kulkas');

    expect(assetRowModel({ ...row, scope_kind: scopeKind }, asset, NONE).kind).toBe(kind);
  });

  it('renders a summary row with no asset row, with no location or category', () => {
    const { row } = siteRow('h-base', 'Kulkas');

    expect(assetRowModel(row, undefined, NONE)).toMatchObject({ location: null, category: null, kwh: '8,400 kWh' });
  });

  it('adds stale to a partial row and replaces nothing', () => {
    const { row, asset } = siteRow('h-stale-offline', 'Router');

    expect(assetRowModel(row, asset, staleAssetIds(scenarios['h-stale-offline'].notices))).toMatchObject({
      kwh: '1,620 kWh',
      quality: 'partial',
      qualityLabel: 'Kelengkapan data: 96,4% periode',
      stale: true,
    });
  });
});

describe('staleAssetIds', () => {
  it('keeps only stale notices with an asset', () => {
    const { row } = siteRow('h-stale-offline', 'Router');
    const notices: InsightNotice[] = [
      ...scenarios['h-stale-offline'].notices,
      { id: 'x', kind: 'stale', asset_id: null, title: 'x', body: 'x' },
    ];

    expect([...staleAssetIds(notices)]).toEqual([row.asset_id]);
  });

  it('ignores a partial notice', () => {
    expect(scenarios['h-learning-partial'].notices.length).toBeGreaterThan(0);
    expect(staleAssetIds(scenarios['h-learning-partial'].notices).size).toBe(0);
  });
});

describe('assetDetailModel', () => {
  it('describes one asset with no share', () => {
    const model = detail('h-base', 'Kulkas');

    expect(model).toMatchObject({
      name: 'Kulkas',
      meta: 'Perangkat · Dapur · Pendingin makanan',
      periodLabel: '19–25 Oktober 2026',
      timezone: 'Asia/Jakarta',
      scopeLabel: 'Cakupan pengukuran: 1 perangkat (hanya beban yang diukur sumber ini)',
      state: 'complete',
      kwh: '8,400 kWh',
      qualifier: 'Kelengkapan data: 100% periode',
      origins: ['simulated'],
    });
    expect(JSON.stringify(model)).not.toContain('100,00');
    expect(model).not.toHaveProperty('share');
    expect(model).not.toHaveProperty('share_percent');
  });

  it('gives every gap with no name prefix', () => {
    expect(detail('h-learning-partial', 'Pompa Air')).toMatchObject({ state: 'partial', gaps: ['24–25 Oktober 2026'] });
  });

  it('gives a conflicted asset one line per source and no total', () => {
    const model = detail('h-scope', 'Kulkas');

    expect(model.state).toBe('conflict');
    expect(model.kwh).toBeNull();
    expect(model.sources).toEqual(['Colokan simulasi Kulkas (sumber kedua): 1,000 kWh', 'Sumber demo (simulasi): 1,000 kWh']);
    expect(model.issues).toEqual([
      'Kulkas memiliki lebih dari satu sumber untuk beban yang sama. Pilih sumber acuan; nilainya tidak dijumlahkan.',
    ]);
    expect(model.origins).toEqual(['simulated']);
    expect(model.sourceRows.map((row) => row.role)).toEqual([
      'Belum dipilih sebagai sumber acuan',
      'Belum dipilih sebagai sumber acuan',
    ]);
  });

  it('labels a meter by its kind', () => {
    expect(detail('h-scope', 'Meter utama').scopeLabel).toBe('Cakupan pengukuran: 1 meter lokasi');
  });

  it.each([
    ['group', 'Cakupan pengukuran: 1 grup'],
    ['circuit', 'Cakupan pengukuran: 1 sirkuit'],
  ] as const)('labels a %s by its kind', (kind, label) => {
    const entry = scenarios['h-base'].details.Kulkas;
    const summary: Summary = {
      ...entry.summary,
      assets: entry.summary.assets.map((row) => ({ ...row, scope_kind: kind })),
    };

    expect(assetDetailModel(summary, entry.asset, []).scopeLabel).toBe(label);
  });

  it('lists a source with its origin, interval, resolution, range and role', () => {
    expect(detail('h-base', 'Kulkas').sourceRows).toEqual([
      expect.objectContaining({
        label: 'Sumber demo (simulasi)',
        origin: 'Simulasi',
        interval: '1 jam · resolusi 0,001 kWh',
        effective: 'mulai 28 September 2026 00.00',
        role: 'Sumber acuan',
      }),
    ]);
  });

  it('adds the transport label', () => {
    expect(detail('h-stale-offline', 'Router').sourceRows[0].origin).toBe('Simulasi · Simulasi koneksi');
  });

  it('says what it does not know about an imported source', () => {
    expect(detail('imported', 'Kulkas').sourceRows[0]).toMatchObject({
      origin: 'Impor CSV · Data historis',
      interval: 'interval tidak diketahui · resolusi tidak diketahui',
    });
  });

  it('ends an effective range when the binding ended', () => {
    const entry = scenarios['h-base'].details.Kulkas;
    const asset: AssetDetail = {
      ...entry.asset,
      bindings: entry.asset.bindings.map((binding) => ({ ...binding, effective_to: '2026-10-01T17:00:00Z' })),
    };

    expect(assetDetailModel(entry.summary, asset, []).sourceRows[0].effective).toBe(
      'mulai 28 September 2026 00.00 sampai 2 Oktober 2026 00.00',
    );
  });

  it('keeps only the stale notice for this asset', () => {
    const router = detail('h-stale-offline', 'Router');
    const kulkas = detail('h-stale-offline', 'Kulkas');

    expect(router.staleNotices.map((notice) => notice.title)).toEqual(['Data belum diperbarui · Router']);
    expect(kulkas.staleNotices).toEqual([]);
  });

  it('works from the summary alone', () => {
    const entry = scenarios['h-base'].details.Kulkas;

    expect(assetDetailModel(entry.summary, undefined, [])).toMatchObject({
      name: 'Kulkas',
      meta: 'Perangkat',
      sourceRows: [],
      origins: [],
    });
  });
});

describe('shownOrigins', () => {
  it('keeps what the service sent', () => {
    expect(shownOrigins(['import'], 'empty')).toEqual(['import']);
  });

  it('labels a demo period with no readings as simulated', () => {
    expect(shownOrigins([], 'h-base')).toEqual(['simulated']);
  });

  it('adds nothing to an empty workspace', () => {
    expect(shownOrigins([], 'empty')).toEqual([]);
  });
});

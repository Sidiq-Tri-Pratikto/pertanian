import { StyleSheet, View } from 'react-native';

import type { AssetEnergy, SourceFreshness } from '@/api/client';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { formatCadence, formatDateTime } from '@/lib/format';

type Row = { id?: string; term: string; value: string; detail?: string };

/** Capture time belongs to the source and remains independent of the client's fetch time. */
export function freshnessRows(
  sources: SourceFreshness[] | undefined, timezone: string, assets: Pick<AssetEnergy, 'asset_id' | 'name'>[] = [],
): Row[] {
  if (sources === undefined) return [{ term: 'Kesegaran sumber', value: 'Belum diketahui' }];
  return sources.flatMap((source): Row[] => {
    const { state, last_capture_at: last, cadence_seconds: cadence, historical_range: range } = source;
    if (state === 'stale' && last && cadence) {
      const asset = assets.find((row) => row.asset_id === source.asset_id);
      return [{
        id: `${source.asset_id}:${source.source_id}`,
        term: `Data belum diperbarui · ${asset?.name ?? source.label}`,
        value: `Pembacaan sumber terakhir: ${formatDateTime(last, timezone)} (${timezone})`,
        detail: `Interval ${formatCadence(cadence)}. Status perangkat tidak diketahui.`,
      }];
    }
    if (state === 'historical' && range && last) {
      return [{
        id: `${source.asset_id}:${source.source_id}`,
        term: source.origin === 'import' ? 'Data historis · Impor CSV' : `Data historis · ${source.label}`,
        value: `Pembacaan historis terakhir: ${formatDateTime(last, timezone)} (${timezone})`,
        detail: `Rentang tercatat: ${formatDateTime(range.start, timezone)} – ${formatDateTime(range.end, timezone)}`,
      }];
    }
    return [];
  });
}

/** Separate rows for completeness, freshness and provenance. Never one score, never "akurat". */
export function HDDataQuality({ rows }: { rows: Row[] }) {
  return (
    <View role="list" aria-label="Kualitas data" style={styles.block}>
      {rows.map((row) => (
        <View key={row.id ?? row.term} role="listitem" style={styles.row}>
          <HDText variant="labelStrong">{row.term}</HDText>
          <HDText>{row.value}</HDText>
          {row.detail ? (
            <HDText variant="label" tone="secondary">
              {row.detail}
            </HDText>
          ) : null}
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({ block: { gap: tokens.space.stack }, row: { gap: tokens.space['4'] } });

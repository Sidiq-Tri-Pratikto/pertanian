import { StyleSheet, View } from 'react-native';

import type { Summary } from '@/api/client';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { formatKwh, formatRatio } from '@/lib/format';

export function scopeEnergy(value: string | null, reason?: string | null): string {
  if (value !== null) return formatKwh(value);
  switch (reason) {
    case 'scope_conflict': return 'Total gabungan belum dapat dihitung';
    case 'source_conflict': return 'Sumber bertentangan';
    case 'insufficient_resolution': return 'Resolusi data belum cukup';
    default: return 'Energi belum tersedia';
  }
}

export function scopeExclusion(reason: string): string {
  return reason === 'archived' ? 'Diarsipkan' : reason === 'not_selected' ? 'Di luar pilihan' : 'Di luar cakupan pengukuran';
}

/** Period figures and membership as the service returned them, with physical scope separate from time coverage. */
export function HDScopeSummary({ summary }: { summary: Summary }) {
  const { scope, coverage, assets } = summary;
  return (
    <View style={styles.section}>
      <HDText variant="labelStrong">{`Cakupan pengukuran: ${scope.included.length} perangkat`}</HDText>
      <HDText variant="label">
        {`Kelengkapan data: ${coverage.minimum === null ? 'belum tersedia' : `${formatRatio(coverage.minimum)} periode`}`}
      </HDText>
      {scope.valid ? (
        <HDText variant="section">{scopeEnergy(summary.energy_kwh, summary.energy_unavailable_reason)}</HDText>
      ) : (
        <HDNotice tone="attention" title="Total gabungan belum dapat dihitung">
          {scope.issues.map((issue) => <HDText key={`${issue.type}:${issue.asset_ids.join(',')}`}>{issue.message}</HDText>)}
        </HDNotice>
      )}
      <HDText variant="labelStrong">Termasuk dalam pengukuran</HDText>
      {assets.length === 0 ? <HDText>Belum ada perangkat dalam pengukuran ini.</HDText> : null}
      {assets.map((asset) => (
        <View key={asset.asset_id} style={styles.list}>
          <HDText>{`${asset.name} · ${scopeEnergy(asset.energy_kwh, asset.energy_unavailable_reason)}`}</HDText>
          {asset.conflict_sources?.map((source) => (
            <HDText key={source.source_id} tone="secondary">
              {`${source.label} · ${formatKwh(source.energy_kwh)}`}
            </HDText>
          ))}
        </View>
      ))}
      {scope.excluded.length > 0 ? <>
        <HDText variant="labelStrong">Di luar pengukuran</HDText>
        {scope.excluded.map((asset) => <HDText key={asset.asset_id}>{`${asset.name} · ${scopeExclusion(asset.reason)}`}</HDText>)}
      </> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  section: { gap: tokens.space.stackTight },
  list: { gap: tokens.space['4'] },
});

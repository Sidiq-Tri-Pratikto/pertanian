import { scopeIssueCopy } from '@/features/scope/scope-copy';
import { useCopy, currentCopy } from '@/features/localization/messages';
import { StyleSheet, View } from 'react-native';

import type { Summary } from '@/api/client';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { formatKwh, formatRatio } from '@/lib/format';

export function scopeEnergy(value: string | null, reason?: string | null): string {
  if (value !== null) return formatKwh(value);
  switch (reason) {
    case 'scope_conflict': return currentCopy("Total gabungan belum dapat dihitung", "Combined total unavailable");
    case 'source_conflict': return currentCopy("Sumber bertentangan", "Conflicting sources");
    case 'insufficient_resolution': return currentCopy("Resolusi data belum cukup", "Data resolution is too low");
    default: return currentCopy("Energi belum tersedia", "Energy data unavailable");
  }
}

export function scopeExclusion(reason: string): string {
  return reason === 'archived' ? currentCopy("Diarsipkan", "Archived") : reason === 'not_selected' ? currentCopy("Di luar pilihan", "Outside the selection") : currentCopy("Di luar cakupan pengukuran", "Outside measurement scope");
}

/** Period figures and membership as the service returned them, with physical scope separate from time coverage. */
export function HDScopeSummary({ summary }: { summary: Summary }) {
  const say = useCopy();
  const { scope, coverage, assets } = summary;
  return (
    <View style={styles.section}>
      <HDText variant="labelStrong">{say(`Cakupan pengukuran: ${scope.included.length} perangkat`, `Devices in scope: ${scope.included.length}`)}</HDText>
      <HDText variant="label">
        {say(`Kelengkapan data: ${coverage.minimum === null ? 'belum tersedia' : `${formatRatio(coverage.minimum)} periode`}`, `Data coverage: ${coverage.minimum === null ? 'unavailable' : `${formatRatio(coverage.minimum)} of the period`}`)}
      </HDText>
      {scope.valid ? (
        <HDText variant="section">{scopeEnergy(summary.energy_kwh, summary.energy_unavailable_reason)}</HDText>
      ) : (
        <HDNotice tone="attention" title={say("Total gabungan belum dapat dihitung", "Combined total unavailable")}>
          {scope.issues.map((issue) => <HDText key={`${issue.type}:${issue.asset_ids.join(',')}`}>{scopeIssueCopy(issue, [...scope.included, ...scope.excluded])}</HDText>)}
        </HDNotice>
      )}
      <HDText variant="labelStrong">{say("Termasuk dalam pengukuran", "Included in measurement")}</HDText>
      {assets.length === 0 ? <HDText>{say("Belum ada perangkat dalam pengukuran ini.", "No devices in this scope yet.")}</HDText> : null}
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
        <HDText variant="labelStrong">{say("Di luar pengukuran", "Outside measurement")}</HDText>
        {scope.excluded.map((asset) => <HDText key={asset.asset_id}>{`${asset.name} · ${scopeExclusion(asset.reason)}`}</HDText>)}
      </> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  section: { gap: tokens.space.stackTight },
  list: { gap: tokens.space['4'] },
});

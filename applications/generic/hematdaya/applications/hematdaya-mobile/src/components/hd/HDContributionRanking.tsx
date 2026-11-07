import { StyleSheet, View } from 'react-native';

import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { formatPercent } from '@/lib/format';

type Item = { name: string; kwh: string; share: string | null; width: number };

/** Sorted bars on a shared zero baseline with direct labels. The largest is not waste; values come from the service. */
export function HDContributionRanking({ items, periodLabel, denominatorLabel }: { items: Item[]; periodLabel: string; denominatorLabel: string }) {
  const shares = items.some((item) => item.share !== null);
  return (
    <View style={styles.block}>
      <HDText variant="section">Kontributor terbesar</HDText>
      <HDText variant="label" tone="secondary">
        {periodLabel} · {denominatorLabel}
      </HDText>
      {!shares ? (
        <HDText tone="secondary">Total energi nol, sehingga tidak ada persentase kontribusi.</HDText>
      ) : null}
      <View role="list" style={styles.block}>
        {items.map((item) => (
          <View key={item.name} role="listitem" style={styles.item}>
            <HDText variant="bodyStrong">{item.name}</HDText>
            <HDText variant="label">
              {item.kwh}
              {item.share !== null ? ` · ${formatPercent(item.share)}` : ''}
            </HDText>
            <View aria-hidden style={styles.track}>
              <View style={[styles.bar, { width: `${Math.min(100, Math.max(0, item.width))}%` }]} />
            </View>
          </View>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  block: { gap: tokens.space.stackTight },
  item: { gap: tokens.space['4'] },
  track: { height: tokens.space['12'], backgroundColor: tokens.color.chartTrack, borderRadius: tokens.radius['8'] },
  bar: { height: '100%', backgroundColor: tokens.color.chartCurrent, borderRadius: tokens.radius['8'] },
});

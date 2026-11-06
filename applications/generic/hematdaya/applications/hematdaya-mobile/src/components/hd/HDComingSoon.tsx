import { StyleSheet, View } from 'react-native';

import { HDIcon } from '@/components/hd/HDIcon';
import { HDTag } from '@/components/hd/HDTag';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import type { Feature } from '@/features/registry';

/** Honest placeholder: what the feature will do, with no sample data and no working-looking controls. */
export function HDComingSoon({ feature }: { feature: Feature }) {
  return (
    <View style={styles.block}>
      <HDTag>Segera hadir</HDTag>
      <HDText>{feature.summary}</HDText>
      <View style={styles.block}>
        <HDText variant="labelStrong">Yang akan tersedia</HDText>
        {feature.points.map((point) => (
          <View key={point} style={styles.point}>
            <HDIcon name="clock" size="small" color={tokens.color.textSecondary} />
            <HDText style={styles.pointText}>{point}</HDText>
          </View>
        ))}
      </View>
      <HDText variant="label" tone="secondary">
        Fitur ini belum tersedia pada versi ini, dan belum ada data yang diproses.
      </HDText>
      {__DEV__ ? (
        <HDText variant="caption" tone="secondary">
          Spesifikasi: {feature.specs.join(', ')} · Layar: {feature.screens.join(', ')}
        </HDText>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  block: { gap: tokens.space.stack },
  point: { flexDirection: 'row', gap: tokens.space.stackTight },
  pointText: { flex: 1 },
});

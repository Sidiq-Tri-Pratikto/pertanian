import { useLocale } from '@/features/localization/locale';
import { localizedFeature } from '@/features/registry';
import { useCopy } from '@/features/localization/messages';
import { StyleSheet, View } from 'react-native';

import { HDIcon } from '@/components/hd/HDIcon';
import { HDTag } from '@/components/hd/HDTag';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import type { Feature } from '@/features/registry';

/** Honest placeholder: what the feature will do, with no sample data and no working-looking controls. */
export function HDComingSoon({ feature: original }: { feature: Feature }) {
  const say = useCopy();
  const feature = localizedFeature(original, useLocale());
  return (
    <View style={styles.block}>
      <HDTag>{say("Segera hadir", "Coming soon")}</HDTag>
      <HDText>{feature.summary}</HDText>
      <View style={styles.block}>
        <HDText variant="labelStrong">{say("Yang akan tersedia", "What’s planned")}</HDText>
        {feature.points.map((point) => (
          <View key={point} style={styles.point}>
            <HDIcon name="clock" size="small" color={tokens.color.textSecondary} />
            <HDText style={styles.pointText}>{point}</HDText>
          </View>
        ))}
      </View>
      <HDText variant="label" tone="secondary">{say("Fitur ini belum tersedia pada versi ini, dan belum ada data yang diproses.", "This feature is planned for a later release.")}</HDText>
      {__DEV__ ? (
        <HDText variant="caption" tone="secondary">{say("Spesifikasi:", "Spec:")} {feature.specs.join(', ')} {say("· Layar:", "· Screen:")} {feature.screens.join(', ')}
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

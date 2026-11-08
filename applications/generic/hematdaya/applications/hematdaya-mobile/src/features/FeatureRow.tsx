import { useCopy } from '@/features/localization/messages';
import { useLocale } from '@/features/localization/locale';
import { localizedFeature } from '@/features/registry';
import { Pressable, StyleSheet, View } from 'react-native';

import { HDIcon } from '@/components/hd/HDIcon';
import { HDTag } from '@/components/hd/HDTag';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import type { Feature } from '@/features/registry';

type FeatureRowProps = { feature: Feature; onPress: () => void };

/** One planned feature as a single row link. */
export function FeatureRow({ feature: original, onPress }: FeatureRowProps) {
  const say = useCopy();
  const feature = localizedFeature(original, useLocale());
  return (
    <Pressable role="link" aria-label={say(`${feature.title}, segera hadir`, `${feature.title}, coming soon`)} onPress={onPress} style={styles.row}>
      <View style={styles.text}>
        <HDText variant="bodyStrong">{feature.title}</HDText>
        <HDTag>{say("Segera hadir", "Coming soon")}</HDTag>
      </View>
      <HDIcon name="chevronRight" color={tokens.color.textSecondary} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: {
    minHeight: tokens.size.targetMinimum,
    flexDirection: 'row',
    alignItems: 'center',
    gap: tokens.space.stack,
    padding: tokens.space['12'],
    borderBottomWidth: tokens.size.borderControl,
    borderBottomColor: tokens.color.borderDecorative,
  },
  text: { flex: 1, gap: tokens.space['4'] },
});

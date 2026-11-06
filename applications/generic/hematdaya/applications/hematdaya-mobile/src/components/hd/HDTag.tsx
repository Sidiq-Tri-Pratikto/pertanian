import { StyleSheet, View } from 'react-native';

import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';

/** Compact status tag, such as Segera hadir. */
export function HDTag({ children }: { children: string }) {
  return (
    <View style={styles.tag}>
      <HDText variant="label">{children}</HDText>
    </View>
  );
}

const styles = StyleSheet.create({
  tag: {
    alignSelf: 'flex-start',
    paddingHorizontal: tokens.space['12'],
    paddingVertical: tokens.space['4'],
    borderRadius: tokens.radius.chip,
    backgroundColor: tokens.color.backgroundSubtle,
  },
});

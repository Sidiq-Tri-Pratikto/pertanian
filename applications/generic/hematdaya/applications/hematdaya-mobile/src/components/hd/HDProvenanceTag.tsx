import { useCopy } from '@/features/localization/messages';
import { StyleSheet, View } from 'react-native';

import { HDTag } from '@/components/hd/HDTag';
import { tokens } from '@/design/tokens.generated';

/**
 * Says where the numbers on a screen come from. Every screen with demo or imported data shows it, and a period
 * that mixes both shows both, so imported data is never presented as simulated or the other way round.
 */
export function HDProvenanceTag({ origins }: { origins: string[] }) {
  const say = useCopy();
  const tags = [
    ...(origins.includes('simulated') ? [say("Demo · Data simulasi", "Demo · Simulated data")] : []),
    ...(origins.includes('import') ? [say("Data historis · Impor CSV", "Historical data · CSV import")] : []),
  ];
  if (tags.length === 0) {
    return null;
  }
  return (
    <View style={styles.row}>
      {tags.map((tag) => (
        <HDTag key={tag}>{tag}</HDTag>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: tokens.space.inlineGap },
});

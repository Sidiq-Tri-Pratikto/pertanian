import { StyleSheet, View } from 'react-native';

import { HDTag } from '@/components/hd/HDTag';
import { tokens } from '@/design/tokens.generated';

/**
 * Says where the numbers on a screen come from. Every screen with demo or imported data shows it, and a period
 * that mixes both shows both, so imported data is never presented as simulated or the other way round.
 */
export function HDProvenanceTag({ origins }: { origins: string[] }) {
  const tags = [
    ...(origins.includes('simulated') ? ['Demo · Data simulasi'] : []),
    ...(origins.includes('import') ? ['Data historis · Impor CSV'] : []),
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

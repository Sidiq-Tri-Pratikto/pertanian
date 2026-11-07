import { StyleSheet, View } from 'react-native';

import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';

type Row = { term: string; value: string; detail?: string };

/** Separate rows for completeness, freshness and provenance. Never one score, never "akurat". */
export function HDDataQuality({ rows }: { rows: Row[] }) {
  return (
    <View role="list" aria-label="Kualitas data" style={styles.block}>
      {rows.map((row) => (
        <View key={row.term} role="listitem" style={styles.row}>
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

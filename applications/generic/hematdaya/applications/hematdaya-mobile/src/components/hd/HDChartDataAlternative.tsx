import { StyleSheet, View } from 'react-native';

import { HDDisclosure } from '@/components/hd/HDDisclosure';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';

type Column = { key: string; label: string };

type HDChartDataAlternativeProps = {
  summary: string;
  caption: string;
  columns: Column[];
  rows: Record<string, string>[];
  toggleLabel?: string;
};

/** Text summary and a table with the same values as the chart. On phones each row stacks with its labels. */
export function HDChartDataAlternative({ summary, caption, columns, rows, toggleLabel = 'Lihat data' }: HDChartDataAlternativeProps) {
  return (
    <View style={styles.block}>
      <HDText>{summary}</HDText>
      <HDDisclosure summary={toggleLabel}>
        <View role="table" aria-label={caption} style={styles.block}>
          <HDText variant="labelStrong">{caption}</HDText>
          {rows.map((row, index) => (
            <View key={index} role="row" style={styles.row}>
              {columns.map((column) => (
                <View key={column.key} role="cell" style={styles.cell}>
                  <HDText variant="label" tone="secondary">
                    {column.label}
                  </HDText>
                  <HDText>{row[column.key] || 'Tidak ada data'}</HDText>
                </View>
              ))}
            </View>
          ))}
        </View>
      </HDDisclosure>
    </View>
  );
}

const styles = StyleSheet.create({
  block: { gap: tokens.space.stackTight },
  row: {
    gap: tokens.space['4'],
    paddingVertical: tokens.space.stackTight,
    borderBottomWidth: tokens.size.borderControl,
    borderBottomColor: tokens.color.borderDecorative,
  },
  cell: { flexDirection: 'row', justifyContent: 'space-between', gap: tokens.space.inlineGap, flexWrap: 'wrap' },
});

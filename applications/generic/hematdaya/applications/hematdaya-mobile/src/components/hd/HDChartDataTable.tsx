import { StyleSheet, View } from 'react-native';

import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';

export type ChartDataTableProps = {
  caption: string;
  columns: { key: string; label: string }[];
  rows: Record<string, string>[];
};

/** Native rows pair each value with its column label at every width. */
export function HDChartDataTable({ caption, columns, rows }: ChartDataTableProps) {
  return (
    <View role="table" aria-label={caption} style={styles.block}>
      <HDText variant="labelStrong">{caption}</HDText>
      {rows.map((row, index) => (
        <View key={index} role="row" style={styles.row}>
          {columns.map((column) => (
            <View key={column.key} role="cell" style={styles.cell}>
              <HDText variant="label" tone="secondary">{column.label}</HDText>
              <HDText style={styles.value}>{row[column.key] || 'Tidak ada data'}</HDText>
            </View>
          ))}
        </View>
      ))}
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
  value: { flexShrink: 1 },
});

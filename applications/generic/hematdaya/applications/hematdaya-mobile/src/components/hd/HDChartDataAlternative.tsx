import { useCopy } from '@/features/localization/messages';
import { StyleSheet, View } from 'react-native';

import { HDChartDataTable, type ChartDataTableProps } from '@/components/hd/HDChartDataTable';
import { HDDisclosure } from '@/components/hd/HDDisclosure';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';

type HDChartDataAlternativeProps = ChartDataTableProps & {
  summary: string;
  toggleLabel?: string;
};

/** Text summary and an optional data disclosure with the same values as the chart. */
export function HDChartDataAlternative({ summary, caption, columns, rows, toggleLabel }: HDChartDataAlternativeProps) {
  const say = useCopy();
  return (
    <View style={styles.block}>
      <HDText>{summary}</HDText>
      <HDDisclosure summary={(toggleLabel ?? say("Lihat data", "View data"))}>
        <HDChartDataTable caption={caption} columns={columns} rows={rows} />
      </HDDisclosure>
    </View>
  );
}

const styles = StyleSheet.create({ block: { gap: tokens.space.stackTight } });

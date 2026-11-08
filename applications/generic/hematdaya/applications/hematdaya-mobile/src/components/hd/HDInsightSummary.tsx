import { useCopy } from '@/features/localization/messages';
import { StyleSheet, View } from 'react-native';

import { HDButton } from '@/components/hd/HDButton';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';

type HDInsightSummaryProps = {
  title: string;
  periodLabel: string;
  comparison: string;
  qualification: string;
  onOpenEvidence: () => void;
  openLabel?: string;
};

/** One observed fact with its period, comparison and qualification. No verdict, no fault, no saving. */
export function HDInsightSummary({ title, periodLabel, comparison, qualification, onOpenEvidence, openLabel }: HDInsightSummaryProps) {
  const say = useCopy();
  return (
    <View role="region" aria-label={title} style={styles.card}>
      <HDText variant="bodyStrong" role="heading">
        {title}
      </HDText>
      <HDText variant="label" tone="secondary">
        {periodLabel} · {comparison}
      </HDText>
      <HDText variant="label">{qualification}</HDText>
      <View style={styles.row}>
        <HDButton variant="text" icon="chevronRight" onPress={onOpenEvidence}>
          {(openLabel ?? say("Lihat dasar saran", "View evidence"))}
        </HDButton>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: tokens.space.stackTight,
    padding: tokens.space['16'],
    borderRadius: tokens.radius.surface,
    borderWidth: tokens.size.borderControl,
    borderColor: tokens.color.borderDecorative,
  },
  row: { flexDirection: 'row', flexWrap: 'wrap' },
});

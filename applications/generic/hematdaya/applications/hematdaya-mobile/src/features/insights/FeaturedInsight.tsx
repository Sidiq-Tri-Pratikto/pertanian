import { StyleSheet, View } from 'react-native';

import { HDInsightSummary } from '@/components/hd/HDInsightSummary';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { evidenceModel } from '@/features/insights/evidence-model';
import { useInsights } from '@/features/insights/useInsights';
import { useTabNavigation } from '@/features/navigation';

/** Beranda's last slot (UX-17): the largest eligible observation, one tap from its exact evidence revision. */
export function FeaturedInsight() {
  const insights = useInsights();
  const { openEvidence } = useTabNavigation();
  const featured = insights.data?.observations[0];

  if (insights.isError && !insights.data) {
    return (
      <HDText variant="label" tone="secondary">
        Saran belum dapat dimuat. Energi di atas tetap berlaku.
      </HDText>
    );
  }
  if (!featured) {
    return null;
  }
  const model = evidenceModel(featured);
  return (
    <View style={styles.section}>
      <HDText variant="section">Pengamatan</HDText>
      <HDInsightSummary
        title={model.title}
        periodLabel={model.periodLabel}
        comparison={model.comparisonLabel}
        qualification={model.qualification}
        onOpenEvidence={() => openEvidence(featured.id, featured.revision)}
      />
    </View>
  );
}

const styles = StyleSheet.create({ section: { gap: tokens.space.stack } });

import { useCopy } from '@/features/localization/messages';
import { StyleSheet, View } from 'react-native';

import { HDInsightSummary } from '@/components/hd/HDInsightSummary';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { evidenceModel } from '@/features/insights/evidence-model';
import { useInsights } from '@/features/insights/useInsights';
import { useTabNavigation } from '@/features/navigation';
import { RestoreNotice } from '@/features/insights/RestoreNotice';

/** Beranda's last slot (UX-17): the largest eligible observation, one tap from its exact evidence revision. */
export function FeaturedInsight() {
  const say = useCopy();
  const insights = useInsights();
  const { openEvidence } = useTabNavigation();
  const featured = insights.data?.observations[0];

  if (insights.isError && !insights.data) {
    return (
      <HDText variant="label" tone="secondary">{say("Saran belum dapat dimuat. Energi di atas tetap berlaku.", "Could not load insights. The energy figures above are still valid.")}</HDText>
    );
  }
  if (!featured) {
    return insights.data ? <RestoreNotice timezone={insights.data.window.timezone} /> : null;
  }
  const model = evidenceModel(featured);
  return (
    <View style={styles.section}>
      <HDText variant="section">{say("Pengamatan", "Observations")}</HDText>
      <RestoreNotice timezone={insights.data!.window.timezone} />
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

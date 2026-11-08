import { errorMessage } from '@/features/localization/error-copy';
import { useCopy } from '@/features/localization/messages';
import { useQuery } from '@tanstack/react-query';
import { StyleSheet, View } from 'react-native';

import { getHiddenInsights, type Insight } from '@/api/client';
import { HDButton } from '@/components/hd/HDButton';
import { HDInsightSummary } from '@/components/hd/HDInsightSummary';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { HDScreen } from '@/components/hd/HDScreen';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { evidenceModel } from '@/features/insights/evidence-model';
import { FeedbackStatus } from '@/features/insights/FeedbackStatus';
import { useFeedback } from '@/features/insights/useFeedback';
import { periodQuery, useNavigationContext } from '@/features/navigation-context/NavigationContextProvider';
import { useTabNavigation } from '@/features/navigation';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';
import { formatDateRange, formatDateTime } from '@/lib/format';

/** Saran tersembunyi: hidden and still-snoozed observations for the period, each with Pulihkan. */
export function HiddenScreen() {
  const say = useCopy();
  const { workspace, credential, credentialGeneration, scopeEpoch } = useWorkspace();
  const { period } = useNavigationContext();
  const { back } = useTabNavigation();
  const hidden = useQuery({
    queryKey: ['hidden-insights', workspace?.siteId, credentialGeneration, period, scopeEpoch],
    queryFn: () => getHiddenInsights(workspace!.siteId, periodQuery(period!), credential!),
    enabled: workspace !== null && period !== null,
  });

  return (
    <HDScreen title={say("Saran tersembunyi", "Hidden insights")} onBack={back}>
      {hidden.data === undefined ? (
        <HDProgressStatus
          state={hidden.isError ? 'failure' : 'loading'}
          label={hidden.isError ? say("Saran tersembunyi belum dapat dimuat", "Could not load hidden insights") : say("Memuat saran tersembunyi…", "Loading hidden insights…")}
          detail={errorMessage(hidden.error)}
          action={
            hidden.isError ? (
              <HDButton variant="text" icon="refresh" onPress={() => void hidden.refetch()}>{say("Coba lagi", "Try again")}</HDButton>
            ) : null
          }
        />
      ) : (
        <>
          <HDText variant="labelStrong">
            {formatDateRange(hidden.data.window.start_date, hidden.data.window.end_date)} · {hidden.data.window.timezone}
          </HDText>
          {hidden.data.observations.length === 0 ? (
            <HDText>{say("Tidak ada saran yang disembunyikan atau ditunda pada periode ini.", "No hidden or snoozed insights for this period.")}</HDText>
          ) : (
            <View role="list" aria-label={say("Saran tersembunyi", "Hidden insights")} style={styles.section}>
              {hidden.data.observations.map((insight) => (
                <View key={insight.id} role="listitem">
                  <HiddenItem insight={insight} timezone={hidden.data.window.timezone} />
                </View>
              ))}
            </View>
          )}
        </>
      )}
    </HDScreen>
  );
}

function HiddenItem({ insight, timezone }: { insight: Insight; timezone: string }) {
  const say = useCopy();
  const { openEvidence } = useTabNavigation();
  const restore = useFeedback(insight.id, insight.revision);
  const model = evidenceModel(insight);
  const until = insight.feedback?.visibility === 'snoozed' && insight.feedback.until ? insight.feedback.until : null;

  return (
    <View style={styles.section}>
      <HDInsightSummary
        title={model.title}
        periodLabel={model.periodLabel}
        comparison={until ? say(`Ditunda hingga ${formatDateTime(until, timezone)}`, `Snoozed until ${formatDateTime(until, timezone)}`) : say("Disembunyikan", "Hidden")}
        qualification={model.qualification}
        onOpenEvidence={() => openEvidence(insight.id, insight.revision)}
      />
      <View style={styles.row}>
        <HDButton loading={restore.state.kind === 'pending'} loadingLabel={say("Memulihkan…", "Restoring…")} onPress={() => void restore.give('restore')}>{say("Pulihkan", "Restore")}</HDButton>
      </View>
      <FeedbackStatus state={restore.state} timezone={timezone} onRetry={() => void restore.retry()} />
    </View>
  );
}

const styles = StyleSheet.create({
  section: { gap: tokens.space.stack },
  row: { flexDirection: 'row', flexWrap: 'wrap' },
});

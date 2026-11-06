import { StyleSheet, View } from 'react-native';

import type { FeedbackAction, Insight } from '@/api/client';
import { HDButton } from '@/components/hd/HDButton';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { ACTION_LABELS } from '@/features/insights/feedback-copy';
import { FeedbackStatus } from '@/features/insights/FeedbackStatus';
import { useFeedback } from '@/features/insights/useFeedback';
import { useNavigationContext } from '@/features/navigation-context/NavigationContextProvider';
import { useTabNavigation } from '@/features/navigation';
import { formatDateTime } from '@/lib/format';

const ACTIONS: FeedbackAction[] = ['useful', 'not_relevant', 'snooze', 'hide'];

/** Harmless feedback on this exact revision. Hiding returns to where the user came from, with Pulihkan there. */
export function FeedbackControls({ insight, timezone }: { insight: Insight; timezone: string }) {
  const { back } = useTabNavigation();
  const { setRecentlyHidden } = useNavigationContext();
  const feedback = useFeedback(insight.id, insight.revision, (result) => {
    if (result.action === 'hide') {
      setRecentlyHidden({ id: insight.id, revision: insight.revision, title: insight.text.title });
      back();
    }
  });
  const busy = feedback.state.kind === 'pending';
  const saved = insight.feedback;

  return (
    <View style={styles.block}>
      <HDText variant="section" role="heading">
        Umpan balik
      </HDText>
      <HDText variant="label" tone="secondary">
        Umpan balik tidak mengubah data, perangkat, atau angka energi.
      </HDText>
      {insight.earlier_feedback ? (
        <HDNotice tone="info" title="Bukti sudah diperbarui">
          Umpan balik Anda sebelumnya tetap tercatat pada versi bukti sebelumnya. Versi ini belum punya umpan balik.
        </HDNotice>
      ) : null}
      {saved?.rating ? (
        <HDText variant="label">{`Tanda Anda: ${ACTION_LABELS[saved.rating as FeedbackAction] ?? saved.rating}.`}</HDText>
      ) : null}
      {saved?.visibility === 'snoozed' && saved.until ? (
        <HDText variant="label">{`Ditunda hingga ${formatDateTime(saved.until, timezone)} menurut jam lokasi.`}</HDText>
      ) : null}
      {saved?.visibility === 'hidden' ? (
        <HDNotice
          tone="neutral"
          title="Saran ini disembunyikan"
          action={
            <HDButton variant="text" loading={busy} onPress={() => void feedback.give('restore')}>
              Pulihkan
            </HDButton>
          }
        />
      ) : null}
      <View style={styles.row}>
        {ACTIONS.map((action) => (
          <HDButton
            key={action}
            variant="secondary"
            loading={busy && feedback.state.kind === 'pending' && feedback.state.action === action}
            loadingLabel="Mengirim…"
            disabledReason={busy && feedback.state.kind === 'pending' && feedback.state.action !== action ? 'Menunggu umpan balik sebelumnya' : null}
            onPress={() => void feedback.give(action)}>
            {ACTION_LABELS[action]}
          </HDButton>
        ))}
      </View>
      <FeedbackStatus state={feedback.state} timezone={timezone} onRetry={() => void feedback.retry()} />
    </View>
  );
}

const styles = StyleSheet.create({
  block: { gap: tokens.space.stack },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: tokens.space.inlineGap },
});

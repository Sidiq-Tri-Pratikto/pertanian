import { useCopy } from '@/features/localization/messages';
import { StyleSheet, View } from 'react-native';

import type { FeedbackAction, Insight } from '@/api/client';
import { HDButton } from '@/components/hd/HDButton';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { actionLabel } from '@/features/insights/feedback-copy';
import { FeedbackStatus } from '@/features/insights/FeedbackStatus';
import { useFeedback } from '@/features/insights/useFeedback';
import { useNavigationContext } from '@/features/navigation-context/NavigationContextProvider';
import { useTabNavigation } from '@/features/navigation';
import { formatDateTime } from '@/lib/format';

const ACTIONS: FeedbackAction[] = ['useful', 'not_relevant', 'snooze', 'hide'];

/** Harmless feedback on this exact revision. Hiding returns to where the user came from, with Pulihkan there. */
export function FeedbackControls({ insight, timezone }: { insight: Insight; timezone: string }) {
  const say = useCopy();
  const { back } = useTabNavigation();
  const { setRecentlyHidden } = useNavigationContext();
  const feedback = useFeedback(insight.id, insight.revision, (result) => {
    if (result.action === 'hide') {
      setRecentlyHidden({ id: insight.id, revision: insight.revision, title: insight.text.title, titles: insight.text_by_locale ? { id: insight.text_by_locale.id.title, en: insight.text_by_locale.en.title } : undefined });
      back();
    }
  });
  const busy = feedback.state.kind === 'pending';
  const saved = insight.feedback;

  return (
    <View style={styles.block}>
      <HDText variant="section" role="heading">{say("Umpan balik", "Feedback")}</HDText>
      <HDText variant="label" tone="secondary">{say("Umpan balik tidak mengubah data, perangkat, atau angka energi.", "Feedback leaves your devices and energy readings as they are.")}</HDText>
      {insight.earlier_feedback ? (
        <HDNotice tone="info" title={say("Bukti sudah diperbarui", "Evidence updated")}>{say("Umpan balik Anda sebelumnya tetap tercatat pada versi bukti sebelumnya. Versi ini belum punya umpan balik.", "Your earlier feedback is saved with the previous evidence version. You can rate this version separately.")}</HDNotice>
      ) : null}
      {saved?.rating ? (
        <HDText variant="label">{say(`Tanda Anda: ${actionLabel(saved.rating as FeedbackAction) ?? saved.rating}.`, `Your rating: ${actionLabel(saved.rating as FeedbackAction) ?? saved.rating}.`)}</HDText>
      ) : null}
      {saved?.visibility === 'snoozed' && saved.until ? (
        <HDText variant="label">{say(`Ditunda hingga ${formatDateTime(saved.until, timezone)} menurut jam lokasi.`, `Snoozed until ${formatDateTime(saved.until, timezone)} in the site’s time zone.`)}</HDText>
      ) : null}
      {saved?.visibility === 'hidden' ? (
        <HDNotice
          tone="neutral"
          title={say("Saran ini disembunyikan", "This insight is hidden")}
          action={
            <HDButton variant="text" loading={busy} onPress={() => void feedback.give('restore')}>{say("Pulihkan", "Restore")}</HDButton>
          }
        />
      ) : null}
      <View style={styles.row}>
        {ACTIONS.map((action) => (
          <HDButton
            key={action}
            variant="secondary"
            loading={busy && feedback.state.kind === 'pending' && feedback.state.action === action}
            loadingLabel={say("Mengirim…", "Sending…")}
            disabledReason={busy && feedback.state.kind === 'pending' && feedback.state.action !== action ? say("Menunggu umpan balik sebelumnya", "Waiting for earlier feedback") : null}
            onPress={() => void feedback.give(action)}>
            {actionLabel(action)}
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

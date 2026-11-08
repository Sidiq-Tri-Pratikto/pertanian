import { useLocale } from '@/features/localization/locale';
import { useCopy } from '@/features/localization/messages';
import { HDButton } from '@/components/hd/HDButton';
import { HDNotice } from '@/components/hd/HDNotice';
import { FeedbackStatus } from '@/features/insights/FeedbackStatus';
import { useFeedback } from '@/features/insights/useFeedback';
import { useNavigationContext, type HiddenItem } from '@/features/navigation-context/NavigationContextProvider';

/** Shown where the user returns after hiding an observation, with an immediate way back. */
export function RestoreNotice({ timezone }: { timezone: string }) {
  const { recentlyHidden } = useNavigationContext();
  return recentlyHidden ? <Restore key={recentlyHidden.id} item={recentlyHidden} timezone={timezone} /> : null;
}

function Restore({ item, timezone }: { item: HiddenItem; timezone: string }) {
  const say = useCopy();
  const locale = useLocale();
  const title = item.titles?.[locale] ?? item.title;
  const restore = useFeedback(item.id, item.revision);
  return (
    <>
      <HDNotice
        tone="success"
        live
        title={say("Saran disembunyikan", "Insight hidden")}
        action={
          <HDButton variant="text" loading={restore.state.kind === 'pending'} loadingLabel={say("Memulihkan…", "Restoring…")} onPress={() => void restore.give('restore')}>{say("Pulihkan", "Restore")}</HDButton>
        }>
        {say(`${title} tidak lagi tampil di daftar. Data dan perangkat tidak berubah.`, `${title} is hidden from the list. Your data and devices are unchanged.`)}
      </HDNotice>
      <FeedbackStatus state={restore.state} timezone={timezone} onRetry={() => void restore.retry()} />
    </>
  );
}
